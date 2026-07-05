from __future__ import annotations

from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Illustrative constants for the MOCK revenue forecast (no real financial data is used).
_AVG_DEAL_USD = 5000
_STAGE_PROBABILITY = {"won": 1.0, "proposal_sent": 0.5, "qualified": 0.3, "contacted": 0.15, "new": 0.05, "lost": 0.0}


class BusinessIntelligenceService:
    """v78.0 Business Intelligence 2.0 — make the business modules more serious.

    A read-only analytics layer over the local business records: a **KPI dashboard**
    (leads, proposals, win rate), a **lead pipeline summary** (by stage), a **proposal
    tracker** (by status), a **mock revenue forecast** (illustrative deal size ×
    stage probability — clearly labelled, never real money), a **risk register**
    (from project risks + derived pipeline risks), a **business report generator**
    (markdown), and an **executive summary export**. Read-only; governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _in_ws(item: dict, workspace_id: str | None) -> bool:
        return not workspace_id or item.get("workspace_id") in (None, workspace_id)

    def _leads(self, workspace_id: str | None) -> list[dict]:
        return [x for x in self.storage.read_list("business_leads.json") if isinstance(x, dict) and self._in_ws(x, workspace_id)]

    def _proposals(self, workspace_id: str | None) -> list[dict]:
        return [x for x in self.storage.read_list("business_proposals.json") if isinstance(x, dict) and self._in_ws(x, workspace_id)]

    @staticmethod
    def _by(field: str, rows: list[dict]) -> dict:
        out: dict[str, int] = {}
        for r in rows:
            key = str(r.get(field) or "unknown")
            out[key] = out.get(key, 0) + 1
        return out

    def kpi_dashboard(self, workspace_id: str | None) -> dict:
        leads = self._leads(workspace_id)
        proposals = self._proposals(workspace_id)
        won = sum(1 for lead in leads if lead.get("status") == "won")
        closed = won + sum(1 for lead in leads if lead.get("status") == "lost")
        return {
            "total_leads": len(leads),
            "total_proposals": len(proposals),
            "won_leads": won,
            "win_rate_pct": round((won / closed) * 100) if closed else 0,
        }

    def lead_pipeline(self, workspace_id: str | None) -> dict:
        leads = self._leads(workspace_id)
        return {"by_stage": self._by("status", leads), "total": len(leads)}

    def proposal_tracker(self, workspace_id: str | None) -> dict:
        proposals = self._proposals(workspace_id)
        return {"by_status": self._by("status", proposals), "total": len(proposals)}

    def revenue_forecast(self, workspace_id: str | None) -> dict:
        leads = self._leads(workspace_id)
        weighted = sum(_STAGE_PROBABILITY.get(lead.get("status"), 0.0) for lead in leads) * _AVG_DEAL_USD
        return {
            "mock_forecast_usd": round(weighted),
            "avg_deal_usd": _AVG_DEAL_USD,
            "basis": "Sum of stage probabilities × illustrative average deal size.",
            "note": "MOCK forecast — illustrative only, not based on real financial data; no billing/payment.",
        }

    def risk_register(self, workspace_id: str | None) -> dict:
        risks = [{"title": r.get("title") or r.get("risk") or "Risk", "level": r.get("level") or r.get("risk_level") or "medium"}
                 for r in self.storage.read_list("project_risks.json") if isinstance(r, dict) and self._in_ws(r, workspace_id)]
        # Derived pipeline risks.
        pipeline = self.lead_pipeline(workspace_id)
        if pipeline["total"] == 0:
            risks.append({"title": "Empty pipeline — no leads recorded.", "level": "high"})
        elif pipeline["by_stage"].get("qualified", 0) + pipeline["by_stage"].get("proposal_sent", 0) == 0:
            risks.append({"title": "No qualified/proposal-stage leads — top-of-funnel only.", "level": "medium"})
        return {"risks": risks[:20], "count": len(risks)}

    def dashboard(self, workspace_id: str | None = None) -> dict:
        self._log("business_intel_viewed", "Rendered the Business Intelligence dashboard.")
        return {
            "kpis": self.kpi_dashboard(workspace_id),
            "lead_pipeline": self.lead_pipeline(workspace_id),
            "proposal_tracker": self.proposal_tracker(workspace_id),
            "revenue_forecast": self.revenue_forecast(workspace_id),
            "risk_register": self.risk_register(workspace_id),
            "note": "Read-only business analytics over local records; forecast is mock; no billing/payment.",
        }

    def report(self, workspace_id: str | None = None) -> dict:
        kpis = self.kpi_dashboard(workspace_id)
        pipeline = self.lead_pipeline(workspace_id)
        forecast = self.revenue_forecast(workspace_id)
        risks = self.risk_register(workspace_id)
        lines = [
            "# Business Report", "", f"_Generated {self._now()}_", "",
            "## KPIs",
            f"- Leads: {kpis['total_leads']} · Proposals: {kpis['total_proposals']} · Won: {kpis['won_leads']} · Win rate: {kpis['win_rate_pct']}%",
            "", "## Pipeline",
            *[f"- {stage}: {count}" for stage, count in pipeline["by_stage"].items()],
            "", "## Revenue (mock)",
            f"- Illustrative weighted forecast: ${forecast['mock_forecast_usd']} ({forecast['note']})",
            "", "## Risks",
            *[f"- [{r['level']}] {r['title']}" for r in risks["risks"]],
            "", "## Executive summary",
            f"- {kpis['total_leads']} leads and {kpis['total_proposals']} proposals; win rate {kpis['win_rate_pct']}%; {risks['count']} risk(s) flagged.",
        ]
        self._log("business_intel_report", "Generated a business report (markdown).")
        return {"format": "markdown", "content": "\n".join(lines),
                "executive_summary": f"{kpis['total_leads']} leads, {kpis['total_proposals']} proposals, {kpis['win_rate_pct']}% win rate, {risks['count']} risk(s)."}

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="business_intelligence",
                agent_name="Business Intelligence",
                action_type=action_type,
                tool_used="BusinessIntelligenceService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def analytics_summary(self) -> dict:
        return {"business_intel_leads": len(self._leads(None)), "business_intel_proposals": len(self._proposals(None))}

    def summary(self) -> dict:
        return {
            "capabilities": ["kpi_dashboard", "lead_pipeline", "proposal_tracker", "revenue_forecast", "risk_register", "report"],
            "note": "Read-only business analytics; revenue forecast is mock; no billing or payment.",
        }
