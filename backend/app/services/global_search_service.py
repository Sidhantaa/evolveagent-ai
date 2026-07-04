from __future__ import annotations

import re
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Each searchable source: label, result type, JSON collection, id key candidates,
# title field candidates, and the fields whose text is indexed for matching.
# Read-only projection only — secrets/governance/analytics are deliberately excluded.
SEARCH_SOURCES = [
    {"label": "Chats", "type": "chat", "file": "chat_sessions.json",
     "id_keys": ["session_id", "id"], "title_keys": ["title", "name"], "text_keys": ["title", "summary"]},
    {"label": "Messages", "type": "message", "file": "messages.json",
     "id_keys": ["message_id", "id"], "title_keys": ["role"], "text_keys": ["content"]},
    {"label": "Files", "type": "file", "file": "files.json",
     "id_keys": ["file_id", "id"], "title_keys": ["filename", "name"], "text_keys": ["filename", "summary", "extracted_text_preview"]},
    {"label": "Goals", "type": "goal", "file": "goals.json",
     "id_keys": ["goal_id", "id"], "title_keys": ["title", "name"], "text_keys": ["title", "description"]},
    {"label": "Agents", "type": "agent", "file": "custom_agents.json",
     "id_keys": ["agent_id", "id"], "title_keys": ["name"], "text_keys": ["name", "role", "description", "system_prompt"]},
    {"label": "Memory", "type": "memory", "file": "workspace_memory.json",
     "id_keys": ["memory_id", "id"], "title_keys": ["title", "key"], "text_keys": ["title", "content", "value"]},
    {"label": "Workflows", "type": "workflow", "file": "playbooks.json",
     "id_keys": ["playbook_id", "id"], "title_keys": ["name", "title"], "text_keys": ["name", "description"]},
    {"label": "Reports", "type": "report", "file": "portfolio_reports.json",
     "id_keys": ["report_id", "id"], "title_keys": ["title", "name"], "text_keys": ["title", "summary", "headline"]},
    {"label": "Reports", "type": "report", "file": "business_reports.json",
     "id_keys": ["report_id", "id"], "title_keys": ["title", "name"], "text_keys": ["title", "summary", "headline"]},
    {"label": "Simulations", "type": "simulation", "file": "simulation_worlds.json",
     "id_keys": ["world_id", "id"], "title_keys": ["name", "title"], "text_keys": ["name", "description", "premise"]},
    {"label": "Schedules", "type": "schedule", "file": "scheduled_tasks.json",
     "id_keys": ["task_id", "id"], "title_keys": ["name", "title"], "text_keys": ["name", "detail", "action_type"]},
    {"label": "Ideas", "type": "idea", "file": "innovation_ideas.json",
     "id_keys": ["idea_id", "id"], "title_keys": ["title", "name"], "text_keys": ["title", "description"]},
    {"label": "Documents", "type": "document", "file": "retrieval_documents.json",
     "id_keys": ["document_id", "id"], "title_keys": ["title", "name"], "text_keys": ["title", "text", "content"]},
]

ALL_TYPES = sorted({s["type"] for s in SEARCH_SOURCES})


class GlobalSearchService:
    """v62.0 Global Search — one read-only search bar across the whole OS.

    Searches a curated set of local JSON collections (chats, messages, files,
    goals, agents, memory, workflows, reports, simulations, schedules, ideas,
    documents) by keyword overlap and returns ranked results with a short
    preview, the source collection (for a Developer-Mode source trace), workspace,
    and timestamp. It is strictly read-only — it never mutates data, and it
    excludes secrets, governance logs, and analytics. Searches are governance-logged.
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
    def _blob(item: dict, keys: list[str]) -> str:
        parts = []
        for key in keys:
            value = item.get(key)
            if isinstance(value, str):
                parts.append(value)
            elif value not in (None, "", [], {}):
                parts.append(str(value))
        return " ".join(parts)

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return [t for t in re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).split() if t]

    def sources(self) -> dict:
        counts = {}
        for source in SEARCH_SOURCES:
            counts[source["file"]] = len(self.storage.read_list(source["file"]))
        return {
            "sources": [
                {"label": s["label"], "type": s["type"], "collection": s["file"], "indexed": counts[s["file"]]}
                for s in SEARCH_SOURCES
            ],
            "types": ALL_TYPES,
            "total_indexed_items": sum(counts.values()),
            "note": "Read-only search across local collections — excludes secrets, governance, and analytics.",
        }

    def search(self, query: str, workspace_id: str | None = None, types: list[str] | None = None, since: str | None = None, limit: int = 30) -> dict:
        query = (query or "").strip()
        terms = self._tokens(query)
        wanted_types = set(types) if types else None
        results: list[dict] = []

        if terms:
            for source in SEARCH_SOURCES:
                if wanted_types and source["type"] not in wanted_types:
                    continue
                for item in self.storage.read_list(source["file"]):
                    if not isinstance(item, dict):
                        continue
                    if workspace_id and item.get("workspace_id") not in (None, workspace_id):
                        continue
                    created = item.get("created_at") or item.get("timestamp") or ""
                    if since and isinstance(created, str) and created and created < since:
                        continue
                    blob = self._blob(item, source["text_keys"]).lower()
                    if not blob:
                        continue
                    score = sum(blob.count(term) for term in terms)
                    if score <= 0:
                        continue
                    title = self._first(item, source["title_keys"], default=f"{source['label']} item")
                    preview = self._blob(item, source["text_keys"]).strip()
                    results.append({
                        "type": source["type"],
                        "label": source["label"],
                        "source_collection": source["file"],   # Developer-Mode source trace
                        "id": self._first(item, source["id_keys"], default=""),
                        "title": title[:160],
                        "preview": (preview[:240] + ("…" if len(preview) > 240 else "")),
                        "workspace_id": item.get("workspace_id"),
                        "created_at": created,
                        "score": score,
                    })

        results.sort(key=lambda r: r["score"], reverse=True)
        results = results[:limit]

        by_type: dict[str, int] = {}
        for result in results:
            by_type[result["type"]] = by_type.get(result["type"], 0) + 1

        self.governance.log_event(
            GovernanceEvent(
                task_type="global_search",
                agent_name="Global Search",
                action_type="global_search",
                tool_used="GlobalSearchService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=f"Searched {len(SEARCH_SOURCES)} sources for a query; {len(results)} result(s).",
            )
        )
        return {
            "query": query,
            "result_count": len(results),
            "by_type": by_type,
            "results": results,
            "note": "Read-only. Use a result as context to seed the composer; nothing is modified.",
        }

    def analytics_summary(self) -> dict:
        total = sum(len(self.storage.read_list(s["file"])) for s in SEARCH_SOURCES)
        return {
            "search_sources": len(SEARCH_SOURCES),
            "search_indexed_items": total,
        }
