from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

CREDIBILITY = ["low", "medium", "high"]
SCORE_FIELDS = ("impact", "feasibility", "novelty")  # 1-5; risk is inverse


class InnovationLabService:
    """v36.0 Autonomous Research + Innovation Lab.

    Tracks market research, competitors, trends, ideas (scored), experiment and
    prototype plans, and generates innovation reports — all from local/manual
    records. It does NOT browse the web or scrape externally; research is entered
    by the user or supplied by existing safe services. Stateful actions are
    governance-logged.
    """

    research_file = "innovation_research_items.json"
    competitors_file = "innovation_competitors.json"
    trends_file = "innovation_trends.json"
    ideas_file = "innovation_ideas.json"
    experiments_file = "innovation_experiments.json"
    prototypes_file = "innovation_prototypes.json"
    reports_file = "innovation_reports.json"

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

    def _string_list(self, values, limit: int = 30, item_max: int = 300) -> list[str]:
        cleaned: list[str] = []
        for value in values or []:
            text = str(value).strip()[:item_max]
            if text and text not in cleaned:
                cleaned.append(text)
            if len(cleaned) >= limit:
                break
        return cleaned

    def _score(self, value, default: int = 3) -> int:
        try:
            return max(1, min(5, int(value)))
        except (TypeError, ValueError):
            return default

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="innovation_lab",
                agent_name="Innovation Lab",
                action_type=action_type,
                tool_used="InnovationLabService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Research items
    # ------------------------------------------------------------------
    def create_research(self, data: dict) -> dict:
        item = {
            "research_id": str(uuid4()),
            "title": self._clean(data.get("title"), 200),
            "source": self._clean(data.get("source"), 300),
            "credibility": self._enum(data.get("credibility"), CREDIBILITY, "medium"),
            "notes": self._clean(data.get("notes"), 4000),
            "tags": self._string_list(data.get("tags")),
            "created_at": self._now(),
        }
        self.storage.append(self.research_file, item)
        self._log("innovation_research_created", f"Added research item: {item['title'] or item['research_id']}.")
        return item

    def list_research(self) -> list[dict]:
        return self.storage.read_list(self.research_file)

    # ------------------------------------------------------------------
    # Competitors
    # ------------------------------------------------------------------
    def create_competitor(self, data: dict) -> dict:
        competitor = {
            "competitor_id": str(uuid4()),
            "name": self._clean(data.get("name"), 200),
            "category": self._clean(data.get("category"), 120),
            "strengths": self._string_list(data.get("strengths")),
            "weaknesses": self._string_list(data.get("weaknesses")),
            "notes": self._clean(data.get("notes"), 2000),
            "created_at": self._now(),
        }
        self.storage.append(self.competitors_file, competitor)
        self._log("innovation_competitor_created", f"Added competitor: {competitor['name']}.")
        return competitor

    def list_competitors(self) -> list[dict]:
        return self.storage.read_list(self.competitors_file)

    # ------------------------------------------------------------------
    # Trends
    # ------------------------------------------------------------------
    def create_trend(self, data: dict) -> dict:
        trend = {
            "trend_id": str(uuid4()),
            "title": self._clean(data.get("title"), 200),
            "direction": self._enum(data.get("direction"), ["rising", "flat", "declining"], "rising"),
            "evidence_notes": self._string_list(data.get("evidence_notes")),
            "confidence": self._enum(data.get("confidence"), CREDIBILITY, "medium"),
            "created_at": self._now(),
        }
        self.storage.append(self.trends_file, trend)
        self._log("innovation_trend_created", f"Tracked trend: {trend['title']}.")
        return trend

    def list_trends(self) -> list[dict]:
        return self.storage.read_list(self.trends_file)

    # ------------------------------------------------------------------
    # Ideas (scored)
    # ------------------------------------------------------------------
    def create_idea(self, data: dict) -> dict:
        impact = self._score(data.get("impact"))
        feasibility = self._score(data.get("feasibility"))
        novelty = self._score(data.get("novelty"))
        risk = self._score(data.get("risk"))
        # Composite favors high impact/feasibility/novelty, penalizes risk.
        composite = round(((impact + feasibility + novelty) * 2) - (risk * 1.5), 2)
        idea = {
            "idea_id": str(uuid4()),
            "title": self._clean(data.get("title"), 200),
            "description": self._clean(data.get("description"), 2000),
            "impact": impact,
            "feasibility": feasibility,
            "novelty": novelty,
            "risk": risk,
            "composite_score": composite,
            "tags": self._string_list(data.get("tags")),
            "created_at": self._now(),
        }
        self.storage.append(self.ideas_file, idea)
        self._log("innovation_idea_created", f"Scored idea '{idea['title']}' (composite {composite}).")
        return idea

    def list_ideas(self) -> list[dict]:
        return list(sorted(self.storage.read_list(self.ideas_file), key=lambda i: i.get("composite_score", 0), reverse=True))

    # ------------------------------------------------------------------
    # Experiments
    # ------------------------------------------------------------------
    def create_experiment(self, data: dict) -> dict:
        experiment = {
            "experiment_id": str(uuid4()),
            "title": self._clean(data.get("title"), 200),
            "hypothesis": self._clean(data.get("hypothesis"), 2000),
            "method": self._clean(data.get("method"), 2000),
            "success_metrics": self._string_list(data.get("success_metrics")),
            "status": "planned",
            "created_at": self._now(),
        }
        self.storage.append(self.experiments_file, experiment)
        self._log("innovation_experiment_created", f"Created experiment plan: {experiment['title']}.")
        return experiment

    def list_experiments(self) -> list[dict]:
        return self.storage.read_list(self.experiments_file)

    # ------------------------------------------------------------------
    # Prototypes
    # ------------------------------------------------------------------
    def create_prototype(self, data: dict) -> dict:
        prototype = {
            "prototype_id": str(uuid4()),
            "title": self._clean(data.get("title"), 200),
            "phases": self._string_list(data.get("phases")) or ["Define", "Build mock", "Test with users", "Decide"],
            "features": self._string_list(data.get("features")),
            "risks": self._string_list(data.get("risks")),
            "status": "planned",
            "created_at": self._now(),
        }
        self.storage.append(self.prototypes_file, prototype)
        self._log("innovation_prototype_created", f"Created prototype plan: {prototype['title']}.")
        return prototype

    def list_prototypes(self) -> list[dict]:
        return self.storage.read_list(self.prototypes_file)

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------
    def create_report(self, data: dict) -> dict:
        ideas = self.list_ideas()
        report = {
            "report_id": str(uuid4()),
            "title": self._clean(data.get("title"), 200) or "Innovation report",
            "research_count": len(self.list_research()),
            "competitor_count": len(self.list_competitors()),
            "trend_count": len(self.list_trends()),
            "top_ideas": [{"title": i.get("title"), "composite_score": i.get("composite_score")} for i in ideas[:5]],
            "experiment_count": len(self.list_experiments()),
            "prototype_count": len(self.list_prototypes()),
            "headline": (
                f"{len(self.list_research())} research item(s), {len(ideas)} idea(s), "
                f"{len(self.list_experiments())} experiment(s) planned."
            ),
            "created_at": self._now(),
        }
        self.storage.append(self.reports_file, report)
        self._log("innovation_report_created", f"Generated innovation report {report['report_id']}.")
        return report

    def list_reports(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.reports_file)[-limit:]))

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard(self) -> dict:
        ideas = self.list_ideas()
        return {
            "research_count": len(self.list_research()),
            "competitor_count": len(self.list_competitors()),
            "trend_count": len(self.list_trends()),
            "idea_count": len(ideas),
            "experiment_count": len(self.list_experiments()),
            "prototype_count": len(self.list_prototypes()),
            "report_count": len(self.storage.read_list(self.reports_file)),
            "top_ideas": ideas[:5],
            "note": "Local/manual research only — no web browsing or external scraping.",
        }
