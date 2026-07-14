from datetime import UTC, datetime
from typing import Any

from app.services.storage_service import StorageService

LINK_STATUSES = {"synced", "selected", "running", "completed", "failed", "blocked"}


class LinearLinkService:
    filename = "linear_links.json"

    def __init__(self, storage: StorageService):
        self.storage = storage

    def list_links(self, workspace_id: str | None = None) -> list[dict[str, Any]]:
        links = self.storage.read_list(self.filename)
        if workspace_id:
            links = [item for item in links if item.get("workspace_id") == workspace_id]
        return sorted(links, key=lambda item: item.get("last_synced_at") or "", reverse=True)

    def get_link_by_issue(self, issue_id: str) -> dict[str, Any] | None:
        return next(
            (item for item in self.storage.read_list(self.filename) if item.get("linear_issue_id") == issue_id),
            None,
        )

    def get_link_by_goal_task(self, goal_id: str, task_id: str | None = None) -> dict[str, Any] | None:
        for item in self.storage.read_list(self.filename):
            if item.get("goal_id") != goal_id:
                continue
            if task_id is None or item.get("task_id") == task_id:
                return item
        return None

    def create_or_update_link(self, data: dict[str, Any]) -> dict[str, Any]:
        # Round 31: was read_list() -> mutate -> write_list(), the same
        # lost-update shape rounds 25-30 fixed elsewhere. Real concurrent
        # writers on both sides: the background Linear poll worker updates
        # links every tick, racing foreground routes (issue select/run/
        # complete, git-webhook commit/push events) for a DIFFERENT link.
        now = datetime.now(UTC).isoformat()

        def _apply(links: list[dict[str, Any]]) -> dict[str, Any]:
            existing = next(
                (item for item in links if item.get("linear_issue_id") == data.get("linear_issue_id")),
                None,
            )
            if existing:
                existing.update(data)
                existing["last_synced_at"] = data.get("last_synced_at", now)
                return dict(existing)

            link = {
                "linear_issue_id": data["linear_issue_id"],
                "linear_identifier": data.get("linear_identifier", ""),
                "linear_url": data.get("linear_url", ""),
                "goal_id": data.get("goal_id"),
                "task_id": data.get("task_id"),
                "workspace_id": data.get("workspace_id"),
                "status": data.get("status", "synced"),
                "last_synced_at": now,
                "last_run_at": data.get("last_run_at"),
                "linear_status": data.get("linear_status"),
                "branch_name": data.get("branch_name"),
                "commits": data.get("commits", []),
                "pushes": data.get("pushes", []),
                "notes": data.get("notes", []),
            }
            links.append(link)
            return dict(link)

        return self.storage.update_list(self.filename, _apply)

    def update_status(self, issue_id: str, status: str, note: str | None = None) -> dict[str, Any] | None:
        if status not in LINK_STATUSES:
            status = "synced"
        now = datetime.now(UTC).isoformat()

        def _apply(links: list[dict[str, Any]]) -> dict[str, Any] | None:
            link = next((item for item in links if item.get("linear_issue_id") == issue_id), None)
            if link is None:
                return None
            link["status"] = status
            if note:
                link.setdefault("notes", []).append({"at": now, "note": note})
            return dict(link)

        return self.storage.update_list(self.filename, _apply)

    def append_commit(self, issue_id: str, commit: dict[str, Any]) -> dict[str, Any] | None:
        def _apply(links: list[dict[str, Any]]) -> dict[str, Any] | None:
            link = next((item for item in links if item.get("linear_issue_id") == issue_id), None)
            if link is None:
                return None
            link.setdefault("commits", []).append(commit)
            return dict(link)

        return self.storage.update_list(self.filename, _apply)

    def append_push(self, issue_id: str, push: dict[str, Any]) -> dict[str, Any] | None:
        def _apply(links: list[dict[str, Any]]) -> dict[str, Any] | None:
            link = next((item for item in links if item.get("linear_issue_id") == issue_id), None)
            if link is None:
                return None
            link.setdefault("pushes", []).append(push)
            return dict(link)

        return self.storage.update_list(self.filename, _apply)
