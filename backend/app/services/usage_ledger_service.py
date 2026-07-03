from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

CAPABILITIES = ["text", "image", "transcription", "mcp", "other"]
# Illustrative default per-unit estimate rates (USD). Estimates only — no billing.
_DEFAULT_RATES = {"text": 0.002, "image": 0.02, "transcription": 0.006, "mcp": 0.0, "other": 0.001}


class UsageLedgerService:
    """v50.0 Cost & Usage Ledger (estimates & planning only — no billing).

    A local ledger of API usage estimates (mock or real) with per-workspace
    budgets and threshold warnings, extending the v11 cost-control visibility.
    Costs are **estimates** derived from illustrative per-unit rates; nothing is
    billed, charged, or sent. Stateful actions are governance-logged.
    """

    entries_file = "usage_ledger_entries.json"
    budgets_file = "usage_budgets.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _enum(self, value, allowed: list[str], default: str) -> str:
        candidate = str(value or "").strip().lower()
        return candidate if candidate in allowed else default

    def _num(self, value, default: float = 0.0) -> float:
        try:
            return max(0.0, round(float(value), 6))
        except (TypeError, ValueError):
            return default

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="usage_ledger",
                agent_name="Cost & Usage Ledger",
                action_type=action_type,
                tool_used="UsageLedgerService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=3,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Entries
    # ------------------------------------------------------------------
    def record_usage(self, data: dict) -> dict:
        data = data or {}
        capability = self._enum(data.get("capability"), CAPABILITIES, "other")
        units = self._num(data.get("units"), 1.0) or 1.0
        provided = data.get("estimated_cost")
        estimated_cost = self._num(provided) if provided is not None else round(units * _DEFAULT_RATES[capability], 6)
        entry = {
            "entry_id": str(uuid4()),
            "workspace_id": self._clean(data.get("workspace_id"), 120) or "default",
            "capability": capability,
            "units": units,
            "estimated_cost": estimated_cost,
            "mode": self._enum(data.get("mode"), ["mock", "real"], "mock"),
            "note": "Estimated cost only — no billing or charge is performed.",
            "created_at": self._now(),
        }
        self.storage.append(self.entries_file, entry)
        self._log("usage_recorded", f"Recorded {capability} usage (est ${estimated_cost}).")
        return entry

    def list_entries(self, workspace_id: str | None = None, limit: int = 100) -> list[dict]:
        entries = self.storage.read_list(self.entries_file)
        if workspace_id:
            entries = [e for e in entries if e.get("workspace_id") == workspace_id]
        return list(reversed(entries[-limit:]))

    # ------------------------------------------------------------------
    # Budgets
    # ------------------------------------------------------------------
    def set_budget(self, data: dict) -> dict:
        data = data or {}
        workspace_id = self._clean(data.get("workspace_id"), 120) or "default"
        budgets = self.storage.read_list(self.budgets_file)
        budget = next((b for b in budgets if b.get("workspace_id") == workspace_id), None)
        limit = self._num(data.get("monthly_limit"))
        if budget:
            budget["monthly_limit"] = limit
            budget["updated_at"] = self._now()
            self.storage.write_list(self.budgets_file, budgets)
        else:
            budget = {
                "budget_id": str(uuid4()),
                "workspace_id": workspace_id,
                "monthly_limit": limit,
                "created_at": self._now(),
                "updated_at": self._now(),
            }
            self.storage.append(self.budgets_file, budget)
        self._log("usage_budget_set", f"Set budget for {workspace_id}: ${limit}.")
        return budget

    def list_budgets(self) -> list[dict]:
        return self.storage.read_list(self.budgets_file)

    def _budget_for(self, workspace_id: str) -> float:
        budget = next((b for b in self.storage.read_list(self.budgets_file) if b.get("workspace_id") == workspace_id), None)
        return float(budget.get("monthly_limit", 0)) if budget else 0.0

    # ------------------------------------------------------------------
    # Summary + analytics
    # ------------------------------------------------------------------
    def summary(self, workspace_id: str | None = None) -> dict:
        entries = self.storage.read_list(self.entries_file)
        if workspace_id:
            entries = [e for e in entries if e.get("workspace_id") == workspace_id]
        total = round(sum(e.get("estimated_cost", 0) for e in entries), 6)
        by_capability: dict[str, float] = {}
        for e in entries:
            by_capability[e["capability"]] = round(by_capability.get(e["capability"], 0) + e.get("estimated_cost", 0), 6)
        budget = self._budget_for(workspace_id) if workspace_id else 0.0
        status = "no_budget"
        if budget > 0:
            pct = total / budget
            status = "over" if pct >= 1.0 else "near" if pct >= 0.8 else "under"
        return {
            "workspace_id": workspace_id,
            "entry_count": len(entries),
            "total_estimated_cost": total,
            "by_capability": by_capability,
            "monthly_limit": budget,
            "budget_status": status,
            "warning": "Estimated usage has reached or exceeded the budget." if status == "over" else "Approaching budget." if status == "near" else None,
            "note": "Estimates only — extends v11 cost visibility. No billing, charging, or payment is performed.",
        }

    def analytics_summary(self) -> dict:
        entries = self.storage.read_list(self.entries_file)
        return {
            "usage_entries": len(entries),
            "usage_total_estimated_cost": round(sum(e.get("estimated_cost", 0) for e in entries), 6),
            "usage_budgets": len(self.storage.read_list(self.budgets_file)),
        }
