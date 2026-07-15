from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.worker_registry_service import WorkerRegistryService


FUTURE_CLOUD_PROVIDERS = [
    {
        "provider": "lambda_labs",
        "name": "Lambda Labs",
        "enabled_env": "LAMBDA_LABS_WORKER_ENABLED",
        "execution_env": "LAMBDA_LABS_EXECUTION_ENABLED",
        "required_env_vars": ["LAMBDA_LABS_API_KEY"],
        "cost_warning": "Lambda Labs can create real paid GPU instances. v240 exposes readiness/dry-run only.",
    },
    {
        "provider": "modal",
        "name": "Modal",
        "enabled_env": "MODAL_WORKER_ENABLED",
        "execution_env": "MODAL_EXECUTION_ENABLED",
        "required_env_vars": ["MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"],
        "cost_warning": "Modal can run paid cloud jobs. v240 exposes readiness/dry-run only.",
    },
    {
        "provider": "replicate",
        "name": "Replicate",
        "enabled_env": "REPLICATE_WORKER_ENABLED",
        "execution_env": "REPLICATE_EXECUTION_ENABLED",
        "required_env_vars": ["REPLICATE_API_TOKEN"],
        "cost_warning": "Replicate can run paid model jobs. v240 exposes readiness/dry-run only.",
    },
]

PROVIDER_ORDER = ["local", "kaggle", "runpod", "lambda_labs", "modal", "replicate"]


