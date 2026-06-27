from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

SEVERITY_ORDER = {"high": 3, "medium": 2, "low": 1}


class CompanyBrainService:
    """v25.0 AI Company Brain.

    Combines existing local data — departments, agent workforce/marketplace,
    business operator, chief of staff, project manager, portfolio, governance,
    and analytics — into one company-level operating dashboard. It aggregates and
    summarizes only; it persists strategy plans, decision logs, and reports of its
    own. Every stateful action is governance-logged. No external calls.
    """

    reports_file = "company_brain_reports.json"
    decisions_file = "company_brain_decisions.json"
    strategy_file = "company_brain_strategy.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _string_list(self, values, limit: int = 20, item_max: int = 300) -> list[str]:
        cleaned: list[str] = []
        for value in values or []:
            text = str(value).strip()[:item_max]
            if text and text not in cleaned:
                cleaned.append(text)
            if len(cleaned) >= limit:
                break
        return cleaned

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="company_brain",
                agent_name="AI Company Brain",
                action_type=action_type,
                tool_used="CompanyBrainService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    def _read(self, filename: str) -> list[dict]:
        return self.storage.read_list(filename)

    # ------------------------------------------------------------------
    # Section summaries
    # ------------------------------------------------------------------
    def _departments_summary(self) -> dict:
        departments = self._read("agent_departments.json")
        active = [d for d in departments if d.get("active", True)]
        return {
            "total": len(departments),
            "active": len(active),
            "names": [d.get("name") for d in active][:12],
            "department_runs": len(self._read("department_runs.json")),
        }

    def _workforce_summary(self) -> dict:
        teams = self._read("agent_marketplace_teams.json")
        custom_agents = self._read("custom_agents.json")
        installs = self._read("agent_marketplace_installs.json")
        return {
            "marketplace_teams": len(teams),
            "custom_agents": len([a for a in custom_agents if a.get("enabled", True)]),
            "pack_installs": len(installs),
        }

    def _business_summary(self) -> dict:
        leads = self._read("business_leads.json")
        cases = self._read("business_support_cases.json")
        proposals = self._read("business_proposals.json")
        won = sum(1 for lead in leads if lead.get("status") == "won")
        lost = sum(1 for lead in leads if lead.get("status") == "lost")
        closed = won + lost
        return {
            "total_leads": len(leads),
            "won_leads": won,
            "lost_leads": lost,
            "conversion_rate": round((won / closed) * 100, 2) if closed else 0,
            "open_support_cases": sum(1 for c in cases if c.get("status") in {"open", "waiting", "escalated"}),
            "proposals": len(proposals),
        }

    def _projects_summary(self) -> dict:
        goals = self._read("goals.json")
        active = [g for g in goals if g.get("status") == "active"]
        completed = [g for g in goals if g.get("status") == "completed"]
        portfolio_reports = self._read("portfolio_reports.json")
        return {
            "total_goals": len(goals),
            "active_goals": len(active),
            "completed_goals": len(completed),
            "goal_success_rate": round((len(completed) / len(goals)) * 100, 2) if goals else 0,
            "portfolio_reports": len(portfolio_reports),
        }

    def _risks(self) -> list[dict]:
        risks = [r for r in self._read("project_risks.json") if r.get("status") != "resolved"]
        risks.sort(key=lambda item: SEVERITY_ORDER.get(item.get("severity", "low"), 1), reverse=True)
        return [
            {"title": r.get("title"), "severity": r.get("severity"), "risk_id": r.get("risk_id")}
            for r in risks[:10]
        ]

    def _governance_summary(self) -> dict:
        events = self._read("governance_log.json")
        return {
            "total_events": len(events),
            "blocked_actions": sum(1 for e in events if e.get("blocked")),
        }

    # ------------------------------------------------------------------
    # Health score
    # ------------------------------------------------------------------
    def _health_score(self, business: dict, projects: dict, risks: list[dict], governance: dict, departments: dict) -> int:
        score = 70
        # Risks drag the score down by severity.
        for risk in risks:
            score -= {"high": 6, "medium": 3, "low": 1}.get(risk.get("severity", "low"), 1)
        # Open support load.
        score -= min(15, business.get("open_support_cases", 0) * 2)
        # Blocked governance actions are a warning sign.
        score -= min(10, governance.get("blocked_actions", 0))
        # Positive signals.
        score += min(10, business.get("won_leads", 0) * 2)
        score += min(10, projects.get("completed_goals", 0) * 2)
        if departments.get("active", 0) >= 3:
            score += 5
        return max(0, min(100, score))

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard(self) -> dict:
        departments = self._departments_summary()
        workforce = self._workforce_summary()
        business = self._business_summary()
        projects = self._projects_summary()
        risks = self._risks()
        governance = self._governance_summary()
        health = self._health_score(business, projects, risks, governance, departments)

        recommendations: list[str] = []
        if any(r.get("severity") == "high" for r in risks):
            recommendations.append("Address high-severity risks before scaling new work.")
        if business.get("open_support_cases", 0) > 0:
            recommendations.append("Triage open support cases to protect customer health.")
        if projects.get("active_goals", 0) == 0:
            recommendations.append("No active goals — set a company objective in Mission Control.")
        if departments.get("active", 0) == 0:
            recommendations.append("Seed departments to model the organization.")
        if not recommendations:
            recommendations.append("Operations look healthy — generate a strategy plan for the next cycle.")

        decisions = list(reversed(self._read(self.decisions_file)[-5:]))
        return {
            "company_health_score": health,
            "departments": departments,
            "agent_workforce": workforce,
            "business": business,
            "projects": projects,
            "risks": risks,
            "decisions": decisions,
            "governance": governance,
            "recommended_next_actions": recommendations,
            "generated_at": self._now(),
        }

    # ------------------------------------------------------------------
    # Strategy
    # ------------------------------------------------------------------
    def create_strategy(self, data: dict) -> dict:
        dashboard = self.dashboard()
        strategy = {
            "strategy_id": str(uuid4()),
            "title": self._clean(data.get("title"), 200) or "Company strategy plan",
            "horizon": self._clean(data.get("horizon"), 40) or "quarter",
            "objectives": self._string_list(data.get("objectives")),
            "focus_areas": self._string_list(data.get("focus_areas")) or dashboard["recommended_next_actions"],
            "health_score_at_creation": dashboard["company_health_score"],
            "created_at": self._now(),
        }
        self.storage.append(self.strategy_file, strategy)
        self._log("company_brain_strategy_created", f"Created company strategy: {strategy['title']}.")
        return strategy

    def list_strategy(self, limit: int = 20) -> list[dict]:
        return list(reversed(self._read(self.strategy_file)[-limit:]))

    # ------------------------------------------------------------------
    # Decisions
    # ------------------------------------------------------------------
    def create_decision(self, data: dict) -> dict:
        decision = {
            "decision_id": str(uuid4()),
            "title": self._clean(data.get("title"), 200),
            "context": self._clean(data.get("context"), 2000),
            "decision": self._clean(data.get("decision"), 2000),
            "rationale": self._clean(data.get("rationale"), 2000),
            "impact": self._clean(data.get("impact"), 40) or "medium",
            "created_at": self._now(),
        }
        self.storage.append(self.decisions_file, decision)
        self._log("company_brain_decision_logged", f"Logged company decision: {decision['title'] or decision['decision_id']}.")
        return decision

    def list_decisions(self, limit: int = 50) -> list[dict]:
        return list(reversed(self._read(self.decisions_file)[-limit:]))

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------
    def create_report(self) -> dict:
        dashboard = self.dashboard()
        report = {
            "report_id": str(uuid4()),
            "generated_at": self._now(),
            "company_health_score": dashboard["company_health_score"],
            "headline": (
                f"Company health {dashboard['company_health_score']}/100 · "
                f"{dashboard['departments']['active']} active department(s), "
                f"{dashboard['business']['total_leads']} lead(s), "
                f"{dashboard['projects']['active_goals']} active goal(s)."
            ),
            "departments": dashboard["departments"],
            "agent_workforce": dashboard["agent_workforce"],
            "business": dashboard["business"],
            "projects": dashboard["projects"],
            "top_risks": dashboard["risks"][:5],
            "recommended_next_actions": dashboard["recommended_next_actions"],
            "recent_decisions": dashboard["decisions"],
        }
        self.storage.append(self.reports_file, report)
        self._log("company_brain_report_generated", f"Generated company brain report (health {report['company_health_score']}).")
        return report

    def list_reports(self, limit: int = 20) -> list[dict]:
        return list(reversed(self._read(self.reports_file)[-limit:]))
