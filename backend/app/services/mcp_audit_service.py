from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.mcp_connector_service import MCPConnectorService
from app.services.mcp_execution_service import MCPExecutionService
from app.services.storage_service import StorageService


class MCPAuditService:
    """v46.0 MCP Audit & Replay.

    Builds a **unified, read-only audit timeline** across the MCP surface —
    connector events (v41), execution requests/results (v42/v43), and MCP-tagged
    governance events — with filtering and export (markdown/JSON). It also offers
    a **read-only replay**: re-deriving what a past execution request *would* do
    today via the connector planning layer (dry) without executing anything. No
    real actions, no secrets; the only stateful write is a stored replay record.
    """

    replays_file = "mcp_replay_records.json"

    def __init__(
        self,
        storage: StorageService,
        governance_service: GovernanceService,
        connector_service: MCPConnectorService,
        execution_service: MCPExecutionService,
    ):
        self.storage = storage
        self.governance = governance_service
        self.connectors = connector_service
        self.executions = execution_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    # ------------------------------------------------------------------
    # Timeline
    # ------------------------------------------------------------------
    def _timeline_events(self) -> list[dict]:
        events: list[dict] = []
        # Connector events (v41).
        for e in self.storage.read_list("mcp_connector_events.json"):
            events.append({
                "source": "connector_event",
                "event_type": e.get("event_type"),
                "connector_id": e.get("connector_id"),
                "message": e.get("message"),
                "risk_level": e.get("risk_level"),
                "created_at": e.get("created_at"),
            })
        # Execution requests (v42/v43).
        for r in self.storage.read_list("mcp_execution_requests.json"):
            events.append({
                "source": "execution_request",
                "event_type": f"execution_{r.get('status')}",
                "connector_id": r.get("connector_id"),
                "message": f"Execution '{r.get('action_name')}' → {r.get('status')}",
                "risk_level": r.get("risk_level"),
                "created_at": r.get("created_at"),
            })
        # MCP-tagged governance events.
        for g in self.storage.read_list("governance_log.json"):
            if str(g.get("task_type", "")).startswith("mcp"):
                events.append({
                    "source": "governance",
                    "event_type": g.get("action_type"),
                    "connector_id": None,
                    "message": g.get("reason"),
                    "risk_level": None,
                    "blocked": g.get("blocked", False),
                    "created_at": g.get("created_at"),
                })
        return events

    def timeline(self, connector_id: str | None = None, event_type: str | None = None, since: str | None = None, limit: int = 200) -> list[dict]:
        events = self._timeline_events()
        if connector_id:
            events = [e for e in events if e.get("connector_id") == connector_id]
        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]
        if since:
            events = [e for e in events if (e.get("created_at") or "") >= since]
        events.sort(key=lambda e: e.get("created_at") or "", reverse=True)
        return events[:limit]

    def summary(self) -> dict:
        events = self._timeline_events()
        by_source: dict[str, int] = {}
        for e in events:
            by_source[e["source"]] = by_source.get(e["source"], 0) + 1
        return {
            "total_events": len(events),
            "by_source": by_source,
            "blocked_events": sum(1 for e in events if e.get("blocked")),
            "replay_count": len(self.storage.read_list(self.replays_file)),
            "recent": self.timeline(limit=10),
            "note": "Read-only unified audit timeline across connector events, executions, and MCP governance.",
        }

    # ------------------------------------------------------------------
    # Export (markdown / json)
    # ------------------------------------------------------------------
    def export(self, fmt: str = "markdown") -> dict:
        events = self.timeline(limit=1000)
        if fmt == "json":
            content = json.dumps(events, indent=2)
            return {"format": "json", "content": content, "event_count": len(events)}
        lines = ["# MCP Audit Timeline", "", f"Generated {self._now()} · {len(events)} event(s)", ""]
        for e in events:
            lines.append(f"- `{e.get('created_at')}` **{e.get('source')}** / {e.get('event_type')} — {e.get('message')}")
        return {"format": "markdown", "content": "\n".join(lines), "event_count": len(events)}

    # ------------------------------------------------------------------
    # Replay (read-only dry re-derivation)
    # ------------------------------------------------------------------
    def replay(self, request_id: str) -> dict:
        request = self.executions.get_request(request_id)
        if request is None:
            raise ValueError("Execution request not found")
        connector = self.connectors.get_connector(request.get("connector_id"))
        if connector is None:
            raise ValueError("Connector not found")
        # Re-derive the plan today (dry) — never executes.
        current_plan = self.connectors.plan_connector_action(
            request.get("connector_id"), request.get("action_name"), {}, None
        )
        record = {
            "replay_id": str(uuid4()),
            "request_id": request_id,
            "connector_id": request.get("connector_id"),
            "action_name": request.get("action_name"),
            "original_status": request.get("status"),
            "original_risk_level": request.get("risk_level"),
            "current_plan": current_plan,
            "would_be_allowed": bool(current_plan.get("planned")),
            "changed": bool(current_plan.get("planned")) != (request.get("status") not in ("blocked", "rejected")),
            "replay_only": True,
            "note": "Read-only replay — re-derived the plan today; no action was executed.",
            "created_at": self._now(),
        }
        self.storage.append(self.replays_file, record)
        self.governance.log_event(
            GovernanceEvent(
                task_type="mcp_audit",
                agent_name="MCP Audit & Replay",
                action_type="mcp_replay",
                tool_used="MCPAuditService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=4,
                reason=f"Replayed request {request_id} (dry, read-only).",
            )
        )
        return record

    def list_replays(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.replays_file)[-limit:]))

    def analytics_summary(self) -> dict:
        return {
            "mcp_audit_events": len(self._timeline_events()),
            "mcp_replays": len(self.storage.read_list(self.replays_file)),
        }