class GPUWorkerService:
    """v240 GPU worker expansion coordinator.

    This service does not run jobs. It normalizes worker/provider readiness over
    the existing WorkerRegistryService and KaggleWorkerService, then produces
    approval-aware dry-run plans. Future paid cloud providers are readiness-only
    here; real execution remains disabled unless an adapter exists, explicit env
    flags are set, and a human approval flow calls that adapter.
    """

    def __init__(
        self,
        worker_registry: WorkerRegistryService,
        kaggle_worker,
        governance_service: GovernanceService,
        runpod_worker=None,
    ):
        self.worker_registry = worker_registry
        self.kaggle_worker = kaggle_worker
        self.runpod_worker = runpod_worker
        self.governance = governance_service

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _env_enabled(name: str) -> bool:
        import os
        return str(os.environ.get(name, "")).strip().lower() in ("1", "true", "yes", "on")

    @staticmethod
    def _env_configured(names: list[str]) -> bool:
        import os
        return all(bool(os.environ.get(name, "").strip()) for name in names)

    def _log(self, action_type: str, reason: str, blocked: bool = False) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="compute_fabric",
                agent_name="GPU Worker Coordinator",
                action_type=action_type,
                tool_used="GPUWorkerService",
                permission_level="approve_to_run" if action_type.endswith("_dry_run") else "read_only",
                approved=not blocked,
                blocked=blocked,
                risk_score=20 if blocked else 5,
                reason=reason,
            )
        )

    @staticmethod
    def _count(workers: list[dict], provider: str) -> int:
        return sum(1 for worker in workers if worker.get("provider") == provider)

    @staticmethod
    def _active_count(workers: list[dict], provider: str) -> int:
        return sum(1 for worker in workers if worker.get("provider") == provider and worker.get("status") in ("online", "busy"))

    def _normalize_worker(self, worker: dict) -> dict:
        provider = str(worker.get("provider") or worker.get("metadata", {}).get("provider") or "other")
        return {
            "worker_id": worker.get("worker_id"),
            "worker_type": worker.get("worker_type"),
            "provider": provider,
            "status": worker.get("status", "unknown"),
            "capabilities": worker.get("capabilities", []),
            "gpu_model": worker.get("gpu_model") or worker.get("metadata", {}).get("gpu_model"),
            "gpu_memory_gb": worker.get("gpu_memory_gb") or worker.get("metadata", {}).get("gpu_memory_gb"),
            "region": worker.get("region") or worker.get("metadata", {}).get("region"),
            "runtime": worker.get("runtime") or worker.get("metadata", {}).get("runtime") or "unknown",
            "supports_jobs": bool(worker.get("supports_jobs", False)),
            "supports_model_serving": bool(worker.get("supports_model_serving", False)),
            "estimated_cost_per_hour": worker.get("estimated_cost_per_hour"),
            "quota_state": worker.get("quota_state") or "unknown",
            "requires_approval": bool(worker.get("requires_approval", True)),
            "last_provider_check": worker.get("last_provider_check"),
            "last_heartbeat": worker.get("last_heartbeat"),
            "registered_at": worker.get("registered_at"),
        }

    def _local_provider(self, workers: list[dict]) -> dict:
        active = self._active_count(workers, "local")
        total = self._count(workers, "local")
        return {
            "provider": "local",
            "name": "Local GPU Workers",
            "enabled": True,
            "configured": total > 0,
            "execution_enabled": False,
            "supports_gpu_jobs": active > 0,
            "supports_cancellation": False,
            "risk_level": "medium" if active else "low",
            "worker_count": total,
            "active_workers": active,
            "required_env_vars": [],
            "cost_warning": "Manual/local GPU workers are status-only in v240; no local job executor is started.",
            "note": "Register local workers manually. Automatic hardware probing is intentionally deferred.",
        }

    def _kaggle_provider(self, workers: list[dict]) -> dict:
        status = self.kaggle_worker.status() if self.kaggle_worker is not None else {"enabled": False, "total_jobs": 0}
        enabled = bool(status.get("enabled"))
        return {
            "provider": "kaggle",
            "name": "Kaggle GPU Worker",
            "enabled": enabled,
            "configured": enabled,
            "execution_enabled": enabled,
            "supports_gpu_jobs": True,
            "supports_cancellation": False,
            "risk_level": "high" if enabled else "medium",
            "worker_count": self._count(workers, "kaggle"),
            "active_workers": self._active_count(workers, "kaggle"),
            "total_jobs": status.get("total_jobs", 0),
            "required_env_vars": ["KAGGLE_WORKER_ENABLED", "KAGGLE_CONFIG_DIR or ~/.kaggle/kaggle.json"],
            "cost_warning": "Kaggle uses account GPU quota. Submissions still require explicit approval through the existing workflow.",
            "note": "Kaggle is the only real v240-capable adapter; it remains opt-in and approval-gated.",
        }

    def _runpod_provider(self, workers: list[dict]) -> dict:
        status = self.runpod_worker.status() if self.runpod_worker is not None else {
            "enabled": False, "configured": False, "default_endpoint_set": False, "total_jobs": 0,
        }
        enabled = bool(status.get("enabled"))
        configured = bool(status.get("configured"))
        endpoint_set = bool(status.get("default_endpoint_set"))
        execution_enabled = enabled and configured and endpoint_set
        missing = []
        if not configured:
            missing.append("RUNPOD_API_KEY")
        if not endpoint_set:
            missing.append("RUNPOD_DEFAULT_ENDPOINT_ID or endpoint_id in approved workflow params")
        return {
            "provider": "runpod",
            "name": "RunPod GPU Worker",
            "enabled": enabled,
            "configured": configured,
            "execution_enabled": execution_enabled,
            "supports_gpu_jobs": execution_enabled,
            "supports_cancellation": False,
            "risk_level": "high",
            "worker_count": self._count(workers, "runpod"),
            "active_workers": self._active_count(workers, "runpod"),
            "total_jobs": status.get("total_jobs", 0),
            "required_env_vars": ["RUNPOD_WORKER_ENABLED", "RUNPOD_API_KEY", "RUNPOD_DEFAULT_ENDPOINT_ID"],
            "missing_configuration": missing,
            "cost_warning": "RunPod can consume paid cloud GPU resources. Submission is approval-gated through DurableWorkflowService.",
            "note": "Real RunPod adapter is wired but disabled by default; API key values are never exposed.",
        }

    def _future_provider(self, spec: dict, workers: list[dict]) -> dict:
        enabled = self._env_enabled(spec["enabled_env"])
        execution_enabled = self._env_enabled(spec["execution_env"])
        configured = self._env_configured(spec["required_env_vars"])
        import os
        missing = [name for name in spec["required_env_vars"] if not os.environ.get(name)]
        return {
            "provider": spec["provider"],
            "name": spec["name"],
            "enabled": enabled,
            "configured": configured,
            "execution_enabled": False,
            "requested_execution_enabled": execution_enabled,
            "missing_configuration": missing,
            "supports_gpu_jobs": False,
            "supports_cancellation": False,
            "risk_level": "high",
            "worker_count": self._count(workers, spec["provider"]),
            "active_workers": self._active_count(workers, spec["provider"]),
            "required_env_vars": spec["required_env_vars"],
            "cost_warning": spec["cost_warning"],
            "note": "Readiness/dry-run only in v240. No live adapter is wired for this provider yet.",
        }

    def providers(self) -> dict:
        workers = [self._normalize_worker(worker) for worker in self.worker_registry.list_workers()]
        providers = [self._local_provider(workers), self._kaggle_provider(workers), self._runpod_provider(workers)]
        providers.extend(self._future_provider(spec, workers) for spec in FUTURE_CLOUD_PROVIDERS)
        providers = sorted(providers, key=lambda row: PROVIDER_ORDER.index(row["provider"]) if row["provider"] in PROVIDER_ORDER else 99)
        return {
            "providers": providers,
            "count": len(providers),
            "note": "Provider readiness reports booleans and env var names only; secret values are never exposed.",
        }

    def dashboard(self) -> dict:
        workers = [self._normalize_worker(worker) for worker in self.worker_registry.list_workers()]
        provider_rows = self.providers()["providers"]
        active_gpu_workers = sum(1 for worker in workers if worker.get("status") in ("online", "busy"))
        return {
            "total_gpu_workers": len(workers),
            "active_gpu_workers": active_gpu_workers,
            "by_provider": {row["provider"]: row["worker_count"] for row in provider_rows},
            "providers": provider_rows,
            "workers": workers,
            "real_execution_default": "disabled",
            "approval_required_for_real_execution": True,
            "generated_at": self._now(),
        }

    def dry_run(self, payload: dict[str, Any]) -> dict:
        provider = str(payload.get("provider") or "kaggle").strip().lower()[:40]
        title = str(payload.get("title") or "GPU job").strip()[:160] or "GPU job"
        estimated_minutes = payload.get("estimated_duration_minutes")
        provider_rows = {row["provider"]: row for row in self.providers()["providers"]}
        row = provider_rows.get(provider)
        if row is None:
            result = {
                "accepted": False,
                "requires_approval": False,
                "declined_reason": "Unknown GPU provider.",
                "provider": provider,
                "title": title,
                "estimated_cost_note": "No cost estimate available for unknown providers.",
                "missing_configuration": [],
                "next_human_action": "Choose a known provider.",
            }
            self._log("gpu_worker_dry_run", f"Dry-run declined for unknown GPU provider {provider}.", blocked=True)
            return result

        missing = list(row.get("missing_configuration") or [])
        if provider == "kaggle":
            accepted = bool(row.get("execution_enabled"))
            declined_reason = "" if accepted else "Kaggle worker is disabled. Set KAGGLE_WORKER_ENABLED=true before approval can submit a real kernel."
            next_action = "Create an approval-gated durable workflow step for run_kaggle_job." if accepted else "Enable Kaggle intentionally, then rerun dry-run."
        elif provider == "runpod":
            endpoint_from_payload = bool(str(payload.get("endpoint_id") or payload.get("metadata", {}).get("endpoint_id") or "").strip())
            configured = bool(row.get("configured"))
            enabled = bool(row.get("enabled"))
            accepted = enabled and configured and (bool(row.get("execution_enabled")) or endpoint_from_payload)
            if accepted:
                declined_reason = ""
                next_action = "Create an approval-gated durable workflow step for run_runpod_job."
                missing = []
            else:
                declined_reason = "RunPod worker is disabled or missing configuration. Set RUNPOD_WORKER_ENABLED=true, RUNPOD_API_KEY, and a default endpoint or workflow endpoint_id."
                next_action = "Configure RunPod intentionally, then rerun dry-run before approval."
        elif provider == "local":
            accepted = False
            declined_reason = "Local GPU workers are registration/status-only in v240; no local executor is wired."
            next_action = "Use this worker for readiness tracking only, or wait for the v260 execution adapter."
        else:
            accepted = False
            declined_reason = "Provider is readiness/dry-run only in v240; no live cloud adapter is wired."
            next_action = "Approve a future provider-specific adapter before allowing paid execution."

        result = {
            "accepted": accepted,
            "requires_approval": bool(accepted),
            "declined_reason": declined_reason,
            "provider": provider,
            "title": title,
            "estimated_duration_minutes": estimated_minutes,
            "estimated_cost_note": row.get("cost_warning", "Cost estimate unavailable; human approval required before execution."),
            "missing_configuration": [] if provider in ("local", "kaggle") else missing,
            "next_human_action": next_action,
            "execution_path": (
                "durable_workflow.run_kaggle_job" if provider == "kaggle" and accepted
                else "durable_workflow.run_runpod_job" if provider == "runpod" and accepted
                else None
            ),
        }
        self._log(
            "gpu_worker_dry_run",
            f"GPU dry-run for provider={provider}, title='{title}', accepted={accepted}.",
            blocked=not accepted,
        )
        return result

    def register_local_worker(self, payload: dict[str, Any]) -> dict:
        name = str(payload.get("name") or "Local GPU Worker").strip()[:80] or "Local GPU Worker"
        capabilities = payload.get("capabilities") or ["gpu", "local"]
        metadata = {
            "provider": "local",
            "gpu_model": payload.get("gpu_model") or "unknown",
            "gpu_memory_gb": payload.get("gpu_memory_gb"),
            "region": payload.get("region") or "local",
            "runtime": payload.get("runtime") or "unknown",
            "supports_jobs": bool(payload.get("supports_jobs", True)),
            "supports_model_serving": bool(payload.get("supports_model_serving", False)),
            "estimated_cost_per_hour": payload.get("estimated_cost_per_hour", 0),
            "quota_state": payload.get("quota_state") or "user_controlled",
            "requires_approval": True,
            "last_provider_check": self._now(),
            "name": name,
        }
        worker = self.worker_registry.register_worker("local_gpu", capabilities=capabilities, metadata=metadata)
        self._log("gpu_local_worker_registered", f"Registered local GPU worker {worker['worker_id']} ({name}).")
        return worker

    def analytics_summary(self) -> dict:
        dashboard = self.dashboard()
        return {
            "gpu_workers_total": dashboard["total_gpu_workers"],
            "gpu_workers_active": dashboard["active_gpu_workers"],
            "gpu_providers_count": len(dashboard["providers"]),
        }
