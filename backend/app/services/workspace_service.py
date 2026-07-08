from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from math import exp
from uuid import uuid4

from app.services.memory_intelligence_service import MemoryIntelligenceService
from app.services.storage_service import StorageService


class WorkspaceService:
    default_name = "Default Workspace"

    def __init__(self, storage: StorageService, memory_v2=None):
        self.storage = storage
        self.memory_intelligence = MemoryIntelligenceService(storage)
        # v140 Workspace Brain: optional MemoryService (v2) collaborator. When it's
        # wired AND running in real pgvector mode, relevant_memory() retrieves by
        # genuine cosine similarity over real embeddings instead of the local
        # sparse/heuristic scoring below — the actual payoff of the v100 Memory v2
        # infrastructure, which until now had no caller in the live agent pipeline.
        # Without it (or in keyword-fallback mode, e.g. plain JSON storage), every
        # method here behaves exactly as before — zero regression.
        self.memory_v2 = memory_v2
        self.ensure_default_workspace()

    def _mirror_to_memory_v2(self, memory: dict) -> None:
        """Best-effort: keep Memory v2 populated as workspace memory grows, so
        real semantic search has something to search. Never blocks a write."""
        if self.memory_v2 is None:
            return
        try:
            text = f"{memory.get('title', '')}\n{memory.get('content', '')}".strip()
            if not text:
                return
            self.memory_v2.add(
                text, kind=memory.get("type") or "note", source="workspace_memory",
                metadata={"workspace_id": memory["workspace_id"], "memory_id": memory["memory_id"]},
            )
        except Exception:
            pass

    def ensure_default_workspace(self) -> dict:
        workspaces = self.storage.read_list("workspaces.json")
        default = next((item for item in workspaces if item.get("default")), None)
        if default:
            return default
        now = datetime.now(UTC).isoformat()
        workspace = {
            "workspace_id": str(uuid4()),
            "name": self.default_name,
            "description": "Default project context for existing chats, files, goals, agents, and memory.",
            "created_at": now,
            "updated_at": now,
            "status": "active",
            "tags": [],
            "default": True,
        }
        workspaces.append(workspace)
        self.storage.write_list("workspaces.json", workspaces)
        return workspace

    def default_workspace_id(self) -> str:
        return self.ensure_default_workspace()["workspace_id"]

    def resolve_workspace_id(self, workspace_id: str | None = None) -> str:
        if workspace_id and self.get_workspace(workspace_id):
            return workspace_id
        return self.default_workspace_id()

    def create_workspace(self, data: dict) -> dict:
        now = datetime.now(UTC).isoformat()
        workspace = {
            "workspace_id": str(uuid4()),
            "name": data.get("name") or "New Workspace",
            "description": data.get("description") or "",
            "created_at": now,
            "updated_at": now,
            "status": "active",
            "tags": data.get("tags", []),
            "default": False,
        }
        workspaces = self.storage.read_list("workspaces.json")
        workspaces.append(workspace)
        self.storage.write_list("workspaces.json", workspaces)
        return workspace

    def list_workspaces(self, include_archived: bool = False) -> list[dict]:
        self.ensure_default_workspace()
        workspaces = self.storage.read_list("workspaces.json")
        if not include_archived:
            workspaces = [item for item in workspaces if item.get("status") != "archived"]
        return sorted(workspaces, key=lambda item: item.get("updated_at") or "", reverse=True)

    def get_workspace(self, workspace_id: str) -> dict | None:
        return next((item for item in self.storage.read_list("workspaces.json") if item.get("workspace_id") == workspace_id), None)

    def update_workspace(self, workspace_id: str, updates: dict) -> dict | None:
        workspaces = self.storage.read_list("workspaces.json")
        workspace = next((item for item in workspaces if item.get("workspace_id") == workspace_id), None)
        if workspace is None:
            return None
        for key in ("name", "description", "status", "tags"):
            if key in updates and updates[key] is not None:
                workspace[key] = updates[key]
        workspace["updated_at"] = datetime.now(UTC).isoformat()
        self.storage.write_list("workspaces.json", workspaces)
        return workspace

    def archive_workspace(self, workspace_id: str) -> dict | None:
        workspace = self.get_workspace(workspace_id)
        if workspace and workspace.get("default"):
            return workspace
        return self.update_workspace(workspace_id, {"status": "archived"})

    def create_memory(self, workspace_id: str, data: dict) -> dict:
        now = datetime.now(UTC).isoformat()
        memory = {
            "memory_id": str(uuid4()),
            "workspace_id": self.resolve_workspace_id(workspace_id),
            "type": data.get("type") or "summary",
            "title": data.get("title") or "Workspace memory",
            "content": data.get("content") or "",
            "source": data.get("source") or "manual",
            "created_at": now,
            "updated_at": now,
            "importance": data.get("importance") or "medium",
            "tags": data.get("tags", []),
            "pinned": bool(data.get("pinned", False)),
            "usage_count": 0,
            "last_used_at": None,
        }
        memory.update(self.memory_intelligence.score_memory(memory))
        self.storage.append("workspace_memory.json", memory)
        self._mirror_to_memory_v2(memory)
        return memory

    def list_memory(
        self,
        workspace_id: str,
        query: str | None = None,
        memory_type: str | None = None,
        tier: str | None = None,
        include_archived: bool = True,
    ) -> list[dict]:
        resolved = self.resolve_workspace_id(workspace_id)
        items = [item for item in self.storage.read_list("workspace_memory.json") if item.get("workspace_id") == resolved]
        if memory_type:
            items = [item for item in items if item.get("type") == memory_type]
        if tier:
            items = [item for item in items if self.memory_intelligence.ensure_metadata(item).get("memory_tier") == tier]
        elif not include_archived:
            items = [item for item in items if self.memory_intelligence.ensure_metadata(item).get("memory_tier") != "archived"]
        if query:
            lowered = query.lower()
            items = [
                item
                for item in items
                if lowered in f"{item.get('title', '')} {item.get('content', '')} {' '.join(item.get('tags', []))}".lower()
            ]
        items = [self.memory_intelligence.public_memory(item) for item in items]
        return sorted(
            items,
            key=lambda item: (
                item.get("memory_tier") == "hot",
                float(item.get("quality_score") or 0),
                self.memory_importance_score(item),
                item.get("updated_at") or item.get("created_at") or "",
            ),
            reverse=True,
        )

    def get_memory(self, workspace_id: str, memory_id: str) -> dict | None:
        resolved = self.resolve_workspace_id(workspace_id)
        return next(
            (
                item
                for item in self.storage.read_list("workspace_memory.json")
                if item.get("workspace_id") == resolved and item.get("memory_id") == memory_id
            ),
            None,
        )

    def update_memory(self, workspace_id: str, memory_id: str, updates: dict) -> dict | None:
        resolved = self.resolve_workspace_id(workspace_id)
        memories = self.storage.read_list("workspace_memory.json")
        memory = next((item for item in memories if item.get("workspace_id") == resolved and item.get("memory_id") == memory_id), None)
        if memory is None:
            return None
        for key in ("type", "title", "content", "source", "importance", "tags", "pinned"):
            if key in updates and updates[key] is not None:
                memory[key] = updates[key]
        memory["updated_at"] = datetime.now(UTC).isoformat()
        memory.update(self.memory_intelligence.score_memory(memory))
        self.storage.write_list("workspace_memory.json", memories)
        return memory

    def delete_memory(self, workspace_id: str, memory_id: str) -> bool:
        resolved = self.resolve_workspace_id(workspace_id)
        memories = self.storage.read_list("workspace_memory.json")
        next_memories = [
            item
            for item in memories
            if not (item.get("workspace_id") == resolved and item.get("memory_id") == memory_id)
        ]
        if len(next_memories) == len(memories):
            return False
        self.storage.write_list("workspace_memory.json", next_memories)
        return True

    def _semantic_candidates(self, workspace_id: str, user_input: str, limit: int) -> list[dict]:
        """Prefer Memory v2's real cosine-similarity search when it's wired and
        running on real embeddings (pgvector mode). Resolves each hit back to its
        source record — a workspace_memory item, or (v140 task 2) a goal mirrored
        by GoalService — so downstream usage-tracking and formatting are
        unaffected either way. Any miss — v2 unwired, keyword-fallback mode, or a
        lookup failure — degrades to the original local heuristic search over
        workspace memory, unchanged."""
        if self.memory_v2 is not None and self.memory_v2.mode == "pgvector":
            try:
                hits = self.memory_v2.search(user_input, limit=limit, workspace_id=workspace_id).get("results", [])
                memories_by_id = {
                    item.get("memory_id"): item
                    for item in self.storage.read_list("workspace_memory.json")
                    if item.get("workspace_id") == workspace_id
                }
                goals_by_id = {
                    item.get("goal_id"): item
                    for item in self.storage.read_list("goals.json")
                    if item.get("workspace_id") == workspace_id
                }
                resolved = []
                for hit in hits:
                    metadata = hit.get("metadata") or {}
                    if (mid := metadata.get("memory_id")) in memories_by_id:
                        resolved.append(memories_by_id[mid])
                    elif (gid := metadata.get("goal_id")) in goals_by_id:
                        goal = goals_by_id[gid]
                        resolved.append({"type": "goal", "title": goal.get("title", "Goal"), "content": goal.get("description", "")})
                if resolved:
                    return resolved
            except Exception:
                pass  # fall through to the heuristic path below
        semantic = self.memory_intelligence.semantic_search(workspace_id, user_input, limit=limit, include_archived=False)
        return [row["memory"] for row in semantic.get("results", [])]

    def relevant_memory(self, workspace_id: str, user_input: str, limit: int = 6, char_limit: int = 4000) -> tuple[str, list[dict]]:
        resolved = self.resolve_workspace_id(workspace_id)
        selected = self._semantic_candidates(resolved, user_input, limit)
        if len(selected) < limit:
            selected_ids = {item.get("memory_id") for item in selected}
            fallback = [
                item
                for item in self.list_memory(resolved, include_archived=False)
                if item.get("memory_id") not in selected_ids and (item.get("importance") == "high" or item.get("pinned"))
            ]
            selected.extend(fallback[: max(limit - len(selected), 0)])
        self._record_memory_usage(workspace_id, [item.get("memory_id") for item in selected if item.get("memory_id")])
        parts = []
        remaining = char_limit
        for item in selected:
            text = f"{item.get('type')}: {item.get('title')}\n{item.get('content')}"
            clipped = text[:remaining]
            if not clipped:
                break
            parts.append(clipped)
            remaining -= len(clipped)
        return "\n\n".join(parts), selected

    def memory_importance_score(self, memory: dict) -> float:
        importance_weight = {"high": 50.0, "medium": 25.0, "low": 10.0}
        score = importance_weight.get(memory.get("importance", "medium"), 25.0)
        score += float(memory.get("quality_score") or 0) * 0.15
        if memory.get("memory_tier") == "hot":
            score += 20.0
        if memory.get("memory_tier") == "archived":
            score -= 60.0
        score += min(int(memory.get("usage_count") or 0), 20) * 2.0
        if memory.get("pinned"):
            score += 100.0
        score += self._recency_score(memory.get("updated_at") or memory.get("created_at"))
        return round(score, 2)

    def _recency_score(self, timestamp: str | None) -> float:
        if not timestamp:
            return 0.0
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return 0.0
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        age_days = max((datetime.now(UTC) - parsed).total_seconds() / 86400, 0)
        return 20.0 * exp(-age_days / 30.0)

    def _record_memory_usage(self, workspace_id: str, memory_ids: list[str]) -> None:
        if not memory_ids:
            return
        resolved = self.resolve_workspace_id(workspace_id)
        memories = self.storage.read_list("workspace_memory.json")
        now = datetime.now(UTC).isoformat()
        changed = False
        for memory in memories:
            if memory.get("workspace_id") == resolved and memory.get("memory_id") in memory_ids:
                memory["usage_count"] = int(memory.get("usage_count") or 0) + 1
                memory["last_used_at"] = now
                changed = True
        if changed:
            self.storage.write_list("workspace_memory.json", memories)

    def summarize_workspace(self, workspace_id: str) -> dict:
        resolved = self.resolve_workspace_id(workspace_id)
        memories = self.list_memory(resolved)
        types = Counter(item.get("type", "summary") for item in memories)
        return {
            "workspace_id": resolved,
            "memory_count": len(memories),
            "memory_types": [{"type": name, "count": count} for name, count in types.most_common()],
            "semantic_recall_engine": self.memory_v2.mode if self.memory_v2 is not None else "heuristic",
        }
