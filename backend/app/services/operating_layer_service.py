from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

DISCLAIMER = (
    "This is not AGI. It is a governed orchestration layer across existing agents, "
    "workflows, tools, memory, simulations, and dashboards."
)

# Capability map across v15-v39 (group -> (label, a representative data collection)).
CAPABILITY_MAP = [
    ("Platform", "EvolveAgent OS / installer / plugins / SLA", "governance_log.json"),
    ("Organization", "Departments, marketplace, team manager, org OS", "agent_departments.json"),
    ("Business", "Business operator, advanced ops, simulator", "business_leads.json"),
    ("Personal", "Chief of Staff, Life OS", "life_tasks.json"),
    ("Agents", "Agent network, custom agents, executive board", "agent_network_contracts.json"),
    ("Automation", "Self-healing, device/universal operators", "self_healing_checks.json"),
    ("Intelligence", "Multi-modal, evaluation, training lab", "training_datasets.json"),
    ("Research", "Innovation lab, simulation world", "innovation_ideas.json"),
    ("Compliance", "Compliance intelligence, governance", "sensitive_data_findings.json"),
    ("Companion", "Hardware companion readiness", "hardware_devices.json"),
]

# Capabilities that are intentionally blocked / boundaries that always hold.
SAFETY_BOUNDARIES = [
    "No unrestricted shell execution.",
    "No real external sending, payments, or device/hardware control.",
    "No production auth; organization records are local only.",
    "No microphone recording or wake-word listening.",
    "No base-model self-training; only orchestration self-optimizes.",
    "Risky actions require human approval and are governance-logged.",
]


class OperatingLayerService:
    """v40.0 EvolveAgent AGI-Style Operating Layer.

    A final governed orchestration dashboard that summarizes the platform's
    capability map across v15-v39 (personal, project, business, agent,
    simulation, organization, and companion systems), produces readiness
    snapshots and cross-system recommendations, and surfaces safety boundaries.
    It is explicitly NOT AGI — see the disclaimer. Stateful actions are
    governance-logged.
    """

    snapshots_file = "operating_layer_snapshots.json"
    capabilities_file = "operating_layer_capabilities.json"
    recommendations_file = "operating_layer_recommendations.json"
    audit_file = "operating_layer_audit.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _audit(self, event: str, ref_id: str, detail: str) -> None:
        self.storage.append(
            self.audit_file,
            {"audit_id": str(uuid4()), "event": event, "ref_id": ref_id, "detail": detail, "created_at": self._now()},
        )

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="operating_layer",
                agent_name="EvolveAgent Operating Layer",
                action_type=action_type,
                tool_used="OperatingLayerService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Capability map
    # ------------------------------------------------------------------
    def capabilities(self) -> dict:
        groups = []
        for group, label, collection in CAPABILITY_MAP:
            record_count = len(self.storage.read_list(collection))
            groups.append(
                {
                    "group": group,
                    "label": label,
                    "active": record_count > 0,
                    "record_count": record_count,
                }
            )
        return {
            "capability_groups": groups,
            "active_group_count": sum(1 for g in groups if g["active"]),
            "total_group_count": len(groups),
            "disclaimer": DISCLAIMER,
        }

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------
    def create_snapshot(self) -> dict:
        capabilities = self.capabilities()
        governance = self.storage.read_list("governance_log.json")
        readiness = round((capabilities["active_group_count"] / capabilities["total_group_count"]) * 100) if capabilities["total_group_count"] else 0
        snapshot = {
            "snapshot_id": str(uuid4()),
            "readiness_score": readiness,
            "active_capability_groups": capabilities["active_group_count"],
            "total_capability_groups": capabilities["total_group_count"],
            "governance_event_count": len(governance),
            "blocked_action_count": sum(1 for e in governance if e.get("blocked")),
            "safety_boundaries": SAFETY_BOUNDARIES,
            "disclaimer": DISCLAIMER,
            "created_at": self._now(),
        }
        self.storage.append(self.snapshots_file, snapshot)
        self._audit("snapshot_created", snapshot["snapshot_id"], f"Readiness {readiness}%.")
        self._log("operating_layer_snapshot_created", f"Generated operating-layer snapshot (readiness {readiness}%).")
        return snapshot

    def list_snapshots(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.snapshots_file)[-limit:]))

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------
    def create_recommendations(self) -> dict:
        capabilities = self.capabilities()
        inactive = [g["group"] for g in capabilities["capability_groups"] if not g["active"]]
        recs = []
        if inactive:
            recs.append(f"Seed data in inactive areas to activate: {', '.join(inactive[:5])}.")
        recs.append("Generate a daily plan (Chief of Staff / Life OS) to drive priorities.")
        recs.append("Run an executive board review before any high-impact decision.")
        recs.append("Keep risky actions behind approval — the layer orchestrates, it does not auto-execute.")
        record = {
            "recommendation_id": str(uuid4()),
            "recommendations": recs,
            "inactive_groups": inactive,
            "disclaimer": DISCLAIMER,
            "created_at": self._now(),
        }
        self.storage.append(self.recommendations_file, record)
        self._audit("recommendations_created", record["recommendation_id"], f"{len(recs)} cross-system recommendation(s).")
        self._log("operating_layer_recommendations_created", f"Generated {len(recs)} cross-system recommendation(s).")
        return record

    def list_recommendations(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.recommendations_file)[-limit:]))

    # ------------------------------------------------------------------
    # Final report
    # ------------------------------------------------------------------
    def create_report(self) -> dict:
        capabilities = self.capabilities()
        snapshot = self.create_snapshot()
        report = {
            "report_id": str(uuid4()),
            "title": "EvolveAgent Operating Layer report",
            "version": "v40.0",
            "readiness_score": snapshot["readiness_score"],
            "capability_groups": capabilities["capability_groups"],
            "active_capability_groups": capabilities["active_group_count"],
            "safety_boundaries": SAFETY_BOUNDARIES,
            "headline": (
                f"Governed orchestration across {capabilities['active_group_count']}/"
                f"{capabilities['total_group_count']} capability areas. Readiness {snapshot['readiness_score']}%."
            ),
            "disclaimer": DISCLAIMER,
            "created_at": self._now(),
        }
        # Reports are surfaced via snapshots list; persist under snapshots store with a type tag.
        self.storage.append(self.snapshots_file, {**report, "snapshot_id": report["report_id"], "type": "report"})
        self._audit("report_created", report["report_id"], "Generated final operating-layer report.")
        self._log("operating_layer_report_created", "Generated final operating-layer report.")
        return report

    # ------------------------------------------------------------------
    # Audit + dashboard
    # ------------------------------------------------------------------
    def audit_log(self, limit: int = 50) -> list[dict]:
        return list(reversed(self.storage.read_list(self.audit_file)[-limit:]))

    def dashboard(self) -> dict:
        capabilities = self.capabilities()
        latest = self.list_snapshots(limit=1)
        return {
            "version": "v40.0",
            "active_capability_groups": capabilities["active_group_count"],
            "total_capability_groups": capabilities["total_group_count"],
            "capability_groups": capabilities["capability_groups"],
            "latest_snapshot": latest[0] if latest else None,
            "safety_boundaries": SAFETY_BOUNDARIES,
            "snapshot_count": len(self.storage.read_list(self.snapshots_file)),
            "recommendation_count": len(self.storage.read_list(self.recommendations_file)),
            "disclaimer": DISCLAIMER,
        }
