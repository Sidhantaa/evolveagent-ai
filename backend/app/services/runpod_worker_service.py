from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import httpx

from app.config import settings
from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


# endpoint_id is interpolated directly into a URL path (f"/v2/{endpoint_id}/run"),
# and was previously only length-capped -- no character validation. The fixed
# api_base_url prevents a genuine host-takeover (concatenation onto an
# already-complete scheme://host, so nothing in endpoint_id can introduce a
# new authority), but an ID this permissive is still inconsistent with every
# comparable case elsewhere in this codebase (KaggleWorkerService._sanitize_slug,
# CodeWriterService._safe_branch_name both apply a character allow-list to
# similar caller-suppliable values that get interpolated into a constructed
# string). Reject rather than silently strip, since an endpoint_id must match
# a real RunPod resource exactly -- silently mangling it could produce a
# different, still-syntactically-valid-but-wrong ID instead of a clear error.
_ENDPOINT_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,160}$")

TERMINAL_STATUSES = {"complete", "error"}
RUNPOD_STATUS_MAP = {
    "COMPLETED": "complete",
    "FAILED": "error",
    "CANCELLED": "error",
    "CANCELED": "error",
    "TIMED_OUT": "error",
    "TIMEOUT": "error",
    "IN_PROGRESS": "running",
    "RUNNING": "running",
    "IN_QUEUE": "queued",
    "QUEUED": "queued",
}


class RunPodWorkerError(Exception):
    pass


