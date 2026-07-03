from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.health_monitor_service import HealthMonitorService
from app.services.storage_service import StorageService

DISCLAIMER = (
    "This is not AGI. It is a governed orchestration layer across existing agents, "
    "workflows, tools, memory, simulations, and dashboards."
)

# Expanded capability map across v15-v53 (group -> (label, representative collection)).
CAPABILITY_MAP_V2 = [
    ("Platform", "EvolveAgent OS / installer / plugins", "governance_log.json"),
    ("Organization", "Departments, marketplace, org OS", "agent_departments.json"),
    ("Business", "Business operator, advanced ops, simulator", "business_leads.json"),
    ("Personal", "Chief of Staff, Life OS", "life_tasks.json"),
    ("Agents", "Agent network, custom agents, executive board", "agent_network_contracts.json"),
    ("Automation", "Self-healing, device/universal operators", "self_healing_checks.json"),
    ("Intelligence", "Multi-modal, evaluation, training lab", "training_datasets.json"),
    ("Research", "Innovation lab, simulation world", "innovation_ideas.json"),
    ("Compliance", "Compliance intelligence, governance", "sensitive_data_findings.json"),
    ("Companion", "Hardware companion readiness", "hardware_devices.json"),
    ("MCP Connectors", "Connector hub (v41)", "mcp_connectors.json"),
    ("MCP Execution", "Execution + read-only adapter (v42/43)", "mcp_execution_requests.json"),
    ("MCP Policy", "Policy engine (v45)", "mcp_policies.json"),
    ("Secret Registry", "Secret references (v47)", "mcp_secret_refs.json"),
    ("Health", "Health & readiness (v49)", "health_snapshots.json"),
    ("Usage", "Cost & usage ledger (v50)", "usage_ledger_entries.json"),
    ("Retrieval", "Local retrieval (v51)", "retrieval_documents.json"),
    ("Evaluation", "Eval harness 2.0 (v52)", "eval_suites.json"),
    ("Playbooks", "Playbook library (v53)", "playbooks.json"),
]

SAFETY_BOUNDARIES = [
    "No unrestricted shell execution.",
    "No real external sending, payments, or device/hardware control.",
    "No production auth; organization records are local only.",
    "No microphone recording or wake-word listening.",
    "No base-model self-training; only orchestration self-optimizes.",
    "MCP execution is mock by default; the only real path is opt-in, sandboxed, read-only.",
    "Risky actions require human approval and are governance-logged.",
]


