"""Agent Registry (v100) — one unified view over the fragmented agent stores.

The app grew three overlapping agent concepts:

* **Agent Studio** profiles (``agent_profiles.json``) — user-built agents
* **Custom Agents** (``custom_agents.json``) — template-based task agents
* **Departments** (``agent_departments.json``) — manager/worker/reviewer rosters

This service is a **read-only adapter** that normalizes all of them into one
registry entry shape, so EVA / the frontend / future orchestration can discover
every agent in the system through a single API. It does NOT move or rewrite any
data — each source store stays owned by its existing service (writes continue to
go through Agent Studio / Custom Agent Builder / Departments). Governance-logged.
"""

from __future__ import annotations

from typing import Any

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

SOURCES = ("agent_studio", "custom_agents", "department")


class AgentRegistryService:
    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(GovernanceEvent(
            task_type="agent_registry", agent_name="Agent Registry", action_type=action_type,
            tool_used="AgentRegistryService", permission_level="read_only", approved=True,
            blocked=False, risk_score=1, reason=reason,
        ))

    # -- normalizers ----------------------------------------------------------
    @staticmethod
    def _from_studio(a: dict) -> dict:
        requires = (a.get("guardrails") or {}).get("requires_approval") or []
        return {
            "id": f"studio:{a.get('agent_id')}",
            "source": "agent_studio",
            "source_id": a.get("agent_id"),
            "name": a.get("name") or "Untitled Agent",
            "role": a.get("role") or "",
            "description": a.get("description") or a.get("role") or "",
            "tools": a.get("tools") or [],
            "status": "published" if a.get("published_local") else "draft",
            "approval_gated": bool(requires),
            "quality_score": (a.get("evaluation") or {}).get("score"),
            "version": a.get("version"),
        }

    @staticmethod
    def _from_custom(a: dict) -> dict:
        return {
            "id": f"custom:{a.get('agent_id')}",
            "source": "custom_agents",
            "source_id": a.get("agent_id"),
            "name": a.get("name") or "Custom Agent",
            "role": a.get("role") or "",
            "description": a.get("description") or "",
            "tools": a.get("tools_allowed") or [],
            "status": "enabled" if a.get("enabled", True) else "disabled",
            "approval_gated": str(a.get("approval_level", "")).lower() not in ("", "none", "auto"),
            "quality_score": None,
            "version": None,
        }

    @staticmethod
    def _from_department(dept: dict) -> list[dict]:
        out: list[dict] = []
        roles = [("manager", [dept.get("manager_agent")]),
                 ("worker", dept.get("worker_agents") or []),
                 ("reviewer", dept.get("reviewer_agents") or []),
                 ("auditor", dept.get("auditor_agents") or [])]
        for role, names in roles:
            for name in names:
                if not name:
                    continue
                out.append({
                    "id": f"dept:{dept.get('department_id')}:{name}",
                    "source": "department",
                    "source_id": dept.get("department_id"),
                    "name": name,
                    "role": f"{role} — {dept.get('name', 'Department')}",
                    "description": dept.get("description") or "",
                    "tools": dept.get("allowed_tools") or [],
                    "status": "active" if dept.get("active", True) else "inactive",
                    "approval_gated": dept.get("permission_level") in ("approve_to_run", "manual"),
                    "quality_score": None,
                    "version": None,
                })
        return out

    # -- API -------------------------------------------------------------------
    def _collect(self) -> list[dict]:
        entries: list[dict] = []
        for a in self.storage.read_list("agent_profiles.json"):
            entries.append(self._from_studio(a))
        for a in self.storage.read_list("custom_agents.json"):
            entries.append(self._from_custom(a))
        for d in self.storage.read_list("agent_departments.json"):
            entries.extend(self._from_department(d))
        return entries

    def list_agents(self, source: str | None = None, q: str | None = None, limit: int = 200) -> dict:
        entries = self._collect()
        if source in SOURCES:
            entries = [e for e in entries if e["source"] == source]
        if q:
            needle = q.lower()
            entries = [e for e in entries if needle in e["name"].lower()
                       or needle in e["role"].lower() or needle in e["description"].lower()]
        try:
            limit = max(1, min(1000, int(limit)))
        except (TypeError, ValueError):
            limit = 200
        self._log("registry_listed", f"Listed {min(len(entries), limit)} agents (source={source or 'all'})")
        return {"agents": entries[:limit], "count": len(entries), "sources": list(SOURCES)}

    def find_capable(
        self, capability: str | None = None, source: str | None = None,
        exclude_approval_gated: bool = False, limit: int = 20,
    ) -> list[dict]:
        """Real capability-based candidate search, built on the ``tools``/``role``/
        ``description`` fields every registry entry already carries (declared by
        Agent Studio, Custom Agents, or Departments) -- no separate skill-contract
        schema. Used by AgentNetworkService to resolve a handoff target by
        capability instead of requiring a caller to already know an exact id."""
        entries = self._collect()
        if source in SOURCES:
            entries = [e for e in entries if e["source"] == source]
        if exclude_approval_gated:
            entries = [e for e in entries if not e["approval_gated"]]
        if capability:
            needle = capability.lower()
            entries = [
                e for e in entries
                if any(needle in str(tool).lower() for tool in e["tools"])
                or needle in e["role"].lower() or needle in e["description"].lower()
            ]
        try:
            limit = max(1, min(100, int(limit)))
        except (TypeError, ValueError):
            limit = 20
        active_statuses = ("published", "enabled", "active")
        entries.sort(key=lambda e: (e["status"] not in active_statuses, e["approval_gated"], e["name"]))
        self._log("registry_capability_search", f"Searched capability='{capability}' source={source or 'all'} -> {len(entries)} candidate(s)")
        return entries[:limit]

    def get(self, registry_id: str) -> dict:
        for e in self._collect():
            if e["id"] == registry_id:
                return e
        raise ValueError(f"Agent not found in registry: {registry_id}")

    def analytics_summary(self) -> dict:
        entries = self._collect()
        by: dict[str, int] = {}
        for e in entries:
            by[e["source"]] = by.get(e["source"], 0) + 1
        return {"agent_registry_total": len(entries), "agent_registry_by_source": by}

    def summary(self) -> dict:
        stats: dict[str, Any] = self.analytics_summary()
        entries = self._collect()
        return {
            **stats,
            "approval_gated": sum(1 for e in entries if e["approval_gated"]),
            "note": "Unified read-only registry over Agent Studio, Custom Agents, and Departments. "
                    "Writes stay with each source service.",
        }
