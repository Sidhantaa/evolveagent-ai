from __future__ import annotations

import re
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Loaded / absolute language that may signal bias — flagged, not judged.
_BIAS_TERMS = ["always", "never", "everyone", "no one", "obviously", "clearly", "undeniable",
               "guaranteed", "proven fact", "everybody knows", "worst", "best ever", "impossible"]
_NEGATION = re.compile(r"\b(not|no|never|isn't|aren't|doesn't|don't|cannot|can't|won't)\b", re.IGNORECASE)
_CITATION_SIGNALS = [
    (re.compile(r"https?://"), "url"),
    (re.compile(r"\b(19|20)\d{2}\b"), "year"),
    (re.compile(r"\bet al\.?|\baccording to\b|\bsource:", re.IGNORECASE), "attribution"),
    (re.compile(r"\bdoi:|\bisbn", re.IGNORECASE), "identifier"),
]


class ResearchAgentService:
    """v77.0 Research Agent 2.0 — stronger evidence-based research (deterministic, local).

    Read-only, mock-safe research tools over sources you pass in: **source comparison**
    (pairwise term overlap), a **claim/evidence table** (claim-like vs evidence-bearing
    sentences), **contradiction detection** (shared-subject sentences differing in
    negation), a **citation quality score** (presence of urls/years/attribution/ids), a
    **research brief generator** (structured markdown), and **bias/risk flags** (loaded
    language). It never browses the web or calls a model. Governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {t for t in re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).split() if len(t) > 3}

    @staticmethod
    def _sentences(text: str) -> list[str]:
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if len(s.strip()) > 10]

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="research_agent",
                agent_name="Research Agent",
                action_type=action_type,
                tool_used="ResearchAgentService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    @staticmethod
    def _norm_sources(sources: list[dict]) -> list[dict]:
        out = []
        for i, s in enumerate(sources or []):
            if isinstance(s, dict):
                out.append({"title": str(s.get("title") or f"Source {i + 1}")[:120], "text": str(s.get("text") or "")})
        return out

    def compare_sources(self, sources: list[dict]) -> dict:
        srcs = self._norm_sources(sources)
        pairs = []
        for i in range(len(srcs)):
            for j in range(i + 1, len(srcs)):
                a, b = self._tokens(srcs[i]["text"]), self._tokens(srcs[j]["text"])
                union = a | b
                sim = round(len(a & b) / len(union), 3) if union else 0.0
                pairs.append({"a": srcs[i]["title"], "b": srcs[j]["title"], "similarity": sim,
                              "agreement": "high" if sim > 0.5 else "medium" if sim > 0.2 else "low"})
        self._log("research_sources_compared", f"Compared {len(srcs)} source(s).")
        return {"source_count": len(srcs), "pairs": pairs}

    def claim_evidence(self, text: str) -> dict:
        rows = []
        for sentence in self._sentences(text):
            has_number = bool(re.search(r"\d", sentence))
            has_citation = any(p.search(sentence) for p, _ in _CITATION_SIGNALS)
            kind = "evidence" if (has_number or has_citation) else "claim"
            rows.append({"statement": sentence[:200], "type": kind,
                         "supported": has_citation or has_number})
        self._log("research_claims_extracted", f"Extracted {len(rows)} claim/evidence row(s).")
        return {"rows": rows[:50], "claim_count": sum(1 for r in rows if r["type"] == "claim"),
                "evidence_count": sum(1 for r in rows if r["type"] == "evidence")}

    def detect_contradictions(self, sources: list[dict]) -> dict:
        srcs = self._norm_sources(sources)
        sentences = []
        for s in srcs:
            for sent in self._sentences(s["text"]):
                sentences.append((s["title"], sent))
        contradictions = []
        for i in range(len(sentences)):
            for j in range(i + 1, len(sentences)):
                ti, si = sentences[i]
                tj, sj = sentences[j]
                shared = self._tokens(si) & self._tokens(sj)
                if len(shared) >= 2 and (bool(_NEGATION.search(si)) != bool(_NEGATION.search(sj))):
                    contradictions.append({"source_a": ti, "source_b": tj,
                                           "statement_a": si[:160], "statement_b": sj[:160], "shared_terms": sorted(shared)[:5]})
        self._log("research_contradictions", f"Detected {len(contradictions)} potential contradiction(s).")
        return {"contradictions": contradictions[:20], "count": len(contradictions),
                "note": "Heuristic (shared subject + differing negation) — review before relying on it."}

    def citation_quality(self, sources: list[dict]) -> dict:
        srcs = self._norm_sources(sources)
        rows = []
        for s in srcs:
            signals = sorted({label for pattern, label in _CITATION_SIGNALS if pattern.search(s["text"])})
            score = round((len(signals) / len(_CITATION_SIGNALS)) * 100)
            rows.append({"title": s["title"], "signals": signals, "score": score,
                         "quality": "strong" if score >= 75 else "adequate" if score >= 50 else "weak"})
        avg = round(sum(r["score"] for r in rows) / len(rows)) if rows else 0
        self._log("research_citation_quality", f"Scored citation quality for {len(rows)} source(s).")
        return {"rows": rows, "average_score": avg}

    def bias_flags(self, text: str) -> dict:
        lower = (text or "").lower()
        flags = [term for term in _BIAS_TERMS if term in lower]
        self._log("research_bias_flags", f"Flagged {len(flags)} loaded-language term(s).")
        return {"flags": flags, "count": len(flags),
                "risk": "high" if len(flags) >= 4 else "medium" if flags else "low",
                "note": "Flags loaded/absolute language — not a judgment of accuracy."}

    def brief(self, topic: str, sources: list[dict]) -> dict:
        srcs = self._norm_sources(sources)
        citation = self.citation_quality(sources)
        contradictions = self.detect_contradictions(sources)
        lines = [f"# Research Brief: {topic}", "", f"_Generated {self._now()} · {len(srcs)} source(s)_", "",
                 "## Sources"]
        for s, row in zip(srcs, citation["rows"]):
            lines.append(f"- **{s['title']}** — citation quality: {row['quality']} ({row['score']})")
        lines += ["", "## Signals",
                  f"- Average citation quality: {citation['average_score']}/100",
                  f"- Potential contradictions: {contradictions['count']}", "",
                  "## Caveats", "- Deterministic, local synthesis — verify claims against primary sources.",
                  "- This is not web research and makes no external calls."]
        self._log("research_brief_generated", f"Generated a research brief for '{topic[:60]}'.")
        return {"topic": topic, "format": "markdown", "content": "\n".join(lines),
                "average_citation_quality": citation["average_score"], "contradiction_count": contradictions["count"]}

    def analytics_summary(self) -> dict:
        return {"research_agent_capabilities": 6}

    def summary(self) -> dict:
        return {
            "capabilities": ["compare_sources", "claim_evidence", "detect_contradictions",
                             "citation_quality", "brief", "bias_flags"],
            "note": "Deterministic, local, read-only research toolkit — no web browsing, no model calls.",
        }
