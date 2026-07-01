from __future__ import annotations

from datetime import UTC, datetime

from app.services.mcp_connector_service import MCPConnectorService
from app.services.mcp_execution_service import MCPExecutionService

_RISK_WEIGHT = {"high": 3, "medium": 2, "low": 1}


class MCPApprovalsInboxService:
    """v44.0 MCP Approvals Inbox.

    A unified, prioritized queue of everything on the MCP surface that is waiting
    for explicit human approval. Today that is the v42 execution requests in
    ``pending_approval`` status; each item is enriched with the connector name,
    risk level, age, and a priority so a reviewer can triage high-risk/oldest
    items first. Approve/reject actions delegate to the execution service (which
    performs the governance logging), so this layer adds no new execution power —
    it only aggregates and prioritizes what already requires approval.
    """

    def __init__(self, execution_service: MCPExecutionService, connector_service: MCPConnectorService):
        self.executions = execution_service
        self.connectors = connector_service

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _age_seconds(self, created_at: str | None) -> int:
        if not created_at:
            return 0
        try:
            created = datetime.fromisoformat(created_at)
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            return max(0, int((self._now() - created).total_seconds()))
        except (ValueError, TypeError):
            return 0

    def _connector_name(self, connector_id: str | None) -> str:
        if not connector_id:
            return "Unknown connector"
        connector = self.connectors.get_connector(connector_id)
        return connector.get("name") if connector else "Unknown connector"

    def _item(self, request: dict) -> dict:
        risk = request.get("risk_level", "medium")
        age = self._age_seconds(request.get("created_at"))
        return {
            "item_id": request.get("request_id"),
            "source": "mcp_execution",
            "connector_id": request.get("connector_id"),
            "connector_name": self._connector_name(request.get("connector_id")),
            "action_name": request.get("action_name"),
            "risk_level": risk,
            "priority": _RISK_WEIGHT.get(risk, 2),
            "age_seconds": age,
            "created_at": request.get("created_at"),
            "recommended_action": (
                "Review carefully before approving — high-risk action."
                if risk == "high"
                else "Review and approve if appropriate."
            ),
        }

    # ------------------------------------------------------------------
    # Inbox
    # ------------------------------------------------------------------
    def list_inbox(self, risk_level: str | None = None) -> list[dict]:
        pending = [r for r in self.executions.list_requests(limit=500) if r.get("status") == "pending_approval"]
        items = [self._item(r) for r in pending]
        if risk_level in _RISK_WEIGHT:
            items = [i for i in items if i["risk_level"] == risk_level]
        # Highest risk first, then oldest first.
        items.sort(key=lambda i: (-i["priority"], -i["age_seconds"]))
        return items

    def summary(self) -> dict:
        items = self.list_inbox()
        by_risk = {level: sum(1 for i in items if i["risk_level"] == level) for level in ("high", "medium", "low")}
        oldest = max((i["age_seconds"] for i in items), default=0)
        return {
            "pending_count": len(items),
            "by_risk": by_risk,
            "high_risk_pending": by_risk["high"],
            "oldest_pending_seconds": oldest,
            "top_items": items[:5],
            "note": "Unified queue of MCP actions awaiting human approval. Approving/rejecting delegates to the governed execution service.",
        }

    # ------------------------------------------------------------------
    # Decisions (delegate to the execution service, which logs governance)
    # ------------------------------------------------------------------
    def approve(self, item_id: str) -> dict:
        return self.executions.approve_execution(item_id)

    def reject(self, item_id: str) -> dict:
        return self.executions.reject_execution(item_id)

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------
    def analytics_summary(self) -> dict:
        items = self.list_inbox()
        return {
            "mcp_inbox_pending": len(items),
            "mcp_inbox_high_risk_pending": sum(1 for i in items if i["risk_level"] == "high"),
            "mcp_inbox_oldest_pending_seconds": max((i["age_seconds"] for i in items), default=0),
        }
