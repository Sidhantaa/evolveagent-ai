from __future__ import annotations

from datetime import UTC, datetime

from app.services.business_operator_advanced_service import BusinessOperatorAdvancedService
from app.services.mcp_execution_service import MCPExecutionService

_RISK_WEIGHT = {"high": 3, "medium": 2, "low": 1}
# Business-operator approval kinds → a normalized risk level.
_BIZ_KIND_RISK = {"payment": "high", "high_risk": "high", "external_send": "medium", "data_share": "medium"}
SOURCES = ["mcp_execution", "business_operator"]


class UnifiedApprovalsService:
    """v48.0 Unified Approvals Center.

    Generalizes the v44 MCP approvals inbox across **all** approval sources into
    one prioritized, governed queue — today the MCP execution requests (v42) and
    the business-operator approval items (v33). Each item is normalized with a
    source, title, risk level, and age, and sorted high-risk / oldest first.
    Approve/reject **delegate to the owning service** (which performs the
    governance logging and state transition); this layer adds no new execution
    power — it only aggregates, prioritizes, and routes decisions.
    """

    def __init__(self, execution_service: MCPExecutionService, business_operator_service: BusinessOperatorAdvancedService):
        self.executions = execution_service
        self.business = business_operator_service

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

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------
    def _mcp_items(self) -> list[dict]:
        items = []
        for r in self.executions.list_requests(limit=500):
            if r.get("status") != "pending_approval":
                continue
            risk = r.get("risk_level", "medium")
            items.append({
                "source": "mcp_execution",
                "item_id": r.get("request_id"),
                "title": f"MCP action: {r.get('action_name')}",
                "risk_level": risk,
                "priority": _RISK_WEIGHT.get(risk, 2),
                "age_seconds": self._age_seconds(r.get("created_at")),
                "created_at": r.get("created_at"),
            })
        return items

    def _business_items(self) -> list[dict]:
        items = []
        for a in self.business.list_approvals():
            if a.get("status") != "pending":
                continue
            risk = _BIZ_KIND_RISK.get(a.get("kind"), "medium")
            items.append({
                "source": "business_operator",
                "item_id": a.get("approval_id"),
                "title": a.get("title") or f"{a.get('kind')} approval",
                "risk_level": risk,
                "priority": _RISK_WEIGHT.get(risk, 2),
                "age_seconds": self._age_seconds(a.get("created_at")),
                "created_at": a.get("created_at"),
            })
        return items

    def list_pending(self, source: str | None = None) -> list[dict]:
        items = self._mcp_items() + self._business_items()
        if source in SOURCES:
            items = [i for i in items if i["source"] == source]
        items.sort(key=lambda i: (-i["priority"], -i["age_seconds"]))
        return items

    def summary(self) -> dict:
        items = self.list_pending()
        by_source = {s: sum(1 for i in items if i["source"] == s) for s in SOURCES}
        by_risk = {level: sum(1 for i in items if i["risk_level"] == level) for level in ("high", "medium", "low")}
        return {
            "pending_count": len(items),
            "by_source": by_source,
            "by_risk": by_risk,
            "high_risk_pending": by_risk["high"],
            "oldest_pending_seconds": max((i["age_seconds"] for i in items), default=0),
            "sources": SOURCES,
            "top_items": items[:5],
            "note": "Unified queue across all approval sources. Approve/reject delegates to the owning governed service.",
        }

    # ------------------------------------------------------------------
    # Decisions (delegate to the owning service)
    # ------------------------------------------------------------------
    def _decide(self, source: str, item_id: str, approve: bool) -> dict:
        if source == "mcp_execution":
            return self.executions.approve_execution(item_id) if approve else self.executions.reject_execution(item_id)
        if source == "business_operator":
            return self.business.update_approval(item_id, "approved" if approve else "rejected")
        raise ValueError("Unknown approval source")

    def approve(self, source: str, item_id: str) -> dict:
        return self._decide(source, item_id, True)

    def reject(self, source: str, item_id: str) -> dict:
        return self._decide(source, item_id, False)

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------
    def analytics_summary(self) -> dict:
        items = self.list_pending()
        return {
            "approvals_center_pending": len(items),
            "approvals_center_high_risk_pending": sum(1 for i in items if i["risk_level"] == "high"),
            "approvals_center_sources": len(SOURCES),
        }