class RunPodWorkerService:
    """Real, opt-in RunPod Serverless GPU worker adapter.

    The adapter mirrors KaggleWorkerService's lifecycle: submit an async job,
    poll it later, then fetch the stored output. It never exposes the raw API
    key; the key is read from settings only when creating the Authorization
    header and is never returned, logged, or persisted.
    """

    jobs_file = "runpod_worker_jobs.json"

    def __init__(
        self,
        storage: StorageService,
        governance_service: GovernanceService,
        worker_registry=None,
        agent_scheduler=None,
        http_client: Any | None = None,
    ):
        self.storage = storage
        self.governance = governance_service
        self.worker_registry = worker_registry
        self.agent_scheduler = agent_scheduler
        self.http_client = http_client

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str, blocked: bool = False) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="compute_fabric",
                agent_name="RunPod Worker Adapter",
                action_type=action_type,
                tool_used="RunPodWorkerService",
                permission_level="approve_to_run",
                approved=not blocked,
                blocked=blocked,
                risk_score=20 if blocked else 35,
                reason=reason,
            )
        )

    def _configured(self) -> bool:
        return bool(settings.runpod_api_key)

    def _endpoint_id(self, endpoint_id: str | None = None) -> str:
        resolved = (endpoint_id or settings.runpod_default_endpoint_id or "").strip()[:160]
        if not resolved:
            raise RunPodWorkerError("RunPod endpoint_id is required. Set RUNPOD_DEFAULT_ENDPOINT_ID or pass endpoint_id.")
        if not _ENDPOINT_ID_RE.match(resolved):
            raise RunPodWorkerError("RunPod endpoint_id contains invalid characters (expected letters, digits, underscore, or hyphen only).")
        return resolved

    def _headers(self) -> dict[str, str]:
        api_key = settings.runpod_api_key
        if not api_key:
            raise RunPodWorkerError("RunPod API key is not configured. Set RUNPOD_API_KEY to enable.")
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def _url(self, path: str) -> str:
        base = settings.runpod_api_base_url.rstrip("/")
        return f"{base}{path}"

    @staticmethod
    def _safe_http_error(exc: Exception) -> str:
        if isinstance(exc, httpx.HTTPStatusError):
            return f"RunPod request failed (HTTP {exc.response.status_code})."
        if isinstance(exc, httpx.HTTPError):
            return f"RunPod request failed ({type(exc).__name__})."
        return f"RunPod request failed ({type(exc).__name__})."

    def _post_json(self, path: str, payload: dict) -> dict:
        try:
            if self.http_client is not None:
                response = self.http_client.post(self._url(path), headers=self._headers(), json=payload, timeout=60)
            else:
                response = httpx.post(self._url(path), headers=self._headers(), json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else {"result": data}
        except Exception as exc:
            raise RunPodWorkerError(self._safe_http_error(exc)) from exc

    def _get_json(self, path: str) -> dict:
        try:
            if self.http_client is not None:
                response = self.http_client.get(self._url(path), headers=self._headers(), timeout=60)
            else:
                response = httpx.get(self._url(path), headers=self._headers(), timeout=60)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else {"result": data}
        except Exception as exc:
            raise RunPodWorkerError(self._safe_http_error(exc)) from exc

    @staticmethod
    def _map_status(raw_status: Any, fallback: str = "submitted") -> str:
        if raw_status is None:
            return fallback
        return RUNPOD_STATUS_MAP.get(str(raw_status).strip().upper(), fallback)

    @staticmethod
    def _input_summary(input_payload: dict) -> dict:
        return {
            "keys": [str(key)[:80] for key in list(input_payload.keys())[:20]],
            "field_count": len(input_payload),
        }

    def submit_job(
        self,
        input_payload: dict,
        endpoint_id: str | None = None,
        title: str = "",
        workspace_id: str | None = None,
    ) -> dict:
        if not settings.runpod_worker_enabled:
            raise RunPodWorkerError("RunPod worker is disabled. Set RUNPOD_WORKER_ENABLED=true to enable.")
        if not isinstance(input_payload, dict) or not input_payload:
            raise RunPodWorkerError("input payload is required to submit a RunPod job.")
        resolved_endpoint = self._endpoint_id(endpoint_id)

        created_at = self._now()
        job = {
            "job_id": str(uuid4()),
            "runpod_job_id": None,
            "endpoint_id": resolved_endpoint,
            "title": title.strip()[:80] or "RunPod GPU job",
            "workspace_id": workspace_id,
            "status": "submit_failed",
            "provider_status": None,
            "submitted": False,
            "input_summary": self._input_summary(input_payload),
            "output": None,
            "error": None,
            "worker_id": None,
            "agent_scheduler_job_id": None,
            "created_at": created_at,
            "updated_at": created_at,
        }
        try:
            payload = {"input": input_payload}
            response = self._post_json(f"/v2/{resolved_endpoint}/run", payload)
            runpod_job_id = response.get("id") or response.get("job_id")
            if not runpod_job_id:
                raise RunPodWorkerError("RunPod response did not include a job id.")
            job["runpod_job_id"] = str(runpod_job_id)
            job["provider_status"] = response.get("status")
            job["status"] = self._map_status(response.get("status"), fallback="submitted")
            job["submitted"] = True
        except Exception as exc:
            job["error"] = str(exc)

        if self.worker_registry is not None and job["submitted"]:
            try:
                worker = self.worker_registry.register_worker(
                    "runpod_gpu",
                    capabilities=["gpu", "serverless", "python"],
                    metadata={
                        "provider": "runpod",
                        "endpoint_id": resolved_endpoint,
                        "runpod_job_id": job["runpod_job_id"],
                        "runtime": "serverless",
                        "supports_jobs": True,
                        "supports_model_serving": True,
                        "quota_state": "account_controlled",
                        "requires_approval": True,
                        "last_provider_check": self._now(),
                    },
                )
                job["worker_id"] = worker["worker_id"]
            except Exception:
                pass
        if self.agent_scheduler is not None and job["submitted"]:
            try:
                sched_job = self.agent_scheduler.create_job({
                    "job_type": "runpod_gpu_job",
                    "title": job["title"],
                    "workspace_id": workspace_id,
                })
                job["agent_scheduler_job_id"] = sched_job.get("job_id")
            except Exception:
                pass

        self.storage.append(self.jobs_file, job)
        self._log(
            "runpod_job_submitted" if job["submitted"] else "runpod_job_submit_failed",
            f"RunPod job for endpoint '{resolved_endpoint}': {'submitted' if job['submitted'] else 'failed'}.",
            blocked=not job["submitted"],
        )
        return job

    def get_job(self, job_id: str) -> dict | None:
        return next((j for j in self.storage.read_list(self.jobs_file) if j.get("job_id") == job_id), None)

    def list_jobs(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.jobs_file)[-limit:]))

    def poll_job(self, job_id: str) -> dict:
        job = self.get_job(job_id)
        if job is None:
            raise ValueError("Job not found")
        if not job.get("submitted"):
            return job
        endpoint_id = job.get("endpoint_id")
        runpod_job_id = job.get("runpod_job_id")
        if not endpoint_id or not runpod_job_id:
            return job

        data = self._get_json(f"/v2/{endpoint_id}/status/{runpod_job_id}")
        provider_status = data.get("status")
        new_status = self._map_status(provider_status, fallback=job.get("status", "submitted"))
        output = data.get("output") if "output" in data else job.get("output")
        error = data.get("error") or data.get("message") if new_status == "error" else job.get("error")
        updated_at = self._now()

        def _apply(jobs: list[dict]) -> dict | None:
            current = next((j for j in jobs if j.get("job_id") == job_id), None)
            if current is None:
                return None
            current["status"] = new_status
            current["provider_status"] = provider_status
            current["output"] = output
            current["error"] = error
            current["last_poll_response"] = {
                "status": provider_status,
                "has_output": output is not None,
                "has_error": bool(error),
            }
            current["updated_at"] = updated_at
            return dict(current)

        updated = self.storage.update_list(self.jobs_file, _apply)
        if updated is None:
            raise ValueError("Job not found")
        job = updated

        if self.agent_scheduler is not None and job.get("agent_scheduler_job_id"):
            try:
                if job["status"] == "complete":
                    self.agent_scheduler.complete(job["agent_scheduler_job_id"], result_summary="RunPod job complete.")
                elif job["status"] == "error":
                    self.agent_scheduler.fail(job["agent_scheduler_job_id"], error="RunPod job failed.")
                else:
                    self.agent_scheduler.heartbeat(job["agent_scheduler_job_id"])
            except Exception:
                pass
        if self.worker_registry is not None and job.get("worker_id") and job["status"] in TERMINAL_STATUSES:
            try:
                self.worker_registry.deregister_worker(job["worker_id"])
            except Exception:
                pass
        return job

    def get_job_output(self, job_id: str) -> dict:
        job = self.get_job(job_id)
        if job is None:
            raise ValueError("Job not found")
        if job.get("output") is not None:
            return {"job_id": job_id, "available": True, "output": job["output"], "source": "stored_status"}
        if job.get("submitted") and job.get("status") not in TERMINAL_STATUSES:
            job = self.poll_job(job_id)
            if job.get("output") is not None:
                return {"job_id": job_id, "available": True, "output": job["output"], "source": "status_poll"}
        return {"job_id": job_id, "available": False, "output": None, "source": "not_ready"}

    def status(self) -> dict:
        jobs = self.storage.read_list(self.jobs_file)
        return {
            "enabled": bool(settings.runpod_worker_enabled),
            "configured": self._configured(),
            "default_endpoint_set": bool(settings.runpod_default_endpoint_id),
            "api_base_url": settings.runpod_api_base_url,
            "total_jobs": len(jobs),
        }

    def analytics_summary(self) -> dict:
        jobs = self.storage.read_list(self.jobs_file)
        return {
            "runpod_jobs_total": len(jobs),
            "runpod_jobs_submitted": sum(1 for j in jobs if j.get("submitted")),
            "runpod_jobs_complete": sum(1 for j in jobs if j.get("status") == "complete"),
        }
