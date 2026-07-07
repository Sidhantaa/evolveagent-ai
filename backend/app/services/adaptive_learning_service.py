from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, datetime
from hashlib import sha1
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

KINDS = ("topic", "reference", "example", "action")
_STOP = {"the", "and", "for", "with", "that", "this", "you", "your", "are", "was", "how", "what", "into", "from"}


def _tokens(text: str) -> set[str]:
    return {t for t in re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).split() if len(t) > 2 and t not in _STOP}


class AdaptiveLearningService:
    """Safe, self-improving **retrieval memory** — NOT base-model training.

    Learns from usage history and repo data by curating a ranked knowledge store,
    then augments future answers with the most relevant learned context and
    few-shot examples (a RAG / few-shot pattern). This is the safe form of
    "personalization" the product allows: **configuration + retrieval + memory +
    examples + preference feedback**. It never fine-tunes or retrains any model's
    weights, and it stores no secrets.

    ``learn()`` auto-ingests recent signals from other local stores:
    repo searches → topics/references, high-grade agent evaluations → few-shot
    examples, workflow effects → action patterns. Everything is local, reversible
    (items can be forgotten), and governance-logged.
    """

    items_file = "adaptive_learning_items.json"
    # Source stores it learns from (read-only).
    _repo_searches = "repo_finder_searches.json"
    _agents = "agent_profiles.json"
    _effects = "durable_workflow_effects.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, memory=None):
        self.storage = storage
        self.governance = governance_service
        # Optional MemoryService (Memory v2). When present and in pgvector mode,
        # recommend() upgrades from keyword overlap to semantic search.
        self.memory = memory

    def _semantic(self) -> bool:
        return self.memory is not None and getattr(self.memory, "mode", "keyword") == "pgvector"

    def _mirror(self, kind: str, text: str, source: str, fingerprint: str) -> None:
        """Best-effort: mirror a NEW learned item into Memory v2 for semantic recall."""
        if self.memory is None:
            return
        try:
            self.memory.add(
                text,
                kind=kind,
                source="adaptive_learning",
                metadata={"fingerprint": fingerprint, "origin": source},
            )
        except Exception:
            pass  # mirroring must never break learning

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="adaptive_learning",
                agent_name="Adaptive Learning",
                action_type=action_type,
                tool_used="AdaptiveLearningService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def status(self) -> dict:
        return {
            "available": True,
            "method": "retrieval_memory_and_few_shot",
            "trains_base_model": False,
            "recall_engine": "semantic" if self._semantic() else "keyword",
            "kinds": list(KINDS),
            "note": (
                "Self-improving retrieval memory (RAG + few-shot). Learns from your history and "
                "repo data to surface relevant context — it does NOT fine-tune or retrain any model, "
                "and stores no secrets. Fully local and reversible."
            ),
        }

    # -- storage helpers -----------------------------------------------------
    def _all(self) -> list[dict]:
        return self.storage.read_list(self.items_file)

    @staticmethod
    def _fingerprint(kind: str, text: str) -> str:
        return sha1(f"{kind}:{text.strip().lower()}".encode()).hexdigest()[:16]

    def _upsert(self, items: list[dict], kind: str, text: str, source: str) -> bool:
        """Add or reinforce an item. Returns True if newly added."""
        text = str(text or "").strip()[:500]
        if not text or kind not in KINDS:
            return False
        fp = self._fingerprint(kind, text)
        for it in items:
            if it.get("fingerprint") == fp:
                it["weight"] = it.get("weight", 1) + 1  # reinforcement
                it["updated_at"] = self._now()
                return False
        items.append({
            "id": str(uuid4()), "fingerprint": fp, "kind": kind, "text": text,
            "source": str(source or "manual")[:60], "weight": 1,
            "created_at": self._now(), "updated_at": self._now(),
        })
        self._mirror(kind, text, source, fp)
        return True

    # -- learning ------------------------------------------------------------
    def learn(self) -> dict:
        items = self._all()
        added = 0

        # 1) Repo searches -> topics + references.
        for row in self.storage.read_list(self._repo_searches):
            q = row.get("query", "")
            if q:
                added += self._upsert(items, "topic", q, "repo_finder")
            top = row.get("top", "")
            if top:
                added += self._upsert(items, "reference", f"GitHub repo {top} (for: {q})", "repo_finder")

        # 2) High-grade agent examples -> few-shot memory.
        for a in self.storage.read_list(self._agents):
            grade = (a.get("evaluation") or {}).get("grade")
            if grade in ("A", "B"):
                for e in (a.get("examples") or [])[:5]:
                    out = str(e.get("output", "")).strip()
                    if out:
                        added += self._upsert(items, "example", f"{e.get('input','')} -> {out}", f"agent:{a.get('name','')}")

        # 3) Workflow effects -> action patterns.
        for e in self.storage.read_list(self._effects):
            at = e.get("action_type", "")
            label = (e.get("params") or {}).get("title") or (e.get("params") or {}).get("message") or ""
            if at:
                added += self._upsert(items, "action", f"{at}: {label}".strip(": "), "durable_workflow")

        self.storage.write_list(self.items_file, items)
        self._log("adaptive_learned", f"Auto-learned from history: +{added} new items ({len(items)} total)")
        return {"ingested": added, "total": len(items), "by_kind": self._by_kind(items),
                "note": "Retrieval memory updated — no model was trained."}

    def ingest(self, text: str, kind: str = "topic", source: str = "manual") -> dict:
        items = self._all()
        if not self._upsert(items, kind, text, source):
            # either invalid or reinforced an existing item
            if kind not in KINDS or not str(text or "").strip():
                raise ValueError(f"invalid item (kind must be one of {KINDS} and text non-empty)")
        self.storage.write_list(self.items_file, items)
        self._log("adaptive_ingested", f"Ingested a {kind} item into learning memory")
        return {"total": len(items), "by_kind": self._by_kind(items)}

    def _recommend_semantic(self, query: str, limit: int) -> list[dict] | None:
        """Semantic recall via Memory v2 (pgvector). Returns None to signal fallback."""
        try:
            hits = self.memory.search(query, limit * 4)  # over-fetch, then filter to our items
        except Exception:
            return None
        by_fp = {it.get("fingerprint"): it for it in self._all()}
        recs: list[dict] = []
        for h in hits.get("results", []):
            meta = h.get("metadata") or {}
            if h.get("source") != "adaptive_learning":
                continue
            it = by_fp.get(meta.get("fingerprint"))
            if not it:
                continue
            recs.append({"kind": it["kind"], "text": it["text"], "source": it["source"],
                         "weight": it.get("weight", 1), "match": h.get("score", 0)})
            if len(recs) >= limit:
                break
        return recs or None  # empty -> let keyword fallback try

    def recommend(self, query: str, limit: int = 5) -> dict:
        q_tokens = _tokens(query)
        if not q_tokens:
            return {"query": query, "recommendations": [], "count": 0, "engine": "keyword",
                    "note": "Relevant learned context is retrieved and added to answers — not model training."}
        try:
            limit = max(1, min(20, int(limit)))
        except (TypeError, ValueError):
            limit = 5

        engine = "keyword"
        recs: list[dict] | None = None
        if self._semantic():
            recs = self._recommend_semantic(query, limit)
            if recs is not None:
                engine = "semantic"
        if recs is None:
            scored = []
            for it in self._all():
                overlap = len(q_tokens & _tokens(it["text"]))
                if overlap:
                    # rank by keyword overlap, tie-broken by reinforcement weight
                    scored.append((overlap, it.get("weight", 1), it))
            scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
            recs = [{"kind": it["kind"], "text": it["text"], "source": it["source"],
                     "weight": it.get("weight", 1), "match": ov} for ov, _, it in scored[:limit]]
        self._log("adaptive_recommend", f"Retrieved {len(recs)} learned items ({engine})")
        return {"query": query, "recommendations": recs, "count": len(recs), "engine": engine,
                "note": "Relevant learned context is retrieved to augment answers — not model training."}

    def items(self, kind: str | None = None, limit: int = 50) -> dict:
        rows = self._all()
        if kind in KINDS:
            rows = [r for r in rows if r.get("kind") == kind]
        rows = sorted(rows, key=lambda r: (r.get("weight", 1), r.get("updated_at", "")), reverse=True)
        try:
            limit = max(1, min(200, int(limit)))
        except (TypeError, ValueError):
            limit = 50
        return {"items": rows[:limit], "count": len(rows), "by_kind": self._by_kind(self._all())}

    def forget(self, item_id: str) -> dict:
        rows = self._all()
        kept = [r for r in rows if r.get("id") != item_id]
        if len(kept) == len(rows):
            raise ValueError("item not found")
        self.storage.write_list(self.items_file, kept)
        self._log("adaptive_forgot", "Removed an item from learning memory")
        return {"removed": item_id, "total": len(kept)}

    @staticmethod
    def _by_kind(items: list[dict]) -> dict:
        c: Counter = Counter(it.get("kind", "unknown") for it in items)
        return dict(c)

    def analytics_summary(self) -> dict:
        items = self._all()
        return {"adaptive_learning_items": len(items),
                "adaptive_learning_weight": sum(it.get("weight", 1) for it in items)}

    def summary(self) -> dict:
        return {**self.status(), **self.analytics_summary(), "by_kind": self._by_kind(self._all())}
