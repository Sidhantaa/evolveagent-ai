from __future__ import annotations

from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.export_center_service import ExportCenterService
from app.services.feature_registry_service import FeatureRegistryService
from app.services.governance_service import GovernanceService
from app.services.qa_center_service import QACenterService
from app.services.storage_service import StorageService

POSITIONING = {
    "name": "EvolveAgent AI",
    "tagline": "A local-first, governed multi-agent AI operating system.",
    "one_liner": "One AI you talk to that routes across 90 versions of governed capabilities — planning-first, "
                 "approval-gated, and fully inspectable. Not AGI; a governed orchestration layer.",
    "pillars": [
        "Local-first & private — all state on your machine, JSON storage.",
        "Governed & safe — every action logged; risky actions held for approval.",
        "One surface — the Master Agent routes across every subsystem.",
        "Inspectable — Developer Mode exposes every layer.",
        "Works with or without API keys — mock fallback for clean demos.",
    ],
    "disclaimer": "This is not AGI. It is a governed orchestration layer across existing agents, workflows, tools, memory, and dashboards.",
}


class ProductLaunchService:
    """v90.0 EvolveAgent Product Launch Console (capstone) — make the project launch-ready.

    The finale of the v61–v90 arc: a single read-only **launch dashboard** unifying
    **product positioning**, a **feature matrix** (from the v65 registry, grouped by
    category + status), **demo-mode** pointers, one-click links to **portfolio / resume /
    case-study exports** (v66/v85), and a **final readiness score** (QA release-readiness +
    feature demo-safe coverage). It reads existing state only and takes no action beyond a
    governance-logged view. Explicitly **not AGI**.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService,
                 feature_registry: FeatureRegistryService, qa_center: QACenterService, export_center: ExportCenterService):
        self.storage = storage
        self.governance = governance_service
        self.features = feature_registry
        self.qa = qa_center
        self.export = export_center

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="product_launch",
                agent_name="Product Launch Console",
                action_type=action_type,
                tool_used="ProductLaunchService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def _feature_matrix(self) -> dict:
        summary = self.features.summary()
        return {
            "total_features": summary["total_features"],
            "by_category": summary["by_category"],
            "by_status": summary["by_status"],
        }

    def _final_readiness(self, qa_readiness: int, matrix: dict) -> dict:
        total = matrix["total_features"] or 1
        demo_safe_ratio = matrix["by_status"].get("demo_safe", 0) / total
        score = round(qa_readiness * 0.6 + demo_safe_ratio * 100 * 0.4)
        return {"score": score, "status": "launch-ready" if score >= 80 else "polishing" if score >= 55 else "in progress"}

    def dashboard(self) -> dict:
        matrix = self._feature_matrix()
        qa = self.qa.dashboard()
        readiness = self._final_readiness(qa["release_readiness_score"], matrix)
        self._log("launch_console_viewed", f"Rendered the Product Launch Console (readiness {readiness['score']}).")
        return {
            "version": "v90.0",
            "positioning": POSITIONING,
            "feature_matrix": matrix,
            "milestones": {"implementation_versions": 90, "governance_events": len(self.storage.read_list("governance_log.json"))},
            "demo_mode": {"route": "/api/demo", "hint": "Seed a demo-safe workspace, then follow the one-click demo script."},
            "exports": {
                "portfolio_case_study": "/api/export-center/case-study",
                "resume_bullets": "/api/demo/resume-bullets",
                "package": "/api/export-center/package",
            },
            "qa": {"release_readiness_score": qa["release_readiness_score"], "readiness_status": qa["readiness_status"]},
            "final_readiness": readiness,
            "disclaimer": POSITIONING["disclaimer"],
            "note": "Read-only launch overview — aggregates existing state; nothing is created or executed.",
        }

    def launch_report(self) -> dict:
        dash = self.dashboard()
        lines = [
            f"# {POSITIONING['name']} — Launch Report (v90.0)", "",
            f"_{POSITIONING['tagline']}_", "",
            f"**Final readiness: {dash['final_readiness']['score']}/100 ({dash['final_readiness']['status']})**", "",
            "## Positioning", POSITIONING["one_liner"], "",
            "## Pillars", *[f"- {p}" for p in POSITIONING["pillars"]], "",
            "## Scale",
            f"- {dash['milestones']['implementation_versions']} implementation versions",
            f"- {dash['feature_matrix']['total_features']} registered features across {len(dash['feature_matrix']['by_category'])} categories", "",
            "## Disclaimer", POSITIONING["disclaimer"],
        ]
        self._log("launch_report_generated", "Generated the final launch report.")
        return {"format": "markdown", "content": "\n".join(lines)}

    def analytics_summary(self) -> dict:
        matrix = self._feature_matrix()
        readiness = self._final_readiness(self.qa.dashboard()["release_readiness_score"], matrix)
        return {"launch_final_readiness": readiness["score"], "launch_implementation_versions": 90}

    def summary(self) -> dict:
        dash = self.dashboard()
        return {
            "version": "v90.0",
            "final_readiness": dash["final_readiness"],
            "total_features": dash["feature_matrix"]["total_features"],
            "disclaimer": POSITIONING["disclaimer"],
        }
