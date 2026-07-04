from __future__ import annotations

import json
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Each timeline source: event type, collection, title fields, detail fields, status field.
# All read-only projections of existing local state — nothing here is written by this service.
TIMELINE_SOURCES = [
    {"type": "governance", "file": "governance_log.json",
     "title_keys": ["action_type"], "detail_keys": ["reason", "agent_name", "tool_used"], "status_key": "permission_level", "actor_key": "agent_name"},
    {"type": "route", "file": "master_agent_runs.json",
     "title_keys": ["primary_domain"], "detail_keys": ["request"], "status_key": None, "actor_key": None},
    {"type": "goal", "file": "goals.json",
     "title_keys": ["title", "name"], "detail_keys": ["description", "status"], "status_key": "status", "actor_key": None},
    {"type": "file", "file": "files.json",
     "title_keys": ["filename", "name"], "detail_keys": ["summary", "extension"], "status_key": "status", "actor_key": None},
    {"type": "report", "file": "portfolio_reports.json",
     "title_keys": ["title", "name"], "detail_keys": ["summary", "headline"], "status_key": None, "actor_key": None},
    {"type": "report", "file": "business_reports.json",
     "title_keys": ["title", "name"], "detail_keys": ["summary", "headline"], "status_key": None, "actor_key": None},
    {"type": "memory", "file": "workspace_memory.json",
     "title_keys": ["title", "key"], "detail_keys": ["content", "value"], "status_key": None, "actor_key": None},
    {"type": "tool_execution", "file": "mcp_execution_requests.json",
     "title_keys": ["action_name", "connector_slug"], "detail_keys": ["connector_slug", "status"], "status_key": "status", "actor_key": "connector_slug"},
    {"type": "approval", "file": "business_approval_items.json",
     "title_keys": ["title", "action_type"], "detail_keys": ["summary", "status"], "status_key": "status", "actor_key": None},
]

ALL_TYPES = sorted({s["type"] for s in TIMELINE_SOURCES})
_TIMESTAMP_KEYS = ("created_at", "timestamp", "at", "updated_at")


class ActivityTimelineService:
    """v63.0 Unified Activity Timeline — one chronological view of everything the OS did.

    Merges events from the governance log, Master Agent routes, goals, files, reports,
    memory, MCP tool executions, and approvals into a single time-ordered timeline.
    Filterable by workspace, type, actor, status, and date; each event can be expanded
    for detail and the whole timeline can be exported (markdown or JSON). It is strictly
    read-only, links every governance event, and excludes secret values. Queries are
    governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _first(item: dict, keys: list[str], default: str = "") -> str:
        for key in keys:
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value
            if value not in (None, "", [], {}):
                return str(value)
        return default

    @staticmethod
    def _timestamp(item: dict) -> str:
        for key in _TIMESTAMP_KEYS:
            value = item.get(key)
            if isinstance(value, str) and value:
                return value
        return ""

    def _events(self, workspace_id: str | None, types: set[str] | None, status: str | None, actor: str | None, since: str | None) -> list[dict]:
        events: list[dict] = []
        for source in TIMELINE_SOURCES:
            if types and source["type"] not in types:
                continue
            for item in self.storage.read_list(source["file"]):
                if not isinstance(item, dict):
                    continue
                if workspace_id and item.get("workspace_id") not in (None, workspace_id):
                    continue
                ts = self._timestamp(item)
                if since and ts and ts < since:
                    continue
                event_status = item.get(source["status_key"]) if source["status_key"] else None
                if status and str(event_status or "").lower() != status.lower():
                    continue
                event_actor = item.get(source["actor_key"]) if source["actor_key"] else None
                if actor and actor.lower() not in str(event_actor or "").lower():
                    continue
                detail = self._first(item, source["detail_keys"])
                events.append({
                    "type": source["type"],
                    "source_collection": source["file"],
                    "title": self._first(item, source["title_keys"], default=source["type"])[:160],
                    "detail": detail[:400],
                    "status": event_status,
                    "actor": event_actor,
                    "workspace_id": item.get("workspace_id"),
                    "governance_linked": source["type"] == "governance",
                    "timestamp": ts,
                })
        events.sort(key=lambda e: e["timestamp"], reverse=True)
        return events

    def timeline(self, workspace_id: str | None = None, types: list[str] | None = None, status: str | None = None, actor: str | None = None, since: str | None = None, limit: int = 100) -> dict:
        events = self._events(workspace_id, set(types) if types else None, status, actor, since)
        limited = events[:limit]
        by_type: dict[str, int] = {}
        for event in limited:
            by_type[event["type"]] = by_type.get(event["type"], 0) + 1
        self.governance.log_event(
            GovernanceEvent(
                task_type="activity_timeline",
                agent_name="Activity Timeline",
                action_type="activity_timeline_viewed",
                tool_used="ActivityTimelineService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=f"Built a unified activity timeline ({len(limited)} of {len(events)} events).",
            )
        )
        return {
            "event_count": len(limited),
            "total_available": len(events),
            "by_type": by_type,
            "types": ALL_TYPES,
            "events": limited,
            "note": "Read-only chronological aggregation of local events — no secrets, no writes.",
        }

    def export(self, fmt: str = "markdown", workspace_id: str | None = None, types: list[str] | None = None, since: str | None = None, limit: int = 500) -> dict:
        events = self._events(workspace_id, set(types) if types else None, None, None, since)[:limit]
        if fmt == "json":
            content = json.dumps(events, indent=2)
        else:
            lines = ["# EvolveAgent AI — Activity Timeline", "", f"_Exported {self._now()} · {len(events)} events_", ""]
            for event in events:
                status = f" · {event['status']}" if event.get("status") else ""
                lines.append(f"- **{event['timestamp'] or 'n/a'}** · `{event['type']}`{status} — {event['title']}")
                if event.get("detail"):
                    lines.append(f"  - {event['detail']}")
            content = "\n".join(lines)
        return {"format": fmt, "event_count": len(events), "content": content}

    def analytics_summary(self) -> dict:
        events = self._events(None, None, None, None, None)
        return {
            "activity_timeline_events": len(events),
            "activity_timeline_sources": len(TIMELINE_SOURCES),
        }

    def summary(self) -> dict:
        events = self._events(None, None, None, None, None)
        by_type: dict[str, int] = {}
        for event in events:
            by_type[event["type"]] = by_type.get(event["type"], 0) + 1
        return {
            "total_events": len(events),
            "by_type": by_type,
            "types": ALL_TYPES,
            "most_recent": events[0]["timestamp"] if events else None,
            "note": "Read-only aggregation across the governance log, routes, goals, files, reports, memory, tool executions, and approvals.",
        }
