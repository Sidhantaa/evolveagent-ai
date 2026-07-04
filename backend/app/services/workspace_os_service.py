from __future__ import annotations

from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.activity_timeline_service import ActivityTimelineService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Collections scanned per workspace for the "feature usage" breakdown (label → collection).
USAGE_COLLECTIONS = [
    ("goals", "goals.json"), ("memory", "workspace_memory.json"), ("agents", "custom_agents.json"),
    ("ideas", "innovation_ideas.json"), ("simulations", "simulation_worlds.json"),
    ("playbooks", "playbooks.json"), ("scheduled", "scheduled_tasks.json"), ("reports", "portfolio_reports.json"),
]


class WorkspaceOSService:
    """v70.0 Workspace Operating System 2.0 — make each workspace its own AI OS.

    A per-workspace, read-only overview: a workspace dashboard, a memory graph
    (memory nodes + knowledge-link edges), feature-usage counts, the workspace's
    agents, its reports, a recent timeline (via the v63 timeline), and a derived
    health score. Reads existing local state only, scoped to one workspace, and is
    governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService, timeline_service: ActivityTimelineService):
        self.storage = storage
        self.governance = governance_service
        self.timeline = timeline_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _in_ws(item: dict, workspace_id: str) -> bool:
        return isinstance(item, dict) and item.get("workspace_id") == workspace_id

    def _workspace(self, workspace_id: str) -> dict | None:
        for w in self.storage.read_list("workspaces.json"):
            if (w.get("workspace_id") or w.get("id")) == workspace_id:
                return w
        return None

    def _feature_usage(self, workspace_id: str) -> dict:
        usage = {}
        for label, collection in USAGE_COLLECTIONS:
            usage[label] = sum(1 for i in self.storage.read_list(collection) if self._in_ws(i, workspace_id))
        return usage

    def _memory_graph(self, workspace_id: str) -> dict:
        nodes = [m for m in self.storage.read_list("workspace_memory.json") if self._in_ws(m, workspace_id)]
        edges = [k for k in self.storage.read_list("knowledge_links.json") if self._in_ws(k, workspace_id)]
        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "sample_nodes": [self._title(n) for n in nodes[:6]],
        }

    @staticmethod
    def _title(item: dict) -> str:
        for key in ("title", "name", "key", "filename"):
            if isinstance(item.get(key), str) and item[key].strip():
                return item[key][:80]
        return "(untitled)"

    def _health_score(self, usage: dict, memory_graph: dict) -> dict:
        # Simple completeness-based score: rewards having goals, memory, and agents.
        score = 0
        score += min(usage.get("goals", 0), 5) * 8       # up to 40
        score += min(memory_graph["node_count"], 10) * 3  # up to 30
        score += min(usage.get("agents", 0), 3) * 10      # up to 30
        score = min(score, 100)
        status = "healthy" if score >= 70 else "developing" if score >= 30 else "sparse"
        return {"score": score, "status": status}

    def dashboard(self, workspace_id: str) -> dict:
        workspace = self._workspace(workspace_id)
        usage = self._feature_usage(workspace_id)
        memory_graph = self._memory_graph(workspace_id)
        agents = [self._title(a) for a in self.storage.read_list("custom_agents.json") if self._in_ws(a, workspace_id)]
        reports = [self._title(r) for r in self.storage.read_list("portfolio_reports.json") + self.storage.read_list("business_reports.json") if self._in_ws(r, workspace_id)]
        timeline = self.timeline.timeline(workspace_id=workspace_id, limit=12)
        health = self._health_score(usage, memory_graph)

        self.governance.log_event(
            GovernanceEvent(
                task_type="workspace_os",
                agent_name="Workspace OS",
                action_type="workspace_os_viewed",
                tool_used="WorkspaceOSService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=f"Rendered the Workspace OS dashboard for workspace {workspace_id}.",
            )
        )
        return {
            "workspace_id": workspace_id,
            "workspace_name": (workspace or {}).get("name", "Unknown workspace"),
            "exists": workspace is not None,
            "feature_usage": usage,
            "memory_graph": memory_graph,
            "agents": agents,
            "reports": reports[:8],
            "timeline": timeline["events"],
            "health": health,
            "note": "Read-only, workspace-scoped overview — aggregates existing local state; nothing is created or executed.",
        }

    def analytics_summary(self) -> dict:
        return {"workspace_os_total_workspaces": len(self.storage.read_list("workspaces.json"))}

    def summary(self) -> dict:
        workspaces = self.storage.read_list("workspaces.json")
        rows = []
        for w in workspaces[:50]:
            wid = w.get("workspace_id") or w.get("id")
            usage = self._feature_usage(wid)
            mg = self._memory_graph(wid)
            rows.append({"workspace_id": wid, "name": w.get("name"), "health": self._health_score(usage, mg)})
        return {"total_workspaces": len(workspaces), "workspaces": rows, "note": "Per-workspace health snapshot; read-only."}
