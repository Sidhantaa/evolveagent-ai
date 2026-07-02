from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "was", "were", "it", "this", "that", "with", "as", "by", "at", "be", "from",
}
_CHUNK_TARGET = 400  # characters per chunk (approximate; split on sentence bounds)
_MAX_CHUNKS = 200


def _tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", (text or "").lower()) if w not in _STOPWORDS and len(w) > 1]


class LocalRetrievalService:
    """v51.0 Local Retrieval Layer (local-only grounding).

    Deepens the v6 memory work: it chunks workspace documents locally and answers
    queries by keyword-overlap scoring, returning the best-matching chunks with a
    source citation. It uses the standard library only — **no external vector
    database and no network** — mirroring the project's local-first stance.
    Indexing and queries are governance-logged.
    """

    documents_file = "retrieval_documents.json"
    queries_file = "retrieval_queries.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="local_retrieval",
                agent_name="Local Retrieval Layer",
                action_type=action_type,
                tool_used="LocalRetrievalService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=3,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Chunking + indexing
    # ------------------------------------------------------------------
    def _chunk(self, content: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", content.strip())
        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            if not sentence:
                continue
            if len(current) + len(sentence) + 1 > _CHUNK_TARGET and current:
                chunks.append(current.strip())
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
            if len(chunks) >= _MAX_CHUNKS:
                break
        if current and len(chunks) < _MAX_CHUNKS:
            chunks.append(current.strip())
        return chunks or ([content.strip()] if content.strip() else [])

    def index_document(self, data: dict) -> dict:
        data = data or {}
        content = self._clean(data.get("content"), 40000)
        title = self._clean(data.get("title"), 200) or "Untitled document"
        workspace_id = self._clean(data.get("workspace_id"), 120) or "default"
        chunk_texts = self._chunk(content)
        doc = {
            "doc_id": str(uuid4()),
            "workspace_id": workspace_id,
            "title": title,
            "chunk_count": len(chunk_texts),
            "chunks": [
                {"chunk_index": i, "text": text, "tokens": sorted(set(_tokens(text)))}
                for i, text in enumerate(chunk_texts)
            ],
            "created_at": self._now(),
        }
        self.storage.append(self.documents_file, doc)
        self._log("retrieval_document_indexed", f"Indexed '{title}' into {len(chunk_texts)} chunk(s).")
        # Return a light view without token lists.
        return {
            "doc_id": doc["doc_id"],
            "workspace_id": workspace_id,
            "title": title,
            "chunk_count": doc["chunk_count"],
            "created_at": doc["created_at"],
        }

    def list_documents(self, workspace_id: str | None = None) -> list[dict]:
        docs = self.storage.read_list(self.documents_file)
        if workspace_id:
            docs = [d for d in docs if d.get("workspace_id") == workspace_id]
        return [
            {"doc_id": d["doc_id"], "workspace_id": d.get("workspace_id"), "title": d.get("title"), "chunk_count": d.get("chunk_count"), "created_at": d.get("created_at")}
            for d in docs
        ]

    # ------------------------------------------------------------------
    # Query (keyword-overlap scoring; local only)
    # ------------------------------------------------------------------
    def query(self, data: dict) -> dict:
        data = data or {}
        query_text = self._clean(data.get("query"), 2000)
        workspace_id = self._clean(data.get("workspace_id"), 120) or None
        top_k = max(1, min(10, int(data.get("top_k") or 3))) if str(data.get("top_k") or "").strip().isdigit() else 3
        q_tokens = set(_tokens(query_text))
        results: list[dict] = []
        docs = self.storage.read_list(self.documents_file)
        for doc in docs:
            if workspace_id and doc.get("workspace_id") != workspace_id:
                continue
            for chunk in doc.get("chunks", []):
                chunk_tokens = set(chunk.get("tokens", []))
                if not chunk_tokens or not q_tokens:
                    continue
                overlap = len(q_tokens & chunk_tokens)
                if overlap == 0:
                    continue
                score = round(overlap / len(q_tokens), 4)
                results.append({
                    "doc_id": doc["doc_id"],
                    "title": doc.get("title"),
                    "chunk_index": chunk.get("chunk_index"),
                    "score": score,
                    "matched_terms": sorted(q_tokens & chunk_tokens),
                    "text": chunk.get("text"),
                    "citation": f"{doc.get('title')} #chunk-{chunk.get('chunk_index')}",
                })
        results.sort(key=lambda r: r["score"], reverse=True)
        top = results[:top_k]
        record = {
            "query_id": str(uuid4()),
            "query": query_text,
            "workspace_id": workspace_id,
            "result_count": len(top),
            "created_at": self._now(),
        }
        self.storage.append(self.queries_file, record)
        self._log("retrieval_query", f"Query '{query_text[:60]}' → {len(top)} result(s).")
        return {
            "query": query_text,
            "results": top,
            "result_count": len(top),
            "note": "Local keyword-overlap retrieval — no external vector database or network call.",
        }

    # ------------------------------------------------------------------
    # Summary + analytics
    # ------------------------------------------------------------------
    def summary(self, workspace_id: str | None = None) -> dict:
        docs = self.list_documents(workspace_id)
        return {
            "document_count": len(docs),
            "chunk_count": sum(d["chunk_count"] for d in docs),
            "query_count": len(self.storage.read_list(self.queries_file)),
            "note": "Local-first retrieval — chunks and scores computed locally; no external vector DB.",
        }

    def analytics_summary(self) -> dict:
        docs = self.storage.read_list(self.documents_file)
        return {
            "retrieval_documents": len(docs),
            "retrieval_chunks": sum(d.get("chunk_count", 0) for d in docs),
            "retrieval_queries": len(self.storage.read_list(self.queries_file)),
        }
