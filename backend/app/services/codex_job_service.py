from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.services.storage_service import StorageService

JOB_STATUSES = {"queued", "running", "passed", "failed", "blocked"}


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
            "started_at": None,
            "completed_at": None,
            "codex_stdout": "",
            "codex_stderr": "",
            "test_results": [],
            "changed_files": [],
            "commit_hash": None,
            "linear_done": False,
            "error": None,
        }
        self.storage.append(self.filename, job)
        return job

    def update_job(self, job_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        jobs = self.storage.read_list(self.filename)
        job = next((item for item in jobs if item.get("job_id") == job_id), None)
        if job is None:
            return None
        job.update(updates)
        self.storage.write_list(self.filename, jobs)
        return job
