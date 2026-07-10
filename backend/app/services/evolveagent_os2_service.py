from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.health_monitor_service import HealthMonitorService
from app.services.operating_layer_v2_service import OperatingLayerV2Service
from app.services.storage_service import StorageService

DISCLAIMER = (
    "This is not AGI. It is a governed orchestration layer across existing agents, "
    "workflows, tools, memory, simulations, and dashboards."
)

# Unified command-center index: domain -> systems (label, API prefix, representative collection).
SYSTEM_INDEX = [
    ("Core", [
        ("Master Agent + run", "/api/run", "governance_log.json"),
        ("Workspace memory", "/api/memory", "workspace_memory.json"),
        ("Tools & plugins", "/api/tools", "tool_executions.json"),
        ("Governance", "/api/governance", "governance_log.json"),
    ]),
    ("Project & Portfolio", [
        ("Project manager", "/api/project-manager", "goals.json"),
        ("Portfolio", "/api/portfolio", "task_graphs.json"),
        ("Self-healing", "/api/self-healing", "self_healing_checks.json"),
    ]),
    ("Business", [
        ("Business operator", "/api/business-operator", "business_workflows.json"),
        ("Executive board", "/api/executive-board", "executive_board_sessions.json"),
        ("Compliance", "/api/compliance", "sensitive_data_findings.json"),
    ]),
    ("Personal & Org", [
        # v200: "chief_of_staff_items.json" was never a real file this service
        # wrote to (ChiefOfStaffService actually uses chief_daily_plans.json,
        # chief_weekly_plans.json, chief_followups.json,
        # chief_priority_scores.json) — this entry has shown active=false
        # unconditionally since it was added, regardless of real usage.
        ("Chief of staff", "/api/chief-of-staff", "chief_daily_plans.json"),
        ("Life OS", "/api/life-os", "life_tasks.json"),
        ("Organization OS", "/api/organization-os", "organizations.json"),
        ("Workspace templates", "/api/workspace-templates", "workspace_templates.json"),
        ("Workspaces", "/api/workspaces", "workspaces.json"),
    ]),
    ("Research & Simulation", [
        ("Innovation lab", "/api/innovation-lab", "innovation_ideas.json"),
        ("Simulation world", "/api/simulation-world", "simulation_worlds.json"),
        ("Local retrieval", "/api/retrieval", "retrieval_documents.json"),
        ("Evaluation harness", "/api/eval-harness", "eval_suites.json"),
    ]),
    ("MCP Arc", [
        ("Connector hub", "/api/mcp", "mcp_connectors.json"),
        ("Execution + read-only", "/api/mcp/executions", "mcp_execution_requests.json"),
        ("Policy engine", "/api/mcp/policies", "mcp_policies.json"),
        ("Secret registry", "/api/mcp/secrets", "mcp_secret_refs.json"),
        ("Audit & replay", "/api/mcp/audit", "mcp_replay_records.json"),
    ]),
    ("Ops & Observability", [
        ("Approvals center", "/api/approvals-center", "business_approval_items.json"),
        ("Health monitor", "/api/health-monitor", "health_snapshots.json"),
        ("Usage ledger", "/api/usage-ledger", "usage_ledger_entries.json"),
        ("Notifications", "/api/notifications", "notifications.json"),
        ("Scheduled tasks", "/api/scheduled-tasks", "scheduled_tasks.json"),
        ("Data export", "/api/data-export", "data_export_log.json"),
        ("Playbooks", "/api/playbooks", "playbooks.json"),
    ]),
    # v200: v100-v190 were built after this command center's last update and
    # were completely absent from it — an "OS 2.0" capstone view that didn't
    # know about a third of the platform. Real collections only, same
    # active-if-any-records heuristic as every domain above.
    ("Real Foundation (v100)", [
        ("Memory v2 (semantic recall)", "/api/memory-v2", "memory_v2_items.json"),
        ("Agent Registry", "/api/agent-registry", "custom_agents.json"),
        ("Agent governance", "/api/governance/risk/agents", "agent_governance_policies.json"),
    ]),
    ("Workflow Automation (v120)", [
        ("Durable workflows", "/api/durable-workflows", "durable_workflow_runs.json"),
        ("Event system", "/api/events", "system_events.json"),
        ("Job queue", "/api/agent-jobs", "agent_jobs.json"),
    ]),
    ("Autonomous Software Team (v150)", [
        # No dedicated local collection (a real commit/push/PR leaves no trace
        # in this app's own storage — it lands in the target git repo /
        # GitHub) — reuses governance_log.json, same imprecise-but-consistent
        # convention already used by "Master Agent + run" and "Governance"
        # above (multiple domains already share that same collection).
        ("Code writer + GitHub connector", "/api/code-writer", "governance_log.json"),
    ]),
    ("Agent Marketplace (v160)", [
        ("Marketplace hub", "/api/marketplace-hub", "marketplace_hub_listings.json"),
    ]),
    ("Multimodal AI OS (v170)", [
        ("Multimodal agent", "/api/multimodal", "multimodal_analyses.json"),
    ]),
    ("Enterprise AI OS (v190)", [
        ("Compliance audit packages", "/api/compliance/audit-packages", "audit_packages.json"),
    ]),
]

SAFETY_BOUNDARIES = [
    "No unrestricted shell execution.",
    "No destructive autonomous file operations.",
    "No real external sending, payments, or device/hardware control.",
    "No production auth; organization records are local only.",
    "No microphone recording or wake-word listening.",
    "No base-model self-training; only orchestration self-optimizes.",
    "MCP execution is mock by default; the only real path is opt-in, sandboxed, read-only.",
    "Risky actions require human approval and are governance-logged.",
]


