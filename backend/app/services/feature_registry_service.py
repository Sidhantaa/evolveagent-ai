from __future__ import annotations

import re
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Status vocabulary:
#   active      — real local behavior, safe to use now
#   demo_safe   — deterministic/mock-safe, great for demos
#   mock        — planning/mock-first (no real external effect)
#   needs_config — requires an env key / opt-in flag to do real work
STATUS = {"active", "demo_safe", "mock", "needs_config"}

# Canonical registry of the platform's features. Each entry is discoverable and
# carries its owning service, primary route, category, and status tags.
FEATURES = [
    {"key": "master-agent", "name": "Master Agent (Command Router)", "version": "v60.1/v61", "category": "Core", "service": "MasterAgentService", "route": "/api/master-agent", "status": ["active", "demo_safe"]},
    {"key": "global-search", "name": "Global Search", "version": "v62", "category": "Core", "service": "GlobalSearchService", "route": "/api/search", "status": ["active", "demo_safe"]},
    {"key": "activity-timeline", "name": "Unified Activity Timeline", "version": "v63", "category": "Core", "service": "ActivityTimelineService", "route": "/api/activity", "status": ["active", "demo_safe"]},
    {"key": "dashboard-home", "name": "Dashboard Home 2.0", "version": "v64", "category": "Core", "service": "DashboardHomeService", "route": "/api/home", "status": ["active", "demo_safe"]},
    {"key": "run", "name": "Master Orchestrator Run", "version": "v1+", "category": "Core", "service": "KernelService", "route": "/api/run", "status": ["active", "demo_safe"]},
    {"key": "workspace-memory", "name": "Workspace Memory", "version": "v3+", "category": "Core", "service": "WorkspaceMemoryService", "route": "/api/memory", "status": ["active"]},
    {"key": "governance", "name": "Governance Log", "version": "v1+", "category": "Governance", "service": "GovernanceService", "route": "/api/governance", "status": ["active"]},
    {"key": "goals", "name": "Mission Control Goals", "version": "v6+", "category": "Project", "service": "GoalService", "route": "/api/goals", "status": ["active"]},
    {"key": "portfolio", "name": "Portfolio / Project Manager", "version": "v33+", "category": "Project", "service": "ProjectManagerService", "route": "/api/project-manager", "status": ["active", "demo_safe"]},
    {"key": "custom-agents", "name": "Custom Agent Builder", "version": "v8+", "category": "Agents", "service": "CustomAgentService", "route": "/api/custom-agents", "status": ["active"]},
    {"key": "eval-harness", "name": "Evaluation Harness 2.0", "version": "v52", "category": "Quality", "service": "EvalHarnessService", "route": "/api/eval-harness", "status": ["active", "demo_safe", "mock"]},
    {"key": "business-operator", "name": "Business Operator", "version": "v34+", "category": "Business", "service": "BusinessOperatorService", "route": "/api/business-operator", "status": ["mock", "demo_safe"]},
    {"key": "compliance", "name": "Compliance Intelligence", "version": "v35", "category": "Compliance", "service": "ComplianceService", "route": "/api/compliance", "status": ["active", "demo_safe"]},
    {"key": "innovation-lab", "name": "Innovation Lab", "version": "v36", "category": "Research", "service": "InnovationLabService", "route": "/api/innovation-lab", "status": ["mock", "demo_safe"]},
    {"key": "simulation-world", "name": "Simulation World", "version": "v37", "category": "Research", "service": "SimulationWorldService", "route": "/api/simulation-world", "status": ["mock", "demo_safe"]},
    {"key": "life-os", "name": "Life OS", "version": "v-life", "category": "Personal", "service": "LifeOSService", "route": "/api/life-os", "status": ["active"]},
    {"key": "organization-os", "name": "Organization OS", "version": "v38", "category": "Personal", "service": "OrganizationOSService", "route": "/api/organization-os", "status": ["active", "needs_config"]},
    {"key": "retrieval", "name": "Local Retrieval Layer", "version": "v51", "category": "Research", "service": "LocalRetrievalService", "route": "/api/retrieval", "status": ["active", "demo_safe"]},
    {"key": "mcp-hub", "name": "MCP Connector Hub", "version": "v41", "category": "MCP", "service": "MCPConnectorService", "route": "/api/mcp", "status": ["active", "needs_config"]},
    {"key": "mcp-execution", "name": "MCP Execution Adapter", "version": "v42/v43", "category": "MCP", "service": "MCPExecutionService", "route": "/api/mcp/executions", "status": ["mock", "needs_config"]},
    {"key": "mcp-policies", "name": "MCP Policy Engine", "version": "v45", "category": "MCP", "service": "MCPPolicyService", "route": "/api/mcp/policies", "status": ["active"]},
    {"key": "mcp-secrets", "name": "Secret Reference Registry", "version": "v47", "category": "MCP", "service": "MCPSecretRegistryService", "route": "/api/mcp/secrets", "status": ["active", "needs_config"]},
    {"key": "mcp-audit", "name": "MCP Audit & Replay", "version": "v46", "category": "MCP", "service": "MCPAuditService", "route": "/api/mcp/audit", "status": ["active", "demo_safe"]},
    {"key": "mcp-suggest", "name": "Task-aware MCP Suggestion", "version": "v57.x", "category": "MCP", "service": "MCPSuggestionService", "route": "/api/mcp/suggest", "status": ["active", "demo_safe"]},
    {"key": "approvals-center", "name": "Unified Approvals Center", "version": "v48", "category": "Ops", "service": "UnifiedApprovalsService", "route": "/api/approvals-center", "status": ["active"]},
    {"key": "health-monitor", "name": "Health & Readiness Monitor", "version": "v49", "category": "Ops", "service": "HealthMonitorService", "route": "/api/health-monitor", "status": ["active", "demo_safe"]},
    {"key": "usage-ledger", "name": "Cost & Usage Ledger", "version": "v50", "category": "Ops", "service": "UsageLedgerService", "route": "/api/usage-ledger", "status": ["mock", "demo_safe"]},
    {"key": "notifications", "name": "Notifications & Alerts Center", "version": "v56", "category": "Ops", "service": "NotificationsCenterService", "route": "/api/notifications", "status": ["active"]},
    {"key": "playbooks", "name": "Playbook Library", "version": "v53", "category": "Automation", "service": "PlaybookLibraryService", "route": "/api/playbooks", "status": ["mock", "demo_safe"]},
    {"key": "scheduled-tasks", "name": "Scheduled Tasks", "version": "v58", "category": "Automation", "service": "ScheduledTasksService", "route": "/api/scheduled-tasks", "status": ["mock", "demo_safe"]},
    {"key": "workspace-templates", "name": "Workspace Templates & Cloning", "version": "v57", "category": "Automation", "service": "WorkspaceTemplatesService", "route": "/api/workspace-templates", "status": ["active"]},
    {"key": "data-export", "name": "Data Export & Backup", "version": "v59", "category": "Data", "service": "DataExportService", "route": "/api/data-export", "status": ["active", "demo_safe"]},
    {"key": "operating-layer-2", "name": "Operating Layer 2.0", "version": "v55", "category": "Ops", "service": "OperatingLayerV2Service", "route": "/api/operating-layer-2", "status": ["active", "demo_safe"]},
    {"key": "os2", "name": "EvolveAgent OS 2.0 (capstone)", "version": "v60", "category": "Core", "service": "EvolveAgentOS2Service", "route": "/api/os2", "status": ["active", "demo_safe"]},
]

