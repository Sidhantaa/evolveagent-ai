from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.health_monitor_service import HealthMonitorService
from app.services.provider_control_service import ProviderControlService
from app.services.storage_service import StorageService

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


class NotificationsInboxService:
    """v69.0 Unified Notifications Inbox 2.0 — make alerts actionable.

    Aggregates live signals into one actionable inbox: approval alerts, failed/blocked
    run alerts (from the governance log), provider-fallback alerts, scheduled-task
    reminders, and health warnings. Each item carries a severity, a link to its source
    route, and a stable key so generation is **idempotent** (an unresolved item is not
    duplicated). Items can be **marked resolved** and are **grouped by severity**. It is
    additive to the v56 Notifications Center (distinct ``/api/notifications-inbox``) and
    read-only against source data; generation/resolution are governance-logged.
    """

    inbox_file = "notifications_inbox.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, health_service: HealthMonitorService, provider_service: ProviderControlService):
        self.storage = storage
        self.governance = governance_service
        self.health = health_service
        self.providers = provider_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="notifications_inbox",
                agent_name="Notifications Inbox",
                action_type=action_type,
                tool_used="NotificationsInboxService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Signal derivation (read-only scans of existing state)
    # ------------------------------------------------------------------
    def _signals(self) -> list[dict]:
        signals: list[dict] = []

        # Approval alerts
        biz_pending = [a for a in self.storage.read_list("business_approval_items.json") if a.get("status") == "pending"]
        mcp_pending = [r for r in self.storage.read_list("mcp_execution_requests.json") if r.get("status") == "pending_approval"]
        pending = len(biz_pending) + len(mcp_pending)
        if pending:
            signals.append({"key": f"approvals:{pending}", "type": "approval", "severity": "warning",
                            "title": f"{pending} approval(s) pending", "source_route": "/api/approvals-center"})

        # Failed / blocked run alerts (governance blocked events)
        blocked = [e for e in self.storage.read_list("governance_log.json") if e.get("blocked")]
        if blocked:
            signals.append({"key": f"blocked:{len(blocked)}", "type": "failed", "severity": "critical",
                            "title": f"{len(blocked)} blocked/failed action(s) recorded", "source_route": "/api/governance"})

        # Provider fallback alerts (a capability is set to real but no provider key is ready)
        dash = self.providers.dashboard()
        any_ready = any(p["ready"] and p["id"] != "local" for p in dash["providers"])
        real_caps = [c for c, m in (dash.get("capability_modes") or {}).items() if m == "real"]
        if real_caps and not any_ready:
            signals.append({"key": f"fallback:{','.join(sorted(real_caps))}", "type": "provider", "severity": "warning",
                            "title": f"Capabilities set to real ({', '.join(real_caps)}) but no provider key is ready — using fallback", "source_route": "/api/provider-control"})

        # Scheduled-task reminders (enabled tasks)
        due = [t for t in self.storage.read_list("scheduled_tasks.json") if t.get("enabled", True)]
        if due:
            signals.append({"key": f"scheduled:{len(due)}", "type": "reminder", "severity": "info",
                            "title": f"{len(due)} scheduled task(s) active", "source_route": "/api/scheduled-tasks"})

        # Health warnings
        health = self.health.dashboard()
        if health.get("status") and health["status"] != "healthy":
            signals.append({"key": f"health:{health['status']}", "type": "health", "severity": "critical" if health["status"] == "unhealthy" else "warning",
                            "title": f"Platform health is {health['status']} (score {health.get('health_score')})", "source_route": "/api/health-monitor"})

        return signals

    def generate(self) -> dict:
        existing = self.storage.read_list(self.inbox_file)
        unresolved_keys = {i["key"] for i in existing if not i.get("resolved")}
        added = 0
        for signal in self._signals():
            if signal["key"] in unresolved_keys:
                continue  # idempotent — don't duplicate an unresolved item
            existing.append({
                "id": str(uuid4()),
                "key": signal["key"],
                "type": signal["type"],
                "severity": signal["severity"],
                "title": signal["title"],
                "source_route": signal["source_route"],
                "resolved": False,
                "created_at": self._now(),
            })
            added += 1
        self.storage.write_list(self.inbox_file, existing)
        self._log("notifications_inbox_generated", f"Generated {added} new inbox item(s).")
        return {"generated": added, **self.list_items()}

    def list_items(self, severity: str | None = None, include_resolved: bool = False) -> dict:
        items = self.storage.read_list(self.inbox_file)
        if not include_resolved:
            items = [i for i in items if not i.get("resolved")]
        if severity:
            items = [i for i in items if i.get("severity") == severity]
        items = sorted(items, key=lambda i: (SEVERITY_ORDER.get(i.get("severity"), 3), i.get("created_at", "")))
        by_severity: dict[str, int] = {}
        for item in items:
            by_severity[item["severity"]] = by_severity.get(item["severity"], 0) + 1
        return {"items": items, "count": len(items), "by_severity": by_severity}

    def resolve(self, item_id: str) -> dict:
        items = self.storage.read_list(self.inbox_file)
        target = next((i for i in items if i.get("id") == item_id), None)
        if target is None:
            raise ValueError("Notification not found")
        target["resolved"] = True
        target["resolved_at"] = self._now()
        self.storage.write_list(self.inbox_file, items)
        self._log("notifications_inbox_resolved", "Marked an inbox item resolved.")
        return {"id": item_id, "resolved": True}

    def analytics_summary(self) -> dict:
        items = self.storage.read_list(self.inbox_file)
        return {
            "notifications_inbox_total": len(items),
            "notifications_inbox_unresolved": sum(1 for i in items if not i.get("resolved")),
        }

    def summary(self) -> dict:
        unresolved = self.list_items()
        return {
            "unresolved_count": unresolved["count"],
            "by_severity": unresolved["by_severity"],
            "note": "Actionable inbox aggregating approvals, failed runs, provider fallback, reminders, and health — additive to the v56 center.",
        }
