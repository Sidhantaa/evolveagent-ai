"""Memory v2 — semantic memory with pgvector, keyword fallback.

Real vector-search infrastructure: store text with an embedding and retrieve by
cosine similarity. Runs in two modes, chosen automatically:

* **pgvector** — when a Postgres URL is available (the app is on Postgres): a
  ``memory_embeddings`` table with a ``vector(1536)`` column, exact cosine search.
* **keyword** — otherwise: items live in a JSON collection via ``StorageService``
  and are scored by token overlap (the safe local fallback).

Embeddings are produced **mock-safe by default** with a deterministic local
embedder (no network, no key), so the pipeline is fully testable offline. When
``OPENAI_API_KEY`` is set and ``MEMORY_EMBEDDINGS=openai``, real OpenAI embeddings
are used instead — same 1536 dims, so the schema is unchanged. Governance-logged.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from datetime import UTC, datetime
from uuid import uuid4

from app.config import settings
from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

DIM = 1536
_ITEMS_FILE = "memory_v2_items.json"
_SCHEMA = [
    "CREATE EXTENSION IF NOT EXISTS vector",
    f"""
    CREATE TABLE IF NOT EXISTS memory_embeddings (
        id text PRIMARY KEY,
        kind text,
        text text,
        source text,
        metadata jsonb,
        embedding vector({DIM}),
        created_at timestamptz DEFAULT now()
    )
    """,
]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def local_embed(text: str) -> list[float]:
    """Deterministic, offline embedding: hashed bag-of-tokens, L2-normalized."""
    vec = [0.0] * DIM
    for tok in _tokens(text):
        idx = int(hashlib.md5(tok.encode()).hexdigest(), 16) % DIM
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class MemoryService:
    def __init__(self, storage: StorageService, governance_service: GovernanceService, database_url: str | None = None):
        self.storage = storage
        self.governance = governance_service
        self.database_url = database_url or (
            settings.database_url if settings.storage_backend.lower() == "postgres" else None
        )
        self._engine = None
        if self.database_url:
            from sqlalchemy import create_engine
            from app.storage.postgres_backend import to_sync_url
            self._engine = create_engine(to_sync_url(self.database_url), pool_pre_ping=True, future=True)
            self._init_schema()

    @property
    def mode(self) -> str:
        return "pgvector" if self._engine is not None else "keyword"

    def _init_schema(self) -> None:
        from sqlalchemy import text
        with self._engine.begin() as conn:  # type: ignore[union-attr]
            for stmt in _SCHEMA:
                conn.execute(text(stmt))

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(GovernanceEvent(
            task_type="memory_v2", agent_name="Memory v2", action_type=action_type,
            tool_used="MemoryService", permission_level="read_only", approved=True,
            blocked=False, risk_score=1, reason=reason,
        ))

    # -- embedding -----------------------------------------------------------
    def _use_openai(self) -> bool:
        return bool(settings.openai_api_key) and os.environ.get("MEMORY_EMBEDDINGS", "local") == "openai"

    def embed(self, text: str) -> list[float]:
        if self._use_openai():
            try:
                from openai import OpenAI
                client = OpenAI(api_key=settings.openai_api_key)
                resp = client.embeddings.create(model="text-embedding-3-small", input=text[:8000])
                return list(resp.data[0].embedding)
            except Exception:
                pass  # fall back to local on any failure
        return local_embed(text)

    @staticmethod
    def _vec_literal(vec: list[float]) -> str:
        return "[" + ",".join(f"{v:.6f}" for v in vec) + "]"

    # -- write ---------------------------------------------------------------
    def add(self, text: str, kind: str = "note", source: str = "manual", metadata: dict | None = None) -> dict:
        text = str(text or "").strip()
        if not text:
            raise ValueError("text is required")
        item_id = str(uuid4())
        metadata = {str(k)[:40]: str(v)[:200] for k, v in (metadata or {}).items()}
        vec = self.embed(text)
        if self.mode == "pgvector":
            import json as _json
            from sqlalchemy import text as sql
            with self._engine.begin() as conn:  # type: ignore[union-attr]
                conn.execute(
                    sql("INSERT INTO memory_embeddings (id, kind, text, source, metadata, embedding) "
                        "VALUES (:id, :k, :t, :s, CAST(:m AS jsonb), CAST(:e AS vector))"),
                    {"id": item_id, "k": kind, "t": text[:4000], "s": source, "m": _json.dumps(metadata), "e": self._vec_literal(vec)},
                )
        else:
            items = self.storage.read_list(_ITEMS_FILE)
            items.append({"id": item_id, "kind": kind, "text": text[:4000], "source": source,
                          "metadata": metadata, "tokens": _tokens(text), "created_at": self._now()})
            self.storage.write_list(_ITEMS_FILE, items)
        self._log("memory_added", f"Added a memory ({self.mode}, kind={kind})")
        return {"id": item_id, "kind": kind, "mode": self.mode}

    # -- search --------------------------------------------------------------
    def search(self, query: str, limit: int = 5, workspace_id: str | None = None) -> dict:
        query = str(query or "").strip()
        try:
            limit = max(1, min(50, int(limit)))
        except (TypeError, ValueError):
            limit = 5
        if not query:
            return {"query": query, "results": [], "count": 0, "mode": self.mode}

        results: list[dict] = []
        if self.mode == "pgvector":
            from sqlalchemy import text as sql
            qv = self._vec_literal(self.embed(query))
            where = " AND metadata->>'workspace_id' = :wsid" if workspace_id else ""
            params = {"q": qv, "n": limit}
            if workspace_id:
                params["wsid"] = workspace_id
            with self._engine.connect() as conn:  # type: ignore[union-attr]
                rows = conn.execute(
                    sql("SELECT id, kind, text, source, metadata, "
                        "1 - (embedding <=> CAST(:q AS vector)) AS score "
                        f"FROM memory_embeddings WHERE true{where} "
                        "ORDER BY embedding <=> CAST(:q AS vector) LIMIT :n"),
                    params,
                ).fetchall()
            results = [{"id": r[0], "kind": r[1], "text": r[2], "source": r[3],
                        "metadata": r[4], "score": round(float(r[5]), 4)} for r in rows]
        else:
            qtokens = set(_tokens(query))
            scored = []
            for it in self.storage.read_list(_ITEMS_FILE):
                if workspace_id and it.get("metadata", {}).get("workspace_id") != workspace_id:
                    continue
                overlap = len(qtokens & set(it.get("tokens", [])))
                if overlap:
                    denom = len(qtokens) or 1
                    scored.append((overlap / denom, it))
            scored.sort(key=lambda x: x[0], reverse=True)
            results = [{"id": it["id"], "kind": it["kind"], "text": it["text"], "source": it["source"],
                        "metadata": it.get("metadata", {}), "score": round(s, 4)} for s, it in scored[:limit]]

        self._log("memory_search", f"Searched memory ({self.mode}) -> {len(results)} hits")
        return {"query": query, "results": results, "count": len(results), "mode": self.mode}

    # -- status / analytics --------------------------------------------------
    def count(self) -> int:
        if self.mode == "pgvector":
            from sqlalchemy import text as sql
            with self._engine.connect() as conn:  # type: ignore[union-attr]
                return int(conn.execute(sql("SELECT count(*) FROM memory_embeddings")).scalar() or 0)
        return len(self.storage.read_list(_ITEMS_FILE))

    def status(self) -> dict:
        return {
            "available": True,
            "mode": self.mode,
            "embedder": "openai" if self._use_openai() else "local",
            "dimensions": DIM,
            "items": self.count(),
            "note": "Semantic memory via pgvector when on Postgres; keyword fallback otherwise. "
                    "Embeddings are local/deterministic unless OPENAI_API_KEY + MEMORY_EMBEDDINGS=openai.",
        }

    def analytics_summary(self) -> dict:
        return {"memory_v2_items": self.count(), "memory_v2_mode": self.mode}
