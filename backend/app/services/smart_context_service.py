from __future__ import annotations

import re
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Candidate sources for context (label → collection, text fields).
CONTEXT_SOURCES = [
    {"kind": "memory", "file": "workspace_memory.json", "text_keys": ["title", "content", "value"]},
    {"kind": "file", "file": "files.json", "text_keys": ["filename", "summary", "extracted_text_preview"]},
    {"kind": "goal", "file": "goals.json", "text_keys": ["title", "description"]},
]

# Sensitive-content patterns → items matching these are filtered out (never included in context).
_SENSITIVE_PATTERNS = [
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "email"),
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "card-like number"),
    (re.compile(r"(sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{10,}|AKIA[0-9A-Z]{12,})"), "api-key-like token"),
    (re.compile(r"(?i)\b(password|secret|api[_-]?key|token)\b\s*[:=]"), "secret assignment"),
]

DEFAULT_BUDGET_CHARS = 4000


class SmartContextService:
    """v71.0 Smart Context Engine — better context selection before every answer.

    A read-only **context planner**: given a query and workspace, it scores candidate
    memory / files / goals by keyword overlap, gives a **selection reason** per item,
    enforces a **context budget** (character cap), removes **duplicate** context, and
    **filters out sensitive content** (emails, card-like numbers, key-like tokens,
    secret assignments) so it never enters the context. It returns a Developer-Mode
    **context trace** of what was included and what was excluded and why. It does not
    change the run pipeline — it previews/plans the context. Governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return [t for t in re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).split() if len(t) > 2]

    @staticmethod
    def _blob(item: dict, keys: list[str]) -> str:
        parts = [str(item[k]) for k in keys if item.get(k) not in (None, "", [], {})]
        return " ".join(parts)

    @staticmethod
    def _sensitive(text: str) -> str | None:
        for pattern, label in _SENSITIVE_PATTERNS:
            if pattern.search(text or ""):
                return label
        return None

    def plan(self, query: str, workspace_id: str | None = None, budget_chars: int = DEFAULT_BUDGET_CHARS) -> dict:
        query = (query or "").strip()
        terms = set(self._tokens(query))
        budget_chars = max(200, min(int(budget_chars or DEFAULT_BUDGET_CHARS), 20000))

        candidates = []
        for source in CONTEXT_SOURCES:
            for item in self.storage.read_list(source["file"]):
                if not isinstance(item, dict):
                    continue
                if workspace_id and item.get("workspace_id") not in (None, workspace_id):
                    continue
                text = self._blob(item, source["text_keys"]).strip()
                if not text:
                    continue
                item_terms = set(self._tokens(text))
                overlap = terms & item_terms
                score = len(overlap)
                candidates.append({
                    "kind": source["kind"],
                    "text": text,
                    "chars": len(text),
                    "score": score,
                    "matched_terms": sorted(overlap)[:6],
                })

        candidates.sort(key=lambda c: c["score"], reverse=True)

        selected, excluded = [], []
        used_chars = 0
        seen_fingerprints: set[str] = set()
        for cand in candidates:
            sensitive = self._sensitive(cand["text"])
            if sensitive:
                excluded.append({**self._preview(cand), "reason": f"sensitive content filtered ({sensitive})"})
                continue
            fingerprint = " ".join(sorted(self._tokens(cand["text"]))[:40])
            if fingerprint in seen_fingerprints:
                excluded.append({**self._preview(cand), "reason": "duplicate context removed"})
                continue
            if cand["score"] == 0:
                excluded.append({**self._preview(cand), "reason": "no keyword overlap with the query"})
                continue
            if used_chars + cand["chars"] > budget_chars:
                excluded.append({**self._preview(cand), "reason": "over context budget"})
                continue
            seen_fingerprints.add(fingerprint)
            used_chars += cand["chars"]
            selected.append({**self._preview(cand), "reason": f"matched {cand['score']} term(s): {', '.join(cand['matched_terms']) or 'relevant'}"})

        self.governance.log_event(
            GovernanceEvent(
                task_type="smart_context",
                agent_name="Smart Context Engine",
                action_type="context_planned",
                tool_used="SmartContextService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=f"Planned context: {len(selected)} selected / {len(excluded)} excluded within {budget_chars} char budget.",
            )
        )
        return {
            "query": query,
            "budget_chars": budget_chars,
            "used_chars": used_chars,
            "selected": selected,
            "excluded": excluded[:30],
            "selected_count": len(selected),
            "excluded_count": len(excluded),
            "note": "Read-only context plan — sensitive content is filtered out and never included; nothing is executed.",
        }

    @staticmethod
    def _preview(cand: dict) -> dict:
        return {"kind": cand["kind"], "chars": cand["chars"], "score": cand["score"], "preview": cand["text"][:160]}

    def analytics_summary(self) -> dict:
        return {"smart_context_sources": len(CONTEXT_SOURCES)}

    def summary(self) -> dict:
        return {
            "context_sources": [s["kind"] for s in CONTEXT_SOURCES],
            "default_budget_chars": DEFAULT_BUDGET_CHARS,
            "sensitive_filters": [label for _, label in _SENSITIVE_PATTERNS],
            "note": "Smart Context Engine plans context selection with reasons, budget, dedup, and sensitive filtering.",
        }