class EvolveAgentOS2Service:
    """v200.0 EvolveAgent OS — Full EvolveAgent OS (capstone command center).

    The definitive unified command center: a navigable index of every major
    system across v1-v199, a platform scorecard (reusing the v55 Operating
    Layer 2.0 scorecard + v49 health), milestone stats, and a final governed
    report. It reads existing local state only, is explicitly NOT AGI, and
    takes no action beyond persisting a governance-logged snapshot/report.
    The v40/v55 layers are left untouched (distinct ``/api/os2`` prefix).

    v200: SYSTEM_INDEX previously stopped at v59 — everything built in
    v100-v190 this session (Real Foundation, Workflow Automation, Workspace
    Brain, Autonomous Software Team, Agent Marketplace, Multimodal AI OS,
    Personal Chief of Staff, Enterprise AI OS) was invisible to this
    "unified" view. Also fixed a latent bug found in the process: the
    pre-existing "Chief of staff" entry pointed at a filename
    (chief_of_staff_items.json) that ChiefOfStaffService never actually
    wrote to, so it showed inactive unconditionally regardless of real usage.
    """

    snapshots_file = "os2_snapshots.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, ol2_service: OperatingLayerV2Service, health_service: HealthMonitorService):
        self.storage = storage
        self.governance = governance_service
        self.ol2 = ol2_service
        self.health = health_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="evolveagent_os2",
                agent_name="EvolveAgent OS 2.0",
                action_type=action_type,
                tool_used="EvolveAgentOS2Service",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=4,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Command center index
    # ------------------------------------------------------------------
    def command_center(self) -> dict:
        domains = []
        active_total = 0
        system_total = 0
        for domain, systems in SYSTEM_INDEX:
            entries = []
            for label, route, collection in systems:
                count = len(self.storage.read_list(collection))
                active = count > 0
                system_total += 1
                active_total += 1 if active else 0
                entries.append({"label": label, "route": route, "active": active, "record_count": count})
            domains.append({"domain": domain, "systems": entries, "active_count": sum(1 for e in entries if e["active"]), "system_count": len(entries)})
        return {
            "version": "v200.0",
            "domains": domains,
            "active_systems": active_total,
            "total_systems": system_total,
            "coverage_pct": round((active_total / system_total) * 100) if system_total else 0,
            "disclaimer": DISCLAIMER,
        }

    # ------------------------------------------------------------------
    # Platform stats + report
    # ------------------------------------------------------------------
    def _stats(self) -> dict:
        return {
            "implementation_versions": 200,
            "governance_events": len(self.storage.read_list("governance_log.json")),
            "workspaces": len(self.storage.read_list("workspaces.json")),
        }

    def dashboard(self) -> dict:
        cc = self.command_center()
        scorecard = self.ol2.scorecard()
        latest = self.list_snapshots(limit=1)
        return {
            "version": "v200.0",
            "title": "EvolveAgent OS 2.0 — Command Center",
            "command_center": cc,
            "scorecard": scorecard,
            "health": {"status": self.health.dashboard().get("status"), "score": self.health.dashboard().get("health_score")},
            "stats": self._stats(),
            "safety_boundaries": SAFETY_BOUNDARIES,
            "latest_snapshot": latest[0] if latest else None,
            "disclaimer": DISCLAIMER,
        }

    def create_snapshot(self) -> dict:
        cc = self.command_center()
        scorecard = self.ol2.scorecard()
        snapshot = {
            "snapshot_id": str(uuid4()),
            "active_systems": cc["active_systems"],
            "total_systems": cc["total_systems"],
            "coverage_pct": cc["coverage_pct"],
            "overall_score": scorecard["overall_score"],
            "overall_grade": scorecard["overall_grade"],
            "created_at": self._now(),
        }
        self.storage.append(self.snapshots_file, snapshot)
        self._log("os2_snapshot_created", f"OS 2.0 snapshot — grade {snapshot['overall_grade']}, {snapshot['active_systems']}/{snapshot['total_systems']} systems active.")
        return snapshot

    def list_snapshots(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.snapshots_file)[-limit:]))

    def create_report(self) -> dict:
        cc = self.command_center()
        scorecard = self.ol2.scorecard()
        report = {
            "report_id": str(uuid4()),
            "title": "EvolveAgent OS 2.0 — Final Platform Report",
            "version": "v200.0",
            "overall_grade": scorecard["overall_grade"],
            "overall_score": scorecard["overall_score"],
            "active_systems": cc["active_systems"],
            "total_systems": cc["total_systems"],
            "coverage_pct": cc["coverage_pct"],
            "stats": self._stats(),
            "safety_boundaries": SAFETY_BOUNDARIES,
            "headline": (
                f"EvolveAgent OS 2.0 — grade {scorecard['overall_grade']} ({scorecard['overall_score']}/100) across "
                f"{cc['active_systems']}/{cc['total_systems']} systems and 200 implementation versions."
            ),
            "disclaimer": DISCLAIMER,
            "created_at": self._now(),
        }
        self.storage.append(self.snapshots_file, {**report, "snapshot_id": report["report_id"], "type": "report"})
        self._log("os2_report_created", "Generated the EvolveAgent OS 2.0 final platform report.")
        return report

    def analytics_summary(self) -> dict:
        cc = self.command_center()
        return {
            "os2_active_systems": cc["active_systems"],
            "os2_total_systems": cc["total_systems"],
            "os2_coverage_pct": cc["coverage_pct"],
        }
