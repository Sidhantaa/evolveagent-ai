from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.health_monitor_service import HealthMonitorService
from app.services.storage_service import StorageService

SEVERITIES = ["info", "warning", "critical"]


class NotificationsCenterService:
    """v56.0 Notifications & Alerts Center (local digest — no real sending).

    Turns platform signals — blocked governance actions, degraded health, and
    pending-approval backlog — into an **in-app** notifications feed the user can
    acknowledge. It sends nothing externally: no email, SMS, or push. Generation
    is idempotent per signal (an unacknowledged notification with the same
    signature is not duplicated). Generation and acknowledgement are
    governance-logged.
    """

    notifications_file = "notifications.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, health_service: HealthMonitorService):
        self.storage = storage
        self.governance = governance_service
        self.health = health_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="notifications_center",
                agent_name="Notifications & Alerts Center",
                action_type=action_type,
                tool_used="NotificationsCenterService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=3,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Signal collection
    # ------------------------------------------------------------------
    def _candidate_signals(self) -> list[dict]:
        signals: list[dict] = []

        governance = self.storage.read_list("governance_log.json")
        blocked = sum(1 for e in governance if e.get("blocked"))
        if blocked > 0:
            signals.append({"type": "governance_block", "severity": "critical", "signature": f"governance_block:{blocked}", "message": f"{blocked} governance-blocked action(s) recorded."})

        health = self.health.dashboard()
        if health.get("status") != "healthy":
            signals.append({"type": "health", "severity": "warning" if health.get("status") == "degraded" else "critical", "signature": f"health:{health.get('status')}:{health.get('health_score')}", "message": f"Platform health is {health.get('status')} (score {health.get('health_score')})."})

        mcp_pending = sum(1 for r in self.storage.read_list("mcp_execution_requests.json") if r.get("status") == "pending_approval")
        biz_pending = sum(1 for a in self.storage.read_list("business_approval_items.json") if a.get("status") == "pending")
        backlog = mcp_pending + biz_pending
        if backlog > 0:
            signals.append({"type": "approvals_backlog", "severity": "warning" if backlog >= 10 else "info", "signature": f"approvals_backlog:{backlog}", "message": f"{backlog} approval(s) awaiting review ({mcp_pending} MCP, {biz_pending} business)."})

        return signals

    # ------------------------------------------------------------------
    # Generate / list / acknowledge
    # ------------------------------------------------------------------
    def generate(self) -> dict:
        existing = self.storage.read_list(self.notifications_file)
        open_signatures = {n.get("signature") for n in existing if not n.get("acknowledged")}
        created = []
        for signal in self._candidate_signals():
            if signal["signature"] in open_signatures:
                continue  # idempotent — don't duplicate an open notification
            notification = {
                "notif_id": str(uuid4()),
                "type": signal["type"],
                "severity": signal["severity"],
                "message": signal["message"],
                "signature": signal["signature"],
                "acknowledged": False,
                "created_at": self._now(),
            }
            self.storage.append(self.notifications_file, notification)
            created.append(notification)
        self._log("notifications_generated", f"Generated {len(created)} notification(s) (local digest; nothing sent).")
        return {"created": created, "created_count": len(created), "note": "Local in-app digest only — no email, SMS, or push is sent."}

    def list_notifications(self, unacknowledged_only: bool = False, limit: int = 100) -> list[dict]:
        items = self.storage.read_list(self.notifications_file)
        if unacknowledged_only:
            items = [n for n in items if not n.get("acknowledged")]
        return list(reversed(items[-limit:]))

    def acknowledge(self, notif_id: str) -> dict:
        items = self.storage.read_list(self.notifications_file)
        notification = next((n for n in items if n.get("notif_id") == notif_id), None)
        if notification is None:
            raise ValueError("Notification not found")
        notification["acknowledged"] = True
        notification["acknowledged_at"] = self._now()
        self.storage.write_list(self.notifications_file, items)
        self._log("notification_acknowledged", f"Acknowledged notification {notif_id}.")
        return notification

    # ------------------------------------------------------------------
    # Summary + analytics
    # ------------------------------------------------------------------
    def summary(self) -> dict:
        items = self.storage.read_list(self.notifications_file)
        unread = [n for n in items if not n.get("acknowledged")]
        by_severity = {s: sum(1 for n in unread if n.get("severity") == s) for s in SEVERITIES}
        return {
            "total": len(items),
            "unread": len(unread),
            "by_severity": by_severity,
            "critical_unread": by_severity["critical"],
            "recent": self.list_notifications(limit=10),
            "note": "In-app digest only — no external delivery (email/SMS/push).",
        }

    def analytics_summary(self) -> dict:
        items = self.storage.read_list(self.notifications_file)
        return {
            "notifications_total": len(items),
            "notifications_unread": sum(1 for n in items if not n.get("acknowledged")),
        }
