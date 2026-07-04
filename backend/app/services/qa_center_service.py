from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.feature_registry_service import FeatureRegistryService
from app.services.governance_service import GovernanceService
from app.services.health_monitor_service import HealthMonitorService
from app.services.storage_service import StorageService

# Standard manual QA checklist (advisory).
QA_CHECKLIST = [
    "Backend test suite passes locally (pytest -q).",
    "Frontend build succeeds (npm run build).",
    "Simple Mode loads cleanly on a fresh workspace.",
    "Developer Mode panels open without errors.",
    "Risky actions are held for approval (not auto-executed).",
    "No secret values appear in any response, log, or panel.",
]


class QACenterService:
    """v88.0 Quality Assurance Center — make testing/verification first-class.

    Aggregates quality signals into one view: a **feature verification matrix** (from the
    v65 registry, with recorded QA status per feature), a **manual QA checklist**, a
    **failed-feature tracker**, a **regression dashboard** (recent QA fails), and a
    **release-readiness score** (feature coverage + demo-safe ratio + QA pass ratio +
    governance-health). QA results are recorded locally (additive). It does not run
    tests itself (no shell) — CI/local runs report status; this centralizes it.
    Governance-logged.
    """

    results_file = "qa_results.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService,
                 feature_registry: FeatureRegistryService, health_service: HealthMonitorService):
        self.storage = storage
        self.governance = governance_service
        self.features = feature_registry
        self.health = health_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _latest_by_feature(self) -> dict[str, dict]:
        latest: dict[str, dict] = {}
        for r in self.storage.read_list(self.results_file):
            if isinstance(r, dict) and r.get("feature_key"):
                latest[r["feature_key"]] = r  # later entries overwrite; list is append-order
        return latest

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="qa_center",
                agent_name="QA Center",
                action_type=action_type,
                tool_used="QACenterService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def record(self, feature_key: str, status: str, note: str = "") -> dict:
        status = status if status in ("pass", "fail", "skip") else "skip"
        record = {"result_id": str(uuid4()), "feature_key": feature_key[:80], "status": status,
                  "note": (note or "")[:500], "at": self._now()}
        self.storage.append(self.results_file, record)
        self._log("qa_recorded", f"Recorded QA result for '{feature_key}': {status}.")
        return record

    def verification_matrix(self) -> dict:
        features = self.features.list_features()["features"]
        latest = self._latest_by_feature()
        rows = []
        for feature in features:
            result = latest.get(feature["key"])
            rows.append({
                "key": feature["key"], "name": feature["name"], "route": feature["route"],
                "demo_safe": "demo_safe" in feature["status"],
                "qa_status": result["status"] if result else "unverified",
                "last_checked": result["at"] if result else None,
            })
        return {"matrix": rows, "count": len(rows)}

    def dashboard(self) -> dict:
        matrix = self.verification_matrix()["matrix"]
        failed = [r for r in matrix if r["qa_status"] == "fail"]
        passed = [r for r in matrix if r["qa_status"] == "pass"]
        verified = len(passed) + len(failed)
        demo_safe = sum(1 for r in matrix if r["demo_safe"])

        # Release readiness score.
        coverage = (verified / len(matrix)) if matrix else 0
        pass_ratio = (len(passed) / verified) if verified else 0
        demo_ratio = (demo_safe / len(matrix)) if matrix else 0
        health = self.health.dashboard()
        health_score = (health.get("health_score", 100) or 100) / 100
        readiness = round((coverage * 25 + pass_ratio * 35 + demo_ratio * 20 + health_score * 20))

        self._log("qa_dashboard_viewed", "Rendered the QA Center dashboard.")
        return {
            "release_readiness_score": readiness,
            "readiness_status": "ready" if readiness >= 80 else "getting there" if readiness >= 55 else "not ready",
            "verification": {"total": len(matrix), "verified": verified, "passed": len(passed), "failed": len(failed),
                             "unverified": len(matrix) - verified, "demo_safe": demo_safe},
            "failed_feature_tracker": failed[:20],
            "regression_dashboard": {"recent_fails": [r for r in list(reversed(self.storage.read_list(self.results_file)))[:10] if r.get("status") == "fail"]},
            "qa_checklist": QA_CHECKLIST,
            "health_status": health.get("status"),
            "note": "Read-only QA aggregation; it does not run tests itself (no shell) — CI/local runs report status.",
        }

    def analytics_summary(self) -> dict:
        results = self.storage.read_list(self.results_file)
        return {"qa_results": len(results), "qa_failed": sum(1 for r in results if r.get("status") == "fail")}

    def summary(self) -> dict:
        dash = self.dashboard()
        return {
            "release_readiness_score": dash["release_readiness_score"],
            "readiness_status": dash["readiness_status"],
            "verified": dash["verification"]["verified"],
            "failed": dash["verification"]["failed"],
            "note": dash["note"],
        }