class OperatingLayerV2Service:
    """v55.0 EvolveAgent Operating Layer 2.0.

    Refreshes the v40 capstone to cover the v41-v53 additions in an expanded
    capability map, and adds a platform-wide **readiness & governance scorecard**
    combining capability coverage, health, governance posture, and approvals
    backlog into graded dimensions and an overall score. It reads existing local
    state only — it is explicitly NOT AGI and takes no actions beyond persisting a
    governance-logged snapshot/report.
    """

    snapshots_file = "operating_layer_v2_snapshots.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, health_service: HealthMonitorService):
        self.storage = storage
        self.governance = governance_service
        self.health = health_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    # ------------------------------------------------------------------
    # Capability map
    # ------------------------------------------------------------------
    def capabilities(self) -> dict:
        groups = []
        for group, label, collection in CAPABILITY_MAP_V2:
            count = len(self.storage.read_list(collection))
            groups.append({"group": group, "label": label, "active": count > 0, "record_count": count})
        active = sum(1 for g in groups if g["active"])
        return {
            "capability_groups": groups,
            "active_group_count": active,
            "total_group_count": len(groups),
            "coverage_pct": round((active / len(groups)) * 100) if groups else 0,
            "disclaimer": DISCLAIMER,
        }

    # ------------------------------------------------------------------
    # Scorecard
    # ------------------------------------------------------------------
    @staticmethod
    def _grade(score: int) -> str:
        return "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"

    def scorecard(self) -> dict:
        caps = self.capabilities()
        coverage = caps["coverage_pct"]

        governance = self.storage.read_list("governance_log.json")
        blocked = sum(1 for e in governance if e.get("blocked"))
        blocked_ratio = (blocked / len(governance)) if governance else 0
        governance_score = round(max(0, 100 - blocked_ratio * 100))

        health_score = self.health.dashboard().get("health_score", 100)

        mcp_pending = sum(1 for r in self.storage.read_list("mcp_execution_requests.json") if r.get("status") == "pending_approval")
        biz_pending = sum(1 for a in self.storage.read_list("business_approval_items.json") if a.get("status") == "pending")
        backlog = mcp_pending + biz_pending
        approvals_score = 100 if backlog == 0 else 70 if backlog < 10 else 40

        dimensions = [
            {"name": "capability_coverage", "score": coverage, "grade": self._grade(coverage)},
            {"name": "governance", "score": governance_score, "grade": self._grade(governance_score)},
            {"name": "health", "score": health_score, "grade": self._grade(health_score)},
            {"name": "approvals_backlog", "score": approvals_score, "grade": self._grade(approvals_score)},
        ]
        overall = round(sum(d["score"] for d in dimensions) / len(dimensions))
        return {
            "overall_score": overall,
            "overall_grade": self._grade(overall),
            "dimensions": dimensions,
            "disclaimer": DISCLAIMER,
        }

    # ------------------------------------------------------------------
    # Snapshots + report + dashboard
    # ------------------------------------------------------------------
    def create_snapshot(self) -> dict:
        scorecard = self.scorecard()
        snapshot = {
            "snapshot_id": str(uuid4()),
            "overall_score": scorecard["overall_score"],
            "overall_grade": scorecard["overall_grade"],
            "dimensions": scorecard["dimensions"],
            "created_at": self._now(),
        }
        self.storage.append(self.snapshots_file, snapshot)
        self._log("operating_layer_v2_snapshot_created", f"Operating Layer 2.0 snapshot (score {snapshot['overall_score']}, grade {snapshot['overall_grade']}).")
        return snapshot

    def list_snapshots(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.snapshots_file)[-limit:]))

    def create_report(self) -> dict:
        caps = self.capabilities()
        scorecard = self.scorecard()
        report = {
            "report_id": str(uuid4()),
            "title": "EvolveAgent Operating Layer 2.0 report",
            "version": "v55.0",
            "overall_score": scorecard["overall_score"],
            "overall_grade": scorecard["overall_grade"],
            "dimensions": scorecard["dimensions"],
            "active_capability_groups": caps["active_group_count"],
            "total_capability_groups": caps["total_group_count"],
            "safety_boundaries": SAFETY_BOUNDARIES,
            "headline": f"Grade {scorecard['overall_grade']} ({scorecard['overall_score']}/100) across {caps['active_group_count']}/{caps['total_group_count']} capability areas.",
            "disclaimer": DISCLAIMER,
            "created_at": self._now(),
        }
        self.storage.append(self.snapshots_file, {**report, "snapshot_id": report["report_id"], "type": "report"})
        self._log("operating_layer_v2_report_created", "Generated Operating Layer 2.0 report.")
        return report

    def dashboard(self) -> dict:
        caps = self.capabilities()
        scorecard = self.scorecard()
        latest = self.list_snapshots(limit=1)
        return {
            "version": "v55.0",
            "overall_score": scorecard["overall_score"],
            "overall_grade": scorecard["overall_grade"],
            "dimensions": scorecard["dimensions"],
            "active_capability_groups": caps["active_group_count"],
            "total_capability_groups": caps["total_group_count"],
            "coverage_pct": caps["coverage_pct"],
            "capability_groups": caps["capability_groups"],
            "latest_snapshot": latest[0] if latest else None,
            "safety_boundaries": SAFETY_BOUNDARIES,
            "disclaimer": DISCLAIMER,
        }

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="operating_layer_v2",
                agent_name="EvolveAgent Operating Layer 2.0",
                action_type=action_type,
                tool_used="OperatingLayerV2Service",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=4,
                reason=reason,
            )
        )

    def analytics_summary(self) -> dict:
        sc = self.scorecard()
        return {
            "operating_layer_v2_score": sc["overall_score"],
            "operating_layer_v2_grade": sc["overall_grade"],
            "operating_layer_v2_coverage_pct": self.capabilities()["coverage_pct"],
        }
