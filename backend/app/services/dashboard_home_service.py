from __future__ import annotations

from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.health_monitor_service import HealthMonitorService
from app.services.storage_service import StorageService

# Static quick-launch cards → the major surfaces of the OS.
QUICK_LAUNCH = [
    {"label": "Ask the Master Agent", "route": "/api/master-agent", "icon": "brain"},
    {"label": "Global Search", "route": "/api/search", "icon": "search"},
    {"label": "Activity Timeline", "route": "/api/activity", "icon": "route"},
    {"label": "Approvals Center", "route": "/api/approvals-center", "icon": "shield"},
    {"label": "Health & Readiness", "route": "/api/health-monitor", "icon": "gauge"},
    {"label": "Playbooks", "route": "/api/playbooks", "icon": "library"},
    {"label": "Scheduled Tasks", "route": "/api/scheduled-tasks", "icon": "clock"},
    {"label": "EvolveAgent OS 2.0", "route": "/api/os2", "icon": "cpu"},
]


class DashboardHomeService:
    """v64.0 Dashboard Home 2.0 — one professional homepage over the whole OS.

    A single read-only overview: a Today snapshot, the active workspace summary,
    pending approvals, recent runs/routes, system health, upcoming tasks, a set of
    rule-based suggested next actions, and quick-launch cards. It only reads existing
    local state (nothing is created or executed) and is governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService, health_service: HealthMonitorService):
        self.storage = storage
        self.governance = governance_service
        self.health = health_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _is_today(ts: str, today: str) -> bool:
        return isinstance(ts, str) and ts.startswith(today)

    def _pending_approvals(self, workspace_id: str | None) -> list[dict]:
        pending = []
        for item in self.storage.read_list("business_approval_items.json"):
            if item.get("status") == "pending" and (not workspace_id or item.get("workspace_id") in (None, workspace_id)):
                pending.append({"source": "business", "title": item.get("title") or item.get("action_type"), "id": item.get("id") or item.get("approval_id")})
        for req in self.storage.read_list("mcp_execution_requests.json"):
            if req.get("status") == "pending_approval" and (not workspace_id or req.get("workspace_id") in (None, workspace_id)):
                pending.append({"source": "mcp", "title": req.get("action_name") or req.get("connector_slug"), "id": req.get("request_id") or req.get("id")})
        return pending

    def _recent_runs(self, workspace_id: str | None, limit: int = 5) -> list[dict]:
        runs = self.storage.read_list("master_agent_runs.json")
        if workspace_id:
            runs = [r for r in runs if r.get("workspace_id") in (None, workspace_id)]
        recent = list(reversed(runs))[:limit]
        return [{"domain": r.get("primary_domain"), "request": (r.get("request") or "")[:120], "requires_approval": r.get("requires_approval"), "created_at": r.get("created_at")} for r in recent]

    def _upcoming_tasks(self, workspace_id: str | None, limit: int = 5) -> list[dict]:
        upcoming = []
        for task in self.storage.read_list("scheduled_tasks.json"):
            if task.get("enabled", True) and (not workspace_id or task.get("workspace_id") in (None, workspace_id)):
                upcoming.append({"source": "scheduled", "title": task.get("name"), "schedule": task.get("schedule")})
        for task in self.storage.read_list("life_tasks.json"):
            if task.get("status") not in ("done", "completed") and (not workspace_id or task.get("workspace_id") in (None, workspace_id)):
                upcoming.append({"source": "life", "title": task.get("title") or task.get("name"), "schedule": task.get("due") or task.get("due_date")})
        return upcoming[:limit]

    def _suggested_actions(self, pending: list[dict], health: dict, upcoming: list[dict]) -> list[str]:
        actions = []
        if pending:
            actions.append(f"Review {len(pending)} pending approval(s) in the Approvals Center")
        if health.get("status") and health["status"] != "healthy":
            actions.append(f"Platform health is {health['status']} — open Health & Readiness")
        if upcoming:
            actions.append(f"You have {len(upcoming)} upcoming task(s)")
        if not actions:
            actions.append("All clear — ask the Master Agent what to work on next")
        return actions[:5]

    def home(self, workspace_id: str | None = None) -> dict:
        today = self._now()[:10]
        workspaces = self.storage.read_list("workspaces.json")
        active_ws = None
        if workspace_id:
            active_ws = next((w for w in workspaces if (w.get("workspace_id") or w.get("id")) == workspace_id), None)

        governance = self.storage.read_list("governance_log.json")
        runs_today = sum(1 for e in governance if self._is_today(e.get("timestamp") or e.get("created_at") or "", today) and e.get("task_type") not in ("dashboard_home",))
        pending = self._pending_approvals(workspace_id)
        recent_runs = self._recent_runs(workspace_id)
        upcoming = self._upcoming_tasks(workspace_id)
        health = self.health.dashboard()

        result = {
            "today": {
                "date": today,
                "events_today": runs_today,
                "pending_approvals": len(pending),
                "upcoming_tasks": len(upcoming),
                "health_status": health.get("status"),
            },
            "active_workspace": {
                "workspace_id": workspace_id,
                "name": (active_ws or {}).get("name") if active_ws else "All workspaces",
                "total_workspaces": len(workspaces),
            },
            "pending_approvals": pending[:8],
            "recent_runs": recent_runs,
            "system_health": {"status": health.get("status"), "score": health.get("health_score"), "recommendations": health.get("recommendations", [])[:3]},
            "upcoming_tasks": upcoming,
            "suggested_actions": self._suggested_actions(pending, health, upcoming),
            "quick_launch": QUICK_LAUNCH,
            "note": "Read-only homepage overview — aggregates existing local state; nothing is created or executed.",
        }
        self.governance.log_event(
            GovernanceEvent(
                task_type="dashboard_home",
                agent_name="Dashboard Home",
                action_type="dashboard_home_viewed",
                tool_used="DashboardHomeService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason="Rendered the Dashboard Home overview.",
            )
        )
        return result

    def analytics_summary(self) -> dict:
        return {
            "dashboard_quick_launch_cards": len(QUICK_LAUNCH),
        }
