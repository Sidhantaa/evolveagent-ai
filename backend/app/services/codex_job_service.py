from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.services.storage_service import StorageService

JOB_STATUSES = {"queued", "running", "passed", "failed", "blocked", "needs_manual_review"}


class CodexJobService:
    filename = "codex_jobs.json"

    def __init__(self, storage: StorageService):
        self.storage = storage

    def list_jobs(self, limit: int | None = None) -> list[dict[str, Any]]:
        jobs = list(reversed(self.storage.read_list(self.filename)))
        if limit is not None:
            return jobs[:limit]
        return jobs

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return next((item for item in self.storage.read_list(self.filename) if item.get("job_id") == job_id), None)

    def get_latest_job_for_issue(self, issue_id: str) -> dict[str, Any] | None:
        jobs = [item for item in self.list_jobs() if item.get("issue_id") == issue_id]
        return jobs[0] if jobs else None

    def create_job(self, data: dict[str, Any]) -> dict[str, Any]:
        job = {
            "job_id": str(uuid4()),
            "issue_id": data["issue_id"],
            "issue_identifier": data.get("issue_identifier", ""),
            "branch_name": data.get("branch_name", ""),
            "handoff_path": data.get("handoff_path", ""),
            "status": "queued",
            "status_detail": "Waiting to start",
            "failure_stage": None,
            "manual_review_required": False,
            "summary": "",
            "started_at": None,
            "completed_at": None,
            "codex_stdout": "",
            "codex_stderr": "",
            "test_results": [],
            "test_result": None,
            "build_result": None,
            "verification_summary": "",
            "changed_files": [],
            "commit_hash": None,
            "linear_done": False,
            "error": None,
        }
        self.storage.append(self.filename, job)
        return job

    def update_job(self, job_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        # Round 32: was read_list() -> mutate -> write_list(), the same
        # lost-update shape rounds 25-31 fixed elsewhere. Real concurrent
        # writers: CodexWorkerService.run_for_issue() calls update_job()
        # ~15 times over a multi-second run (subprocess Codex CLI + git
        # commit/push/verify) -- the background Linear poll worker can run
        # one issue's job inline while a foreground POST runs a different
        # issue's job, racing on this same file.
        def _apply(jobs: list[dict[str, Any]]) -> dict[str, Any] | None:
            job = next((item for item in jobs if item.get("job_id") == job_id), None)
            if job is None:
                return None
            job.update(updates)
            return dict(job)

        return self.storage.update_list(self.filename, _apply)
