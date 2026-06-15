from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from math import exp
from uuid import uuid4

from app.services.storage_service import StorageService


STOP_WORDS = {
    "about",
    "after",
    "again",
    "also",
    "because",
    "before",
    "being",
    "from",
    "have",
    "into",
    "more",
    "should",
    "that",
    "their",
    "there",
    "this",
    "with",
    "your",
}


class MemoryIntelligenceService:
    """Local, JSON-backed memory intelligence without external embeddings."""

    def __init__(self, storage: StorageService):
        self.storage = storage

    def score_memory(self, memory: dict, duplicate_penalty: bool = False) -> dict:
        content = f"{memory.get('title', '')} {memory.get('content', '')}".strip()
        words = self.tokens(content)
        reasons = []
        score = 35.0

        content_length = len(memory.get("content") or "")
        if content_length >= 120:
            score += 18
            reasons.append("specific content")
        elif content_length >= 40:
            score += 10
            reasons.append("usable detail")
        else:
            score -= 12
            reasons.append("thin content")

        unique_terms = len(set(words))
        if unique_terms >= 18:
            score += 12
            reasons.append("rich keywords")
        elif unique_terms < 6:
            score -= 8
            reasons.append("few unique terms")

        importance = memory.get("importance", "medium")
        score += {"high": 16, "medium": 8, "low": 0}.get(importance, 8)
        reasons.append(f"{importance} importance")

        usage_count = int(memory.get("usage_count") or 0)
        if usage_count:
            score += min(usage_count, 10) * 2
            reasons.append("used in context")

        if memory.get("pinned"):
            score += 22
            reasons.append("pinned")

        recency = self.recency_score(memory.get("updated_at") or memory.get("created_at"))
        score += recency
        if recency > 8:
            reasons.append("recent")

        if duplicate_penalty:
            score -= 20
            reasons.append("possible duplicate")

        score = max(0, min(100, round(score, 1)))
        return {
            "quality_score": score,
            "quality_reasons": reasons[:5],
            "semantic_terms": self.semantic_terms(memory),
            "memory_tier": self.tier_for(memory, score),
        }

    def tier_for(self, memory: dict, quality_score: float) -> str:
        if memory.get("memory_tier") == "archived":
            return "archived"
        if memory.get("pinned") or memory.get("importance") == "high" or quality_score >= 72 or int(memory.get("usage_count") or 0) >= 5:
            return "hot"
        if quality_score < 35:
            return "archived"
        return "warm"

    def rescore_workspace(self, workspace_id: str) -> dict:
        memories = self.storage.read_list("workspace_memory.json")
        workspace_items = [item for item in memories if item.get("workspace_id") == workspace_id]
        duplicate_ids = set()
        for group in self.find_duplicate_groups(workspace_items):
            keep = self.best_memory(group)
            duplicate_ids.update(item.get("memory_id") for item in group if item.get("memory_id") != keep.get("memory_id"))

        now = datetime.now(UTC).isoformat()
        rescored = []
        for memory in memories:
            if memory.get("workspace_id") != workspace_id:
                continue
            scoring = self.score_memory(memory, duplicate_penalty=memory.get("memory_id") in duplicate_ids)
            memory.update(scoring)
            memory["updated_at"] = memory.get("updated_at") or now
            rescored.append(memory)
        self.storage.write_list("workspace_memory.json", memories)
        return self.summary(workspace_id, rescored)

    def summary(self, workspace_id: str, items: list[dict] | None = None) -> dict:
        memories = items if items is not None else [
            item for item in self.storage.read_list("workspace_memory.json") if item.get("workspace_id") == workspace_id
        ]
        scored = [self.ensure_metadata(item) for item in memories]
        tiers = Counter(item.get("memory_tier", "warm") for item in scored)
        average = round(sum(float(item.get("quality_score") or 0) for item in scored) / len(scored), 1) if scored else 0
        return {
            "workspace_id": workspace_id,
            "total_memories": len(scored),
            "average_quality_score": average,
            "tiers": [{"tier": tier, "count": count} for tier, count in tiers.most_common()],
            "hot_memories": [self.public_memory(item) for item in sorted(scored, key=lambda row: row.get("quality_score") or 0, reverse=True)[:5]],
            "suggested_consolidations": self.consolidation_preview(workspace_id)["groups"],
        }

    def semantic_search(self, workspace_id: str, query: str, limit: int = 10, include_archived: bool = False) -> dict:
        query_terms = self.tokens(query)
        results = []
        for memory in self.storage.read_list("workspace_memory.json"):
            if memory.get("workspace_id") != workspace_id:
                continue
            enriched = self.ensure_metadata(memory)
            if not include_archived and enriched.get("memory_tier") == "archived":
                continue
            memory_terms = set(enriched.get("semantic_terms") or self.semantic_terms(enriched))
            matched = sorted(memory_terms.intersection(query_terms))
            if query_terms:
                semantic_score = len(matched) / max(len(query_terms), 1) * 60
            else:
                semantic_score = 0
            quality_boost = float(enriched.get("quality_score") or 0) * 0.25
            pin_boost = 15 if enriched.get("pinned") else 0
            score = round(semantic_score + quality_boost + pin_boost, 2)
            if score > 8 or matched:
                results.append({
                    "score": score,
                    "matched_terms": matched,
                    "memory": self.public_memory(enriched),
                })
        return {
            "workspace_id": workspace_id,
            "query": query,
            "results": sorted(results, key=lambda row: row["score"], reverse=True)[:limit],
        }

    def consolidation_preview(self, workspace_id: str) -> dict:
        memories = [
            self.ensure_metadata(item)
            for item in self.storage.read_list("workspace_memory.json")
            if item.get("workspace_id") == workspace_id and item.get("memory_tier") != "archived"
        ]
        groups = []
        for group in self.find_duplicate_groups(memories):
            keep = self.best_memory(group)
            groups.append({
                "group_id": str(uuid4()),
                "keep_memory_id": keep.get("memory_id"),
                "duplicate_memory_ids": [item.get("memory_id") for item in group if item.get("memory_id") != keep.get("memory_id")],
                "reason": "similar title/content terms",
                "items": [self.public_memory(item) for item in group],
            })
        return {"workspace_id": workspace_id, "groups": groups}

    def consolidate(self, workspace_id: str, approved: bool = False) -> dict:
        preview = self.consolidation_preview(workspace_id)
        if not approved:
            return {**preview, "applied": False}

        memories = self.storage.read_list("workspace_memory.json")
        now = datetime.now(UTC).isoformat()
        archived = []
        for group in preview["groups"]:
            keep_id = group["keep_memory_id"]
            duplicate_ids = set(group["duplicate_memory_ids"])
            duplicate_tags = set()
            for memory in memories:
                if memory.get("memory_id") in duplicate_ids:
                    memory["memory_tier"] = "archived"
                    memory["consolidated_into"] = keep_id
                    memory["archived_at"] = now
                    memory["updated_at"] = now
                    archived.append(memory.get("memory_id"))
                    duplicate_tags.update(memory.get("tags") or [])
            for memory in memories:
                if memory.get("memory_id") == keep_id:
                    memory["tags"] = sorted(set(memory.get("tags") or []).union(duplicate_tags))
                    memory["updated_at"] = now
                    memory.update(self.score_memory(memory))
                    break
        self.storage.write_list("workspace_memory.json", memories)
        return {"workspace_id": workspace_id, "applied": True, "archived_memory_ids": archived, "groups": preview["groups"]}

    def archive_memory(self, workspace_id: str, memory_id: str, archived: bool = True) -> dict | None:
        memories = self.storage.read_list("workspace_memory.json")
        memory = next(
            (item for item in memories if item.get("workspace_id") == workspace_id and item.get("memory_id") == memory_id),
            None,
        )
        if memory is None:
            return None
        now = datetime.now(UTC).isoformat()
        memory["memory_tier"] = "archived" if archived else self.score_memory({**memory, "memory_tier": "warm"})["memory_tier"]
        memory["archived_at"] = now if archived else None
        memory["updated_at"] = now
        if not archived:
            memory.pop("consolidated_into", None)
        memory.update(self.score_memory(memory))
        self.storage.write_list("workspace_memory.json", memories)
        return self.public_memory(memory)

    def find_duplicate_groups(self, memories: list[dict]) -> list[list[dict]]:
        groups_by_fingerprint: dict[str, list[dict]] = defaultdict(list)
        for memory in memories:
            terms = self.semantic_terms(memory)
            if len(terms) < 3:
                continue
            fingerprint = " ".join(terms[:6])
            groups_by_fingerprint[fingerprint].append(memory)

        groups = [items for items in groups_by_fingerprint.values() if len(items) > 1]
        if groups:
            return groups

        paired = []
        seen = set()
        for index, left in enumerate(memories):
            left_terms = set(self.semantic_terms(left))
            for right in memories[index + 1:]:
                pair_key = tuple(sorted([left.get("memory_id"), right.get("memory_id")]))
                if pair_key in seen:
                    continue
                right_terms = set(self.semantic_terms(right))
                if not left_terms or not right_terms:
                    continue
                overlap = len(left_terms.intersection(right_terms)) / max(len(left_terms.union(right_terms)), 1)
                same_title = (left.get("title") or "").strip().lower() == (right.get("title") or "").strip().lower()
                if overlap >= 0.72 or same_title:
                    paired.append([left, right])
                    seen.add(pair_key)
        return paired

    def best_memory(self, group: list[dict]) -> dict:
        return sorted(
            group,
            key=lambda item: (
                bool(item.get("pinned")),
                float(item.get("quality_score") or self.score_memory(item)["quality_score"]),
                len(item.get("content") or ""),
                item.get("updated_at") or item.get("created_at") or "",
            ),
            reverse=True,
        )[0]

    def ensure_metadata(self, memory: dict) -> dict:
        if memory.get("quality_score") is None or memory.get("memory_tier") is None or not memory.get("semantic_terms"):
            return {**memory, **self.score_memory(memory)}
        return memory

    def public_memory(self, memory: dict) -> dict:
        enriched = self.ensure_metadata(memory)
        keys = (
            "memory_id",
            "workspace_id",
            "type",
            "title",
            "content",
            "source",
            "importance",
            "tags",
            "pinned",
            "usage_count",
            "last_used_at",
            "quality_score",
            "quality_reasons",
            "semantic_terms",
            "memory_tier",
            "consolidated_into",
            "created_at",
            "updated_at",
        )
        return {key: enriched.get(key) for key in keys if key in enriched}

    def semantic_terms(self, memory: dict) -> list[str]:
        text = f"{memory.get('title', '')} {memory.get('content', '')} {' '.join(memory.get('tags', []))}"
        counts = Counter(self.token_list(text))
        ranked = sorted(counts.items(), key=lambda row: (-row[1], row[0]))
        return [term for term, _ in ranked[:18]]

    def tokens(self, text: str) -> set[str]:
        return set(self.token_list(text))

    def token_list(self, text: str) -> list[str]:
        return [
            token
            for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]{2,}", text.lower())
            if token not in STOP_WORDS and len(token) > 2
        ]

    def recency_score(self, timestamp: str | None) -> float:
        if not timestamp:
            return 0.0
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return 0.0
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        age_days = max((datetime.now(UTC) - parsed).total_seconds() / 86400, 0)
        return 12.0 * exp(-age_days / 45.0)
