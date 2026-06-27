from __future__ import annotations

from app.services.storage_service import StorageService


class OSSchedulerService:
    """EVO-323 OS-Level Agent Scheduler overview.

    A platform overview layer — NOT a replacement for the existing
    AgentSchedulerService. It aggregates queue/approval/automation state across
    agent_jobs, autopilot_runs, approval_chains, and codex_jobs to give an
    OS-level snapshot of scheduling health. It does not run a background loop or
    mutate any job state.
    """

    def __init__(self, storage: StorageService):
        self.storage = storage

    def overview(self) -> dict:
        jobs = self.storage.read_list("agent_jobs.json")
        autopilot_runs = self.storage.read_list("autopilot_runs.json")
        approvals = self.storage.read_list("approval_chains.json")
        codex_jobs = self.storage.read_list("codex_jobs.json")

        queued_jobs = sum(1 for job in jobs if job.get("status") == "queued")
        running_jobs = sum(1 for job in jobs if job.get("status") == "running")
        paused_jobs = sum(1 for job in jobs if job.get("status") == "paused")
        failed_jobs = sum(1 for job in jobs if job.get("status") == "failed")
        pending_approvals = sum(1 for chain in approvals if chain.get("status") == "pending")
        active_codex_jobs = sum(1 for job in codex_jobs if job.get("status") in {"queued", "running"})

        bottlenecks: list[str] = []
        if pending_approvals:
            bottlenecks.append(f"{pending_approvals} approval(s) pending human review.")
        if queued_jobs > running_jobs and queued_jobs >= 5:
            bottlenecks.append(f"{queued_jobs} job(s) queued and waiting to start.")
        if failed_jobs:
            bottlenecks.append(f"{failed_jobs} job(s) failed and may need a retry.")
        if paused_jobs:
            bottlenecks.append(f"{paused_jobs} job(s) paused.")

        if failed_jobs or pending_approvals > 5:
            scheduler_health = "blocked"
        elif bottlenecks:
            scheduler_health = "watch"
        else:
            scheduler_health = "healthy"

        recommendations: list[str] = []
        if pending_approvals:
            recommendations.append("Review pending approvals to unblock automation.")
        if failed_jobs:
            recommendations.append("Inspect failed jobs and retry or cancel them.")
        if queued_jobs >= 5 and running_jobs == 0:
            recommendations.append("Start the scheduler tick to drain the job queue.")
        if not recommendations:
            recommendations.append("Scheduler is flowing; no action required.")

        return {
            "queued_jobs": queued_jobs,
            "running_jobs": running_jobs,
            "paused_jobs": paused_jobs,
            "failed_jobs": failed_jobs,
            "pending_approvals": pending_approvals,
            "autopilot_runs": len(autopilot_runs),
            "codex_jobs": active_codex_jobs,
            "scheduler_health": scheduler_health,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
        }
