from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService
from app.services.workspace_service import WorkspaceService


class AgentSchedulerService:
    filename = "agent_jobs.json"
    terminal_states = {"completed", "failed", "canceled"}

    def __init__(
        self,
        storage: StorageService,
        governance: GovernanceService,
        workspace_service: WorkspaceService,
        concurrency_limit: int = 2,
        timeout_seconds: int = 600,
    ):
        self.storage = storage
        self.governance = governance
        self.workspace_service = workspace_service
        self.concurrency_limit = concurrency_limit
        self.timeout_seconds = timeout_seconds

    def create_job(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        workspace_id = self.workspace_service.resolve_workspace_id(data.get("workspace_id"))
        job = {
            "job_id": str(uuid4()),
            "workspace_id": workspace_id,
            "job_type": data.get("job_type") or "workflow",
            "title": data.get("title") or "Agent job",
            "payload": data.get("payload") or {},
            "status": "queued",
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "completed_at": None,
            "heartbeat_at": None,
            "error": None,
            "result_summary": None,
            "lifecycle_events": [{"status": "queued", "created_at": now, "reason": "Job created."}],
        }
        # Round 27: was a hand-rolled read_list() -> append in memory ->
        # write_list() -- the same lost-update shape rounds 25/26 fixed
        # elsewhere, except here the WHOLE list gets written back instead of
        # using the already-atomic storage.append(). Two concurrent
        # create_job() calls (e.g. a Kaggle submit + a durable workflow start)
        # could both read the same snapshot and each write back a list
        # missing the other's new job -- one job silently never gets tracked.
        self.storage.append(self.filename, job)
        self._log(job, "agent_job_created", "Agent job was queued.")
        return job

    def list_jobs(self, status: str | None = None, workspace_id: str | None = None) -> list[dict[str, Any]]:
        jobs = self.storage.read_list(self.filename)
        if status:
            jobs = [job for job in jobs if job.get("status") == status]
        if workspace_id:
            resolved = self.workspace_service.resolve_workspace_id(workspace_id)
            jobs = [job for job in jobs if job.get("workspace_id") == resolved]
        return sorted(jobs, key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return next((job for job in self.storage.read_list(self.filename) if job.get("job_id") == job_id), None)

    def start_next(self) -> dict[str, Any] | None:
        now = datetime.now(UTC).isoformat()

        def _apply(jobs: list[dict[str, Any]]) -> dict[str, Any] | None:
            running = [item for item in jobs if item.get("status") == "running"]
            if len(running) >= self.concurrency_limit:
                return None
            job = next((item for item in jobs if item.get("status") == "queued"), None)
            if job is None:
                return None
            job["status"] = "running"
            job["started_at"] = now
            job["heartbeat_at"] = now
            job["updated_at"] = now
            job.setdefault("lifecycle_events", []).append({"status": "running", "created_at": now, "reason": "Scheduler started job."})
            return dict(job)

        # Round 27: was read_list() -> mutate -> write_list(), the same
        # lost-update shape as everywhere else in this file. Also closes a
        # second-order bug: without one atomic read-decide-write, two
        # concurrent start_next() calls could each separately see "under
        # concurrency_limit" and both dequeue+start a job, exceeding the
        # limit this method exists to enforce.
        job = self.storage.update_list(self.filename, _apply)
        if job is None:
            return None
        self._log(job, "agent_job_started", "Agent job started.")
        return job

    def pause(self, job_id: str, reason: str | None = None) -> dict[str, Any]:
        return self._transition(job_id, "paused", reason or "Job paused by user.")

    def resume(self, job_id: str, reason: str | None = None) -> dict[str, Any]:
        return self._transition(job_id, "queued", reason or "Job resumed and returned to queue.")

    def cancel(self, job_id: str, reason: str | None = None) -> dict[str, Any]:
        return self._transition(job_id, "canceled", reason or "Job canceled by user.")

    def complete(self, job_id: str, result_summary: str = "") -> dict[str, Any]:
        return self._transition(job_id, "completed", result_summary or "Job completed.", result_summary=result_summary)

    def fail(self, job_id: str, error: str) -> dict[str, Any]:
        return self._transition(job_id, "failed", error, error=error)

    def heartbeat(self, job_id: str) -> dict[str, Any]:
        return self._transition(job_id, "running", "Heartbeat recorded.")

    def health(self) -> dict[str, Any]:
        jobs = self.storage.read_list(self.filename)
        now = datetime.now(UTC)
        stale = []
        for job in jobs:
            if job.get("status") != "running":
                continue
            heartbeat = job.get("heartbeat_at") or job.get("started_at")
            if not heartbeat:
                stale.append(job)
                continue
            try:
                parsed = datetime.fromisoformat(heartbeat.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=UTC)
            except ValueError:
                stale.append(job)
                continue
            if (now - parsed).total_seconds() > self.timeout_seconds:
                stale.append(job)
        running_count = sum(1 for job in jobs if job.get("status") == "running")
        return {
            "total_jobs": len(jobs),
            "queued": sum(1 for job in jobs if job.get("status") == "queued"),
            "running": running_count,
            "paused": sum(1 for job in jobs if job.get("status") == "paused"),
            "completed": sum(1 for job in jobs if job.get("status") == "completed"),
            "failed": sum(1 for job in jobs if job.get("status") == "failed"),
            "canceled": sum(1 for job in jobs if job.get("status") == "canceled"),
            "stale_running_jobs": [
                {"job_id": job.get("job_id"), "title": job.get("title"), "heartbeat_at": job.get("heartbeat_at")}
                for job in stale
            ],
            "healthy": not stale,
            # concurrency_limit is only actually ENFORCED by start_next() (the
            # manual dequeue-one-at-a-time flow) -- real automated job
            # producers (DurableWorkflowService, KaggleWorkerService) create
            # and heartbeat jobs directly, bypassing that gate by design (their
            # own execution engines are the real throttle, not this queue).
            # Surfaced here as real, visible signal only -- never blocks a
            # real run/job, matching this app's existing "observability, not
            # enforcement" contract for those two paths.
            "concurrency_limit": self.concurrency_limit,
            "over_concurrency_limit": running_count > self.concurrency_limit,
        }

    def _transition(
        self,
        job_id: str,
        status: str,
        reason: str,
        *,
        error: str | None = None,
        result_summary: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()

        def _apply(jobs: list[dict[str, Any]]) -> dict[str, Any]:
            job = next((item for item in jobs if item.get("job_id") == job_id), None)
            if job is None:
                raise ValueError("Agent job not found.")
            if job.get("status") in self.terminal_states and status not in self.terminal_states:
                raise ValueError("Terminal jobs cannot be resumed or modified.")
            job["status"] = status
            job["updated_at"] = now
            if status == "running":
                job["heartbeat_at"] = now
                if not job.get("started_at"):
                    job["started_at"] = now
            if status in self.terminal_states:
                job["completed_at"] = now
            if error is not None:
                job["error"] = error
            if result_summary is not None:
                job["result_summary"] = result_summary
            job.setdefault("lifecycle_events", []).append({"status": status, "created_at": now, "reason": reason})
            return dict(job)

        # Round 27: was read_list() -> mutate -> write_list() -- the classic
        # lost-update shape. Concretely, a job's heartbeat() racing another
        # job's complete()/fail() (both real, independent transitions on the
        # SAME agent_jobs.json) could silently drop the heartbeat, letting
        # the round-5 stale-job watchdog wrongly kill a genuinely healthy,
        # actively-heartbeating job.
        job = self.storage.update_list(self.filename, _apply)
        self._log(job, f"agent_job_{status}", reason, blocked=status in {"failed", "canceled"})
        return job

    def _log(self, job: dict[str, Any], action_type: str, reason: str, blocked: bool = False) -> None:
        self.governance.log_event(
            GovernanceEvent(
                run_id=job.get("job_id"),
                workspace_id=job.get("workspace_id"),
                task_type=job.get("job_type"),
                agent_name="Agent Scheduler Service",
                action_type=action_type,
                tool_used="AgentSchedulerService",
                permission_level="read_only",
                blocked=blocked,
                risk_score=35 if blocked else 0,
                reason=reason,
            )
        )
