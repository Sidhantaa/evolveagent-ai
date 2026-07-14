from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

WORKER_STATUSES = ["online", "offline", "busy"]


class WorkerRegistryService:
    """v220 Compute Fabric -- Worker Registry (first building block).

    A real, local registry of compute workers (e.g. a Kaggle GPU worker) --
    register/heartbeat/list/deregister. This is deliberately the minimum
    architecture the v200 strategy doc calls for before any distributed
    execution: worker registration and heartbeat monitoring. It does not run
    any job itself; job dispatch is a separate, adapter-specific service (see
    KaggleWorkerService) that registers here so a worker's real, current
    status is visible in one place regardless of which adapter backs it.
    """

    workers_file = "compute_workers.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="compute_fabric",
                agent_name="Worker Registry",
                action_type=action_type,
                tool_used="WorkerRegistryService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    def register_worker(self, worker_type: str, capabilities: list[str] | None = None, metadata: dict | None = None) -> dict:
        worker = {
            "worker_id": str(uuid4()),
            "worker_type": str(worker_type or "unknown").strip()[:60],
            "capabilities": [str(c).strip()[:60] for c in (capabilities or [])][:20],
            "metadata": {str(k)[:40]: str(v)[:200] for k, v in list((metadata or {}).items())[:10]},
            "status": "online",
            "registered_at": self._now(),
            "last_heartbeat": self._now(),
        }
        self.storage.append(self.workers_file, worker)
        self._log("worker_registered", f"Registered worker {worker['worker_id']} (type={worker['worker_type']}).")
        return worker

    def heartbeat(self, worker_id: str, status: str = "online") -> dict:
        # Round 26: was a plain read_list() + write_list() pair (the exact
        # lost-update shape round 25 fixed for Kaggle jobs) -- a concurrent
        # register_worker()/heartbeat()/deregister_worker() for a DIFFERENT
        # worker landing between this read and write would be silently
        # overwritten by this call's stale snapshot. update_list() closes it
        # by holding one lock for the whole find-mutate-persist sequence.
        resolved_status = status if status in WORKER_STATUSES else "online"
        last_heartbeat = self._now()

        def _apply(workers: list[dict]) -> dict | None:
            worker = next((w for w in workers if w.get("worker_id") == worker_id), None)
            if worker is None:
                return None
            worker["status"] = resolved_status
            worker["last_heartbeat"] = last_heartbeat
            return dict(worker)

        updated = self.storage.update_list(self.workers_file, _apply)
        if updated is None:
            raise ValueError("Worker not found")
        return updated

    def deregister_worker(self, worker_id: str) -> dict:
        # Same fix as heartbeat() above.
        last_heartbeat = self._now()

        def _apply(workers: list[dict]) -> dict | None:
            worker = next((w for w in workers if w.get("worker_id") == worker_id), None)
            if worker is None:
                return None
            worker["status"] = "offline"
            worker["last_heartbeat"] = last_heartbeat
            return dict(worker)

        updated = self.storage.update_list(self.workers_file, _apply)
        if updated is None:
            raise ValueError("Worker not found")
        self._log("worker_deregistered", f"Deregistered worker {worker_id}.")
        return updated

    def get_worker(self, worker_id: str) -> dict | None:
        return next((w for w in self.storage.read_list(self.workers_file) if w.get("worker_id") == worker_id), None)

    def list_workers(self, status: str | None = None) -> list[dict]:
        workers = self.storage.read_list(self.workers_file)
        if status:
            workers = [w for w in workers if w.get("status") == status]
        return workers

    def dashboard(self) -> dict:
        workers = self.storage.read_list(self.workers_file)
        return {
            "total_workers": len(workers),
            "online": sum(1 for w in workers if w.get("status") == "online"),
            "offline": sum(1 for w in workers if w.get("status") == "offline"),
            "busy": sum(1 for w in workers if w.get("status") == "busy"),
            "by_type": {t: sum(1 for w in workers if w.get("worker_type") == t) for t in {w.get("worker_type") for w in workers}},
            "workers": workers,
        }

    def analytics_summary(self) -> dict:
        workers = self.storage.read_list(self.workers_file)
        return {
            "compute_workers_total": len(workers),
            "compute_workers_online": sum(1 for w in workers if w.get("status") == "online"),
        }