CATEGORIES = sorted({f["category"] for f in FEATURES})


class FeatureRegistryService:
    """v65.0 Feature Registry + Capability Map 3.0 — make all 60+ versions discoverable.

    A canonical, searchable registry of every major feature: its owning service,
    primary API route, category, and status tags (active / demo-safe / mock /
    needs-config). Supports UI feature search, status/category filters, a
    route → feature map (Developer-Mode route map), and a "try this feature"
    descriptor that hands back the route to open. Read-only; governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def list_features(self, query: str | None = None, status: str | None = None, category: str | None = None) -> dict:
        terms = [t for t in re.sub(r"[^a-z0-9]+", " ", (query or "").lower().strip()).split() if t]
        matches = []
        for feature in FEATURES:
            if status and status not in feature["status"]:
                continue
            if category and feature["category"] != category:
                continue
            if terms:
                blob = f"{feature['name']} {feature['key']} {feature['category']} {feature['service']} {feature['route']}".lower()
                if not all(term in blob for term in terms):
                    continue
            matches.append(feature)
        self.governance.log_event(
            GovernanceEvent(
                task_type="feature_registry",
                agent_name="Feature Registry",
                action_type="feature_registry_listed",
                tool_used="FeatureRegistryService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=f"Listed {len(matches)} feature(s) from the registry.",
            )
        )
        return {
            "features": matches,
            "feature_count": len(matches),
            "total_features": len(FEATURES),
            "categories": CATEGORIES,
            "statuses": sorted(STATUS),
            "note": "Canonical feature registry — read-only discovery across the platform.",
        }

    def route_map(self) -> dict:
        return {
            "route_map": [{"route": f["route"], "feature": f["name"], "service": f["service"], "status": f["status"]} for f in FEATURES],
            "count": len(FEATURES),
        }

    def try_feature(self, key: str) -> dict:
        feature = next((f for f in FEATURES if f["key"] == key), None)
        if feature is None:
            raise ValueError("Feature not found")
        self.governance.log_event(
            GovernanceEvent(
                task_type="feature_registry",
                agent_name="Feature Registry",
                action_type="feature_try_launched",
                tool_used="FeatureRegistryService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=f"Prepared a 'try this feature' launch for {feature['name']}.",
            )
        )
        return {
            "feature": feature,
            "open_route": feature["route"],
            "launch_note": f"Open {feature['route']} to try {feature['name']}." + (
                " Requires configuration (an env key / opt-in flag)." if "needs_config" in feature["status"] else ""
            ),
        }

    def analytics_summary(self) -> dict:
        by_status = {s: sum(1 for f in FEATURES if s in f["status"]) for s in sorted(STATUS)}
        return {
            "registry_total_features": len(FEATURES),
            "registry_demo_safe_features": by_status["demo_safe"],
        }

    def summary(self) -> dict:
        by_category = {c: sum(1 for f in FEATURES if f["category"] == c) for c in CATEGORIES}
        by_status = {s: sum(1 for f in FEATURES if s in f["status"]) for s in sorted(STATUS)}
        return {
            "total_features": len(FEATURES),
            "by_category": by_category,
            "by_status": by_status,
            "categories": CATEGORIES,
            "note": "Feature Registry + Capability Map 3.0 — canonical, read-only discovery.",
        }
