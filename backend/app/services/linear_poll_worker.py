from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.services.linear_orchestration_service import LinearOrchestrationService
from app.services.linear_service import LinearService, LinearServiceError

IN_PROGRESS_NAMES = {"in progress", "started", "doing"}


class LinearPollWorker:
    def __init__(
        self,
        linear_service: LinearService,
        orchestration: LinearOrchestrationService,
        codex_worker: Any | None = None,
    ):
        self.linear = linear_service
        self.orchestration = orchestration
        self.codex_worker = codex_worker
        self.running = False
        self._task: asyncio.Task | None = None
        self.last_poll_at: str | None = None
        self.last_error: str | None = None
        self.last_processed: list[dict[str, Any]] = []

    async def start(self) -> None:
        if self.running or not settings.linear_sync_enabled or not settings.linear_configured:
            return
        self.running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self.running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        while self.running:
            await asyncio.to_thread(self.poll_once)
            await asyncio.sleep(max(settings.linear_poll_interval_seconds, 15))

    def poll_once(self) -> list[dict[str, Any]]:
        self.last_poll_at = datetime.now(UTC).isoformat()
        self.last_error = None
        processed: list[dict[str, Any]] = []
        if not settings.linear_sync_enabled or not settings.linear_configured:
            self.last_processed = processed
            return processed

        try:
            issues = self.linear.list_in_progress_issues()
            for issue in issues:
                if not self._is_in_progress(issue):
                    continue
                issue_id = issue["id"]
                link = self.orchestration.links.get_link_by_issue(issue_id)
                if link and link.get("linear_status") == issue.get("status") and link.get("branch_name"):
                    continue
                result = self.orchestration.prepare_in_progress_issue(issue_id)
                entry = {
                    "issue_id": issue_id,
                    "identifier": issue.get("identifier"),
                    "action": "prepared",
                    "branch": result.get("branch", {}).get("branch"),
                }
                if (
                    settings.linear_autonomous_codex_worker
                    and settings.codex_worker_enabled
                    and self.codex_worker is not None
                ):
                    try:
                        codex_result = self.codex_worker.run_for_issue(issue_id)
                        entry["action"] = "prepared_and_codex"
                        entry["codex_job"] = codex_result.get("job")
                        if codex_result.get("error"):
                            entry["codex_error"] = codex_result["error"]
                    except Exception as error:  # noqa: BLE001
                        entry["codex_error"] = str(error)
                processed.append(entry)
            for item in self.orchestration.sync_pending_completions():
                processed.append(item)
        except LinearServiceError as error:
            self.last_error = str(error)
        except Exception as error:  # noqa: BLE001
            self.last_error = str(error)

        self.last_processed = processed
        return processed

    @staticmethod
    def _is_in_progress(issue: dict[str, Any]) -> bool:
        status = (issue.get("status") or "").lower()
        status_type = (issue.get("status_type") or "").lower()
        return status in IN_PROGRESS_NAMES or status_type == "started"

    def status(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "enabled": settings.linear_sync_enabled,
            "configured": settings.linear_configured,
            "poll_interval_seconds": settings.linear_poll_interval_seconds,
            "last_poll_at": self.last_poll_at,
            "last_error": self.last_error,
            "last_processed": self.last_processed,
            "autonomous_codex_worker": settings.linear_autonomous_codex_worker,
            "codex_worker_enabled": settings.codex_worker_enabled,
        }
