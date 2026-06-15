from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from math import exp, sqrt
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
        tier_decision = self.tier_decision(memory, score)
        return {
            "quality_score": score,
            "quality_reasons": reasons[:5],
            "quality_recommendation": self.quality_recommendation(memory, score, reasons),
            "semantic_terms": self.semantic_terms(memory),
            "memory_vector_id": self.vector_id(memory),
            "memory_tier": tier_decision["tier"],
            "tier_reason": tier_decision["reason"],
            "retention_action": tier_decision["retention_action"],
        }

    def tier_for(self, memory: dict, quality_score: float) -> str:
        return self.tier_decision(memory, quality_score)["tier"]

    def tier_decision(self, memory: dict, quality_score: float) -> dict:
        if memory.get("memory_tier") == "archived":
            return {
                "tier": "archived",
                "reason": "manually archived or consolidated",
                "retention_action": "keep_archived",
            }
        usage_count = int(memory.get("usage_count") or 0)
        age_days = self.age_days(memory.get("updated_at") or memory.get("created_at"))
        if memory.get("pinned"):
            return {"tier": "hot", "reason": "pinned by user", "retention_action": "keep_hot"}
        if memory.get("importance") == "high" and quality_score >= 45:
            return {"tier": "hot", "reason": "high importance", "retention_action": "keep_hot"}
        if quality_score >= 78 or usage_count >= 5:
            return {"tier": "hot", "reason": "high score or frequent use", "retention_action": "keep_hot"}
        if quality_score < 35:
            return {"tier": "archived", "reason": "low quality score", "retention_action": "archive"}
        if age_days > 120 and usage_count == 0 and memory.get("importance") == "low":
            return {"tier": "archived", "reason": "stale low-importance memory", "retention_action": "archive"}
        if age_days > 60 and usage_count == 0 and quality_score < 55:
            return {"tier": "warm", "reason": "stale but still usable", "retention_action": "review"}
        return {"tier": "warm", "reason": "usable workspace context", "retention_action": "keep_warm"}

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
            old_tier = memory.get("memory_tier", "warm")
            scoring = self.score_memory(memory, duplicate_penalty=memory.get("memory_id") in duplicate_ids)
            memory.update(scoring)
            self.record_tier_transition(memory, old_tier, memory.get("memory_tier"), memory.get("tier_reason"))
            if not memory.get("tier_history"):
                memory["tier_history"] = [{
                    "from": "unclassified",
                    "to": memory.get("memory_tier", "warm"),
                    "reason": memory.get("tier_reason") or "initial tier classification",
                    "created_at": now,
                }]
            memory["updated_at"] = memory.get("updated_at") or now
            rescored.append(memory)
        self.storage.write_list("workspace_memory.json", memories)
        self.rebuild_index(workspace_id)
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
            "recommended_actions": self.recommended_actions(scored),
            "vector_index": self.index_summary(workspace_id),
            "hot_memories": [self.public_memory(item) for item in sorted(scored, key=lambda row: row.get("quality_score") or 0, reverse=True)[:5]],
            "suggested_consolidations": self.consolidation_preview(workspace_id)["groups"],
        }

    def maintain_tiers(self, workspace_id: str) -> dict:
        before = {
            item.get("memory_id"): item.get("memory_tier", "warm")
            for item in self.storage.read_list("workspace_memory.json")
            if item.get("workspace_id") == workspace_id
        }
        summary = self.rescore_workspace(workspace_id)
        memories = [
            item for item in self.storage.read_list("workspace_memory.json")
            if item.get("workspace_id") == workspace_id
        ]
        transitions = [
            {
                "memory_id": item.get("memory_id"),
                "title": item.get("title"),
                "from": before.get(item.get("memory_id"), "warm"),
                "to": item.get("memory_tier", "warm"),
                "reason": item.get("tier_reason"),
            }
            for item in memories
            if before.get(item.get("memory_id"), "warm") != item.get("memory_tier", "warm")
        ]
        return {**summary, "tier_transitions": transitions}

    def semantic_search(self, workspace_id: str, query: str, limit: int = 10, include_archived: bool = False) -> dict:
        if not query.strip():
            return {"workspace_id": workspace_id, "query": query, "results": []}
        self.ensure_index(workspace_id)
        query_terms = self.tokens(self.expand_query(query))
        query_vector = self.sparse_vector(query)
        vector_entries = {
            item.get("memory_id"): item
            for item in self.storage.read_list("memory_vectors.json")
            if item.get("workspace_id") == workspace_id
        }
        results = []
        for memory in self.storage.read_list("workspace_memory.json"):
            if memory.get("workspace_id") != workspace_id:
                continue
            enriched = self.ensure_metadata(memory)
            if not include_archived and enriched.get("memory_tier") == "archived":
                continue
            vector_entry = vector_entries.get(memory.get("memory_id"))
            memory_vector = vector_entry.get("vector", {}) if vector_entry else self.sparse_vector(self.memory_text(enriched))
            memory_terms = set(vector_entry.get("terms", []) if vector_entry else enriched.get("semantic_terms") or self.semantic_terms(enriched))
            matched = sorted(memory_terms.intersection(query_terms))
            cosine = self.cosine_similarity(query_vector, memory_vector)
            if query_terms:
                semantic_score = len(matched) / max(len(query_terms), 1) * 35
            else:
                semantic_score = 0
            quality_boost = float(enriched.get("quality_score") or 0) * 0.25
            pin_boost = 15 if enriched.get("pinned") else 0
            tier_boost = 10 if enriched.get("memory_tier") == "hot" else 0
            score = round((cosine * 55) + semantic_score + quality_boost + pin_boost + tier_boost, 2)
            if score > 12 or matched:
                results.append({
                    "score": score,
                    "vector_score": round(cosine, 4),
                    "matched_terms": matched,
                    "memory": self.public_memory(enriched),
                })
        return {
            "workspace_id": workspace_id,
            "query": query,
            "index": self.index_summary(workspace_id),
            "results": sorted(results, key=lambda row: row["score"], reverse=True)[:limit],
        }

    def rebuild_index(self, workspace_id: str) -> dict:
        memories = [
            self.ensure_metadata(item)
            for item in self.storage.read_list("workspace_memory.json")
            if item.get("workspace_id") == workspace_id
        ]
        all_vectors = [item for item in self.storage.read_list("memory_vectors.json") if item.get("workspace_id") != workspace_id]
        now = datetime.now(UTC).isoformat()
        entries = []
        for memory in memories:
            if memory.get("memory_tier") == "archived":
                continue
            vector = self.sparse_vector(self.memory_text(memory))
            entries.append({
                "vector_id": self.vector_id(memory),
                "workspace_id": workspace_id,
                "memory_id": memory.get("memory_id"),
                "terms": sorted(vector.keys()),
                "vector": vector,
                "model": "local-sparse-keyword-v1",
                "created_at": now,
                "updated_at": now,
            })
        self.storage.write_list("memory_vectors.json", all_vectors + entries)
        return {
            "workspace_id": workspace_id,
            "indexed_memories": len(entries),
            "model": "local-sparse-keyword-v1",
            "updated_at": now,
        }

    def ensure_index(self, workspace_id: str) -> None:
        existing = [
            item for item in self.storage.read_list("memory_vectors.json")
            if item.get("workspace_id") == workspace_id
        ]
        active_memory_ids = {
            item.get("memory_id")
            for item in self.storage.read_list("workspace_memory.json")
            if item.get("workspace_id") == workspace_id and self.ensure_metadata(item).get("memory_tier") != "archived"
        }
        indexed_ids = {item.get("memory_id") for item in existing}
        if active_memory_ids != indexed_ids:
            self.rebuild_index(workspace_id)

    def index_summary(self, workspace_id: str) -> dict:
        entries = [
            item for item in self.storage.read_list("memory_vectors.json")
            if item.get("workspace_id") == workspace_id
        ]
        terms = Counter(term for entry in entries for term in entry.get("terms", []))
        return {
            "workspace_id": workspace_id,
            "indexed_memories": len(entries),
            "model": "local-sparse-keyword-v1",
            "top_terms": [{"term": term, "count": count} for term, count in terms.most_common(10)],
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
                    old_tier = memory.get("memory_tier", "warm")
                    memory["memory_tier"] = "archived"
                    memory["consolidated_into"] = keep_id
                    memory["archived_at"] = now
                    memory["updated_at"] = now
                    self.record_tier_transition(memory, old_tier, "archived", "consolidated duplicate")
                    archived.append(memory.get("memory_id"))
                    duplicate_tags.update(memory.get("tags") or [])
            for memory in memories:
                if memory.get("memory_id") == keep_id:
                    memory["tags"] = sorted(set(memory.get("tags") or []).union(duplicate_tags))
                    memory["updated_at"] = now
                    memory.update(self.score_memory(memory))
                    break
        self.storage.write_list("workspace_memory.json", memories)
        self.rebuild_index(workspace_id)
        return {"workspace_id": workspace_id, "applied": True, "archived_memory_ids": archived, "groups": preview["groups"]}

    def create_consolidation_job(self, workspace_id: str, apply: bool = False) -> dict:
        now = datetime.now(UTC).isoformat()
        preview = self.consolidation_preview(workspace_id)
        job = {
            "job_id": str(uuid4()),
            "workspace_id": workspace_id,
            "status": "running" if apply else "preview_ready",
            "mode": "apply" if apply else "preview",
            "duplicate_group_count": len(preview["groups"]),
            "candidate_memory_count": sum(len(group.get("duplicate_memory_ids", [])) for group in preview["groups"]),
            "groups": preview["groups"],
            "archived_memory_ids": [],
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
            "error": None,
        }
        if apply:
            try:
                result = self.consolidate(workspace_id, approved=True)
                job["status"] = "completed"
                job["archived_memory_ids"] = result.get("archived_memory_ids", [])
                job["groups"] = result.get("groups", preview["groups"])
                job["completed_at"] = datetime.now(UTC).isoformat()
                job["updated_at"] = job["completed_at"]
            except Exception as error:  # pragma: no cover - defensive job logging
                job["status"] = "failed"
                job["error"] = str(error)
                job["updated_at"] = datetime.now(UTC).isoformat()
        self.storage.append("memory_consolidation_jobs.json", job)
        return job

    def list_consolidation_jobs(self, workspace_id: str, limit: int = 20) -> list[dict]:
        jobs = [
            item
            for item in self.storage.read_list("memory_consolidation_jobs.json")
            if item.get("workspace_id") == workspace_id
        ]
        return sorted(jobs, key=lambda item: item.get("created_at") or "", reverse=True)[:limit]

    def get_consolidation_job(self, workspace_id: str, job_id: str) -> dict | None:
        return next(
            (
                item
                for item in self.storage.read_list("memory_consolidation_jobs.json")
                if item.get("workspace_id") == workspace_id and item.get("job_id") == job_id
            ),
            None,
        )

    def apply_consolidation_job(self, workspace_id: str, job_id: str) -> dict | None:
        jobs = self.storage.read_list("memory_consolidation_jobs.json")
        job = next((item for item in jobs if item.get("workspace_id") == workspace_id and item.get("job_id") == job_id), None)
        if job is None:
            return None
        if job.get("status") == "completed":
            return job
        now = datetime.now(UTC).isoformat()
        job["status"] = "running"
        job["updated_at"] = now
        try:
            result = self.consolidate(workspace_id, approved=True)
            job["status"] = "completed"
            job["archived_memory_ids"] = result.get("archived_memory_ids", [])
            job["groups"] = result.get("groups", job.get("groups", []))
            job["completed_at"] = datetime.now(UTC).isoformat()
            job["updated_at"] = job["completed_at"]
            job["error"] = None
        except Exception as error:  # pragma: no cover - defensive job logging
            job["status"] = "failed"
            job["error"] = str(error)
            job["updated_at"] = datetime.now(UTC).isoformat()
        self.storage.write_list("memory_consolidation_jobs.json", jobs)
        return job

    def archive_memory(self, workspace_id: str, memory_id: str, archived: bool = True) -> dict | None:
        memories = self.storage.read_list("workspace_memory.json")
        memory = next(
            (item for item in memories if item.get("workspace_id") == workspace_id and item.get("memory_id") == memory_id),
            None,
        )
        if memory is None:
            return None
        now = datetime.now(UTC).isoformat()
        old_tier = memory.get("memory_tier", "warm")
        memory["memory_tier"] = "archived" if archived else self.score_memory({**memory, "memory_tier": "warm"})["memory_tier"]
        memory["archived_at"] = now if archived else None
        memory["updated_at"] = now
        if not archived:
            memory.pop("consolidated_into", None)
        memory.update(self.score_memory(memory))
        self.record_tier_transition(memory, old_tier, memory.get("memory_tier"), "manual archive" if archived else "manual restore")
        self.storage.write_list("workspace_memory.json", memories)
        self.rebuild_index(workspace_id)
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
            "quality_recommendation",
            "semantic_terms",
            "memory_vector_id",
            "memory_tier",
            "tier_reason",
            "tier_history",
            "retention_action",
            "consolidated_into",
            "created_at",
            "updated_at",
        )
        return {key: enriched.get(key) for key in keys if key in enriched}

    def semantic_terms(self, memory: dict) -> list[str]:
        text = self.memory_text(memory)
        counts = Counter(self.token_list(text))
        ranked = sorted(counts.items(), key=lambda row: (-row[1], row[0]))
        return [term for term, _ in ranked[:18]]

    def memory_text(self, memory: dict) -> str:
        return f"{memory.get('title', '')} {memory.get('content', '')} {' '.join(memory.get('tags', []))}"

    def vector_id(self, memory: dict) -> str:
        return f"vec_{memory.get('memory_id') or uuid4()}"

    def sparse_vector(self, text: str) -> dict[str, float]:
        expanded = self.expand_query(text)
        tokens = self.token_list(expanded)
        counts = Counter(tokens)
        if not counts:
            return {}
        max_count = max(counts.values())
        return {
            token: round((count / max_count) * (1.0 + min(len(token), 12) / 20), 4)
            for token, count in sorted(counts.items())
        }

    def cosine_similarity(self, left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        shared = set(left).intersection(right)
        dot = sum(left[token] * right[token] for token in shared)
        left_norm = sqrt(sum(value * value for value in left.values()))
        right_norm = sqrt(sum(value * value for value in right.values()))
        if not left_norm or not right_norm:
            return 0.0
        return dot / (left_norm * right_norm)

    def expand_query(self, text: str) -> str:
        synonyms = {
            "backend": "api server fastapi python service route",
            "frontend": "react ui interface component client",
            "resume": "cv job internship application",
            "test": "pytest build validation quality",
            "tests": "pytest build validation quality",
            "bug": "error issue fix failure",
            "memory": "context recall knowledge preference",
            "recording": "audio transcript meeting lecture",
            "automation": "workflow approval command file edit",
        }
        terms = self.token_list(text)
        additions = " ".join(synonyms.get(term, "") for term in terms)
        return f"{text} {additions}".strip()

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

    def age_days(self, timestamp: str | None) -> float:
        if not timestamp:
            return 0.0
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return 0.0
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return max((datetime.now(UTC) - parsed).total_seconds() / 86400, 0)

    def quality_recommendation(self, memory: dict, score: float, reasons: list[str]) -> str:
        if score >= 80:
            return "Keep as strong workspace context."
        if memory.get("pinned"):
            return "Pinned memory should stay visible; refresh content if it becomes stale."
        if "thin content" in reasons:
            return "Add more specific project details or archive this memory."
        if score < 45:
            return "Review for usefulness; archive if it no longer guides current work."
        return "Keep available, but let usage and recency decide future tier changes."

    def recommended_actions(self, memories: list[dict]) -> list[dict]:
        actions = []
        for memory in memories:
            if memory.get("retention_action") in {"archive", "review"} or (
                memory.get("memory_tier") == "archived" and float(memory.get("quality_score") or 0) < 45
            ):
                actions.append({
                    "memory_id": memory.get("memory_id"),
                    "title": memory.get("title"),
                    "action": memory.get("retention_action") or "review",
                    "reason": memory.get("tier_reason"),
                    "quality_score": memory.get("quality_score"),
                })
        return sorted(actions, key=lambda item: item.get("quality_score") or 0)[:8]

    def record_tier_transition(self, memory: dict, old_tier: str | None, new_tier: str | None, reason: str | None) -> None:
        old_tier = old_tier or "warm"
        new_tier = new_tier or "warm"
        if old_tier == new_tier:
            return
        history = list(memory.get("tier_history") or [])
        history.append({
            "from": old_tier,
            "to": new_tier,
            "reason": reason or "tier rule update",
            "created_at": datetime.now(UTC).isoformat(),
        })
        memory["tier_history"] = history[-10:]
