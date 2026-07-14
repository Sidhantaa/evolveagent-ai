from __future__ import annotations

import json
import re
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from app.config import settings
from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Kaggle's kernel API is async/batch, not a low-latency job queue: a push
# queues a kernel run on Kaggle's own infrastructure (free-tier GPU quota is
# time-limited per week), which the caller must separately poll. This adapter
# models that reality -- submit_job() only enqueues; poll_job()/get_job_output()
# check on it later. It is a real background GPU worker, not an interactive one.
KAGGLE_CLI = "kaggle"
_ALLOWED_SUBCOMMANDS = {
    "push": ("kernels", "push"),
    "status": ("kernels", "status"),
    "output": ("kernels", "output"),
    "config_view": ("config", "view"),
}
_USERNAME_RE = re.compile(r"username:\s*(\S+)")


class KaggleWorkerError(Exception):
    pass


def _default_kaggle_runner(argv: list[str], cwd: Path | None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False, timeout=timeout)


class KaggleWorkerService:
    """v220 Compute Fabric -- real (opt-in) Kaggle GPU worker adapter.

    Submits a job as a real Kaggle kernel push via the allowlisted `kaggle`
    CLI (argv-only, no shell=True), backed by the user's own already-configured
    Kaggle credentials (never read, stored, or logged by this service -- the
    `kaggle` CLI resolves them itself from ~/.kaggle/kaggle.json). Off by
    default via KAGGLE_WORKER_ENABLED; submitting a job is the only write
    action and must go through the same approval-gated whitelisted-action
    path as every other real external write in this app (see
    DurableWorkflowService's run_kaggle_job action). Never auto-applies,
    auto-promotes, or retries -- a human decides whether to submit, and later
    to poll/pull the result.
    """

    jobs_file = "kaggle_worker_jobs.json"

    def __init__(
        self,
        storage: StorageService,
        governance_service: GovernanceService,
        worker_registry=None,
        agent_scheduler=None,
        kaggle_runner: Callable[[list[str], Path | None, int], subprocess.CompletedProcess[str]] | None = None,
    ):
        self.storage = storage
        self.governance = governance_service
        # v220: optional WorkerRegistryService collaborator -- this adapter's
        # worker is registered there so its real status is visible alongside
        # any future non-Kaggle worker adapter, in one place.
        self.worker_registry = worker_registry
        # v220: optional AgentSchedulerService collaborator -- a submitted job
        # becomes a real, observable job in the already-real job queue, same
        # pattern DurableWorkflowService already uses for its own runs.
        self.agent_scheduler = agent_scheduler
        self._run = kaggle_runner or _default_kaggle_runner
        self._username_cache: str | None = None

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str, blocked: bool = False) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="compute_fabric",
                agent_name="Kaggle Worker Adapter",
                action_type=action_type,
                tool_used="KaggleWorkerService",
                permission_level="approve_to_run",
                approved=not blocked,
                blocked=blocked,
                risk_score=15 if blocked else 30,
                reason=reason,
            )
        )

    @staticmethod
    def _sanitize_slug(title: str) -> str:
        slug = re.sub(r"[^a-z0-9-]+", "-", (title or "job").strip().lower()).strip("-")[:40] or "job"
        return f"{slug}-{uuid4().hex[:8]}"

    def _resolve_username(self) -> str:
        # Never reads ~/.kaggle/kaggle.json directly -- resolves the
        # already-authenticated account via the CLI's own read-only config
        # command instead, so this service never touches credentials.
        if self._username_cache is not None:
            return self._username_cache
        result = self._run([KAGGLE_CLI, *_ALLOWED_SUBCOMMANDS["config_view"]], None, 30)
        match = _USERNAME_RE.search(result.stdout or "")
        self._username_cache = match.group(1) if match else ""
        return self._username_cache

    def _kernel_ref(self, kernel_slug: str) -> str:
        username = self._resolve_username()
        return f"{username}/{kernel_slug}" if username else kernel_slug

    def submit_job(self, code: str, title: str = "", workspace_id: str | None = None) -> dict:
        if not settings.kaggle_worker_enabled:
            raise KaggleWorkerError("Kaggle worker is disabled. Set KAGGLE_WORKER_ENABLED=true to enable.")
        if not (code or "").strip():
            raise KaggleWorkerError("code is required to submit a Kaggle job.")

        kernel_slug = self._sanitize_slug(title)
        tmp_dir = Path(tempfile.mkdtemp(prefix="kaggle-job-"))
        (tmp_dir / "script.py").write_text(code, encoding="utf-8")
        metadata = {
            "id": self._kernel_ref(kernel_slug),
            # Kaggle derives the ACTUAL kernel slug from `title`, not `id`, if
            # they diverge (confirmed live: a human-readable title caused the
            # kernel to land at a different ref than `id` specified, silently).
            # Using kernel_slug itself as the title guarantees they always
            # resolve to the same kernel -- the human-readable title is kept
            # separately in this job's own record (job["title"]), never sent
            # to Kaggle's metadata.
            "title": kernel_slug,
            "code_file": "script.py",
            "language": "python",
            "kernel_type": "script",
            "is_private": bool(settings.kaggle_worker_private),
            "enable_gpu": True,
            "enable_internet": False,
        }
        (tmp_dir / "kernel-metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        argv = [KAGGLE_CLI, *_ALLOWED_SUBCOMMANDS["push"], "-p", str(tmp_dir)]
        result = self._run(argv, tmp_dir, 120)
        submitted = result.returncode == 0

        job = {
            "job_id": str(uuid4()),
            "kernel_slug": kernel_slug,
            "kernel_ref": metadata["id"],
            "title": title.strip()[:60] or kernel_slug,
            "workspace_id": workspace_id,
            "status": "submitted" if submitted else "submit_failed",
            "submitted": submitted,
            "stdout_tail": (result.stdout or "")[-1000:],
            "stderr_tail": (result.stderr or "")[-1000:],
            "worker_id": None,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        if self.worker_registry is not None and submitted:
            try:
                worker = self.worker_registry.register_worker(
                    "kaggle_gpu", capabilities=["gpu", "python"], metadata={"kernel_ref": metadata["id"]},
                )
                job["worker_id"] = worker["worker_id"]
            except Exception:
                pass
        if self.agent_scheduler is not None and submitted:
            try:
                sched_job = self.agent_scheduler.create_job({
                    "job_type": "kaggle_gpu_job", "title": job["title"], "workspace_id": workspace_id,
                })
                job["agent_scheduler_job_id"] = sched_job.get("job_id")
            except Exception:
                pass

        self.storage.append(self.jobs_file, job)
        self._log(
            "kaggle_job_submitted" if submitted else "kaggle_job_submit_failed",
            f"Kaggle kernel push for '{kernel_slug}': {'submitted' if submitted else 'failed'}.",
            blocked=not submitted,
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

        # The real `kaggle kernels status` CLI call happens here, OUTSIDE any
        # storage lock -- it can take up to 60s, and holding the (process-wide,
        # single) storage lock for that long would serialize every unrelated
        # read/write in the whole app for the duration of one Kaggle poll.
        argv = [KAGGLE_CLI, *_ALLOWED_SUBCOMMANDS["status"], job["kernel_ref"]]
        result = self._run(argv, None, 60)
        output = (result.stdout or "").lower()
        if "complete" in output:
            new_status = "complete"
        elif "error" in output or "cancelacknowledged" in output:
            new_status = "error"
        elif "running" in output:
            new_status = "running"
        elif "queued" in output:
            new_status = "queued"
        else:
            new_status = job.get("status")
        last_poll_output = (result.stdout or "")[-500:]
        updated_at = self._now()

        def _apply(jobs: list[dict]) -> dict | None:
            current = next((j for j in jobs if j.get("job_id") == job_id), None)
            if current is None:
                return None
            current["status"] = new_status
            current["last_poll_output"] = last_poll_output
            current["updated_at"] = updated_at
            return dict(current)

        # Previously: read_list() then write_list() as two separate lock
        # acquisitions, with the slow CLI call sitting in between them -- a
        # concurrent submit_job()'s append() landing in that window would be
        # silently overwritten by this call's stale snapshot on write-back
        # (a real, reachable lost-update: two concurrent HTTP requests run in
        # separate threads even under one worker, since FastAPI's sync `def`
        # handlers run in a threadpool). update_list() re-reads fresh state
        # and does the find-mutate-write as one atomic sequence.
        updated = self.storage.update_list(self.jobs_file, _apply)
        if updated is None:
            raise ValueError("Job not found")
        job = updated

        if self.agent_scheduler is not None and job.get("agent_scheduler_job_id"):
            try:
                if job["status"] == "complete":
                    self.agent_scheduler.complete(job["agent_scheduler_job_id"], result_summary="Kaggle kernel complete.")
                elif job["status"] == "error":
                    self.agent_scheduler.fail(job["agent_scheduler_job_id"], error="Kaggle kernel run failed.")
                else:
                    self.agent_scheduler.heartbeat(job["agent_scheduler_job_id"])
            except Exception:
                pass

        # The worker_registry entry created at submit time (register_worker())
        # was never closed on the other end -- every job leaked a permanent
        # "online" phantom GPU worker regardless of how it actually finished.
        # Mirror the same terminal-status handling used for agent_scheduler
        # above, via the worker_id already stored on this job.
        if self.worker_registry is not None and job.get("worker_id") and job["status"] in ("complete", "error"):
            try:
                self.worker_registry.deregister_worker(job["worker_id"])
            except Exception:
                pass
        return job

    def get_job_output(self, job_id: str) -> dict:
        job = self.get_job(job_id)
        if job is None:
            raise ValueError("Job not found")
        tmp_dir = Path(tempfile.mkdtemp(prefix="kaggle-output-"))
        argv = [KAGGLE_CLI, *_ALLOWED_SUBCOMMANDS["output"], job["kernel_ref"], "-p", str(tmp_dir)]
        result = self._run(argv, tmp_dir, 120)
        files = [str(p.name) for p in tmp_dir.glob("*")] if result.returncode == 0 else []
        return {"job_id": job_id, "downloaded": result.returncode == 0, "files": files, "output_dir": str(tmp_dir) if files else None}

    def status(self) -> dict:
        """Real, honest opt-in status -- consumed by CapabilityDirectoryService
        (previously this real capability had no entry there at all, since
        nothing exposed a status() to classify it by)."""
        jobs = self.storage.read_list(self.jobs_file)
        return {
            "enabled": settings.kaggle_worker_enabled,
            "total_jobs": len(jobs),
        }

    def analytics_summary(self) -> dict:
        jobs = self.storage.read_list(self.jobs_file)
        return {
            "kaggle_jobs_total": len(jobs),
            "kaggle_jobs_submitted": sum(1 for j in jobs if j.get("submitted")),
            "kaggle_jobs_complete": sum(1 for j in jobs if j.get("status") == "complete"),
        }
