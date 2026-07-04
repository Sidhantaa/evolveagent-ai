from __future__ import annotations

from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

_DONE = {"done", "completed", "closed", "cancelled"}
_PRIORITY_RANK = {"high": 0, "urgent": 0, "medium": 1, "normal": 1, "low": 2}


class PersonalProductivityService:
    """v74.0 Personal Productivity Brain — help decide what to do next.

    A read-only assistant over goals, life tasks, and deadlines: **priority
    recommendations**, a **daily focus list**, **blocker detection**, an **overdue
    task review**, a **goal-progress summary**, and a "**what should I work on now?**"
    pick. It reads existing local state only and never creates or completes anything.
    Governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _in_ws(item: dict, workspace_id: str | None) -> bool:
        return not workspace_id or item.get("workspace_id") in (None, workspace_id)

    def _open_tasks(self, workspace_id: str | None) -> list[dict]:
        tasks = []
        for t in self.storage.read_list("life_tasks.json"):
            if not isinstance(t, dict) or not self._in_ws(t, workspace_id):
                continue
            if str(t.get("status", "")).lower() in _DONE:
                continue
            tasks.append({
                "id": t.get("task_id"), "title": t.get("title"), "due_date": t.get("due_date"),
                "priority": str(t.get("priority", "medium")).lower(), "status": t.get("status"),
                "source": "task",
            })
        return tasks

    def _priority_key(self, item: dict, today: str) -> tuple:
        overdue = bool(item.get("due_date") and str(item["due_date"])[:10] < today)
        return (0 if overdue else 1, _PRIORITY_RANK.get(item.get("priority"), 1), str(item.get("due_date") or "9999"))

    def brain(self, workspace_id: str | None = None) -> dict:
        today = self._now()[:10]
        tasks = self._open_tasks(workspace_id)
        ranked = sorted(tasks, key=lambda t: self._priority_key(t, today))

        overdue = [t for t in tasks if t.get("due_date") and str(t["due_date"])[:10] < today]
        blockers = [t for t in tasks if "block" in str(t.get("status", "")).lower() or "wait" in str(t.get("status", "")).lower()]

        deadlines = [d for d in self.storage.read_list("life_deadlines.json") if isinstance(d, dict) and self._in_ws(d, workspace_id)]
        upcoming_deadlines = sorted(
            [{"title": d.get("title"), "due_date": d.get("due_date"), "kind": d.get("kind")} for d in deadlines if d.get("due_date") and str(d["due_date"])[:10] >= today],
            key=lambda d: str(d["due_date"]),
        )[:5]

        goals = [g for g in self.storage.read_list("goals.json") if isinstance(g, dict) and self._in_ws(g, workspace_id)]
        open_goals = [g for g in goals if str(g.get("status", "")).lower() not in _DONE]
        progress_values = [float(g.get("progress_percent", 0) or 0) for g in open_goals]
        goal_progress = {
            "open_goals": len(open_goals),
            "avg_progress_pct": round(sum(progress_values) / len(progress_values), 1) if progress_values else 0,
        }

        self.governance.log_event(
            GovernanceEvent(
                task_type="personal_productivity",
                agent_name="Productivity Brain",
                action_type="productivity_reviewed",
                tool_used="PersonalProductivityService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=f"Reviewed productivity: {len(tasks)} open tasks, {len(overdue)} overdue.",
            )
        )
        return {
            "priority_recommendations": ranked[:8],
            "daily_focus": ranked[:3],
            "blockers": blockers,
            "overdue": overdue,
            "upcoming_deadlines": upcoming_deadlines,
            "goal_progress": goal_progress,
            "what_now": self._what_now(ranked, overdue, blockers),
            "open_task_count": len(tasks),
            "note": "Read-only productivity review — nothing is created or completed.",
        }

    @staticmethod
    def _what_now(ranked: list[dict], overdue: list[dict], blockers: list[dict]) -> dict:
        if overdue:
            return {"pick": overdue[0]["title"], "reason": "It's overdue — clear it first."}
        if ranked:
            return {"pick": ranked[0]["title"], "reason": "Highest-priority open item."}
        if blockers:
            return {"pick": blockers[0]["title"], "reason": "Unblock this to move forward."}
        return {"pick": None, "reason": "All clear — no open tasks. Consider planning your next goal."}

    def what_now(self, workspace_id: str | None = None) -> dict:
        return self.brain(workspace_id)["what_now"]

    def analytics_summary(self) -> dict:
        return {"productivity_open_tasks": len(self._open_tasks(None))}

    def summary(self) -> dict:
        brain = self.brain(None)
        return {
            "open_tasks": brain["open_task_count"],
            "overdue": len(brain["overdue"]),
            "blockers": len(brain["blockers"]),
            "what_now": brain["what_now"],
            "note": brain["note"],
        }
