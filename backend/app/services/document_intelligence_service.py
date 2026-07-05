from __future__ import annotations

import re
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Contract clauses worth flagging (label → keywords).
_CONTRACT_RISKS = {
    "auto-renewal": ["auto-renew", "automatically renew", "renewal term"],
    "liability": ["liability", "indemnify", "indemnification", "hold harmless"],
    "termination": ["termination", "terminate", "for cause", "without cause"],
    "non-compete": ["non-compete", "noncompete", "restrictive covenant"],
    "confidentiality": ["confidential", "non-disclosure", "nda"],
    "penalty": ["penalty", "liquidated damages", "late fee"],
}


class DocumentIntelligenceService:
    """v75.0 Document Intelligence 2.0 — stronger document work (deterministic, local).

    A read-only, mock-safe document toolkit that operates on text you pass in:
    **document comparison** (overlap + unique terms), **resume ATS scoring** (keyword
    coverage vs a job's keywords), **contract/risk summary** (flags common clauses),
    **CSV insight report** (rows/columns/simple profiling), **document Q&A** (keyword
    sentence retrieval — no LLM), and **export-ready summaries**. All scoring is
    deterministic (no external model call). Governance-logged.
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
    def _sentences(text: str) -> list[str]:
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="document_intelligence",
                agent_name="Document Intelligence",
                action_type=action_type,
                tool_used="DocumentIntelligenceService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def compare(self, text_a: str, text_b: str) -> dict:
        a, b = set(self._tokens(text_a)), set(self._tokens(text_b))
        shared = a & b
        union = a | b
        similarity = round(len(shared) / len(union), 3) if union else 0.0
        self._log("doc_compared", "Compared two documents.")
        return {
            "similarity": similarity,
            "shared_term_count": len(shared),
            "only_in_a": sorted(a - b)[:20],
            "only_in_b": sorted(b - a)[:20],
            "verdict": "very similar" if similarity > 0.6 else "somewhat similar" if similarity > 0.3 else "different",
        }

    def ats_score(self, resume_text: str, job_keywords: list[str]) -> dict:
        resume_terms = set(self._tokens(resume_text))
        keywords = [k.strip().lower() for k in job_keywords if k.strip()]
        matched = [k for k in keywords if all(part in resume_terms for part in self._tokens(k))]
        missing = [k for k in keywords if k not in matched]
        score = round((len(matched) / len(keywords)) * 100) if keywords else 0
        self._log("doc_ats_scored", f"ATS-scored a resume against {len(keywords)} keywords → {score}%.")
        return {
            "ats_score": score,
            "matched_keywords": matched,
            "missing_keywords": missing,
            "recommendation": "Strong match" if score >= 75 else "Add the missing keywords where truthful" if score >= 40 else "Significant gaps — tailor the resume",
        }

    def contract_risk(self, text: str) -> dict:
        lower = (text or "").lower()
        findings = []
        for label, keywords in _CONTRACT_RISKS.items():
            hits = [kw for kw in keywords if kw in lower]
            if hits:
                findings.append({"clause": label, "matched": hits})
        self._log("doc_contract_reviewed", f"Reviewed a contract — {len(findings)} clause type(s) flagged.")
        return {
            "flagged_clauses": findings,
            "flag_count": len(findings),
            "risk_level": "high" if len(findings) >= 4 else "medium" if findings else "low",
            "note": "Heuristic clause detection — not legal advice.",
        }

    def csv_insight(self, text: str) -> dict:
        lines = [ln for ln in (text or "").splitlines() if ln.strip()]
        if not lines:
            return {"rows": 0, "columns": 0, "headers": [], "note": "Empty CSV."}
        delimiter = "," if lines[0].count(",") >= lines[0].count("\t") else "\t"
        headers = [h.strip() for h in lines[0].split(delimiter)]
        rows = len(lines) - 1
        self._log("doc_csv_analyzed", f"Profiled a CSV — {rows} rows × {len(headers)} columns.")
        return {
            "rows": rows,
            "columns": len(headers),
            "headers": headers[:30],
            "insight": f"{rows} data row(s) across {len(headers)} column(s).",
        }

    def qa(self, text: str, question: str) -> dict:
        q_terms = set(self._tokens(question))
        best, best_score = "", 0
        for sentence in self._sentences(text):
            score = len(q_terms & set(self._tokens(sentence)))
            if score > best_score:
                best, best_score = sentence, score
        self._log("doc_qa", "Answered a question from a document (keyword retrieval).")
        return {
            "question": question,
            "answer": best or "No relevant passage found in the document.",
            "confidence": "high" if best_score >= 3 else "medium" if best_score >= 1 else "low",
            "note": "Deterministic keyword retrieval — no LLM call.",
        }

    def analytics_summary(self) -> dict:
        return {"doc_intel_capabilities": 5}

    def summary(self) -> dict:
        return {
            "capabilities": ["compare", "ats_score", "contract_risk", "csv_insight", "qa"],
            "contract_clause_types": list(_CONTRACT_RISKS.keys()),
            "note": "Deterministic, local, read-only document intelligence — no external model calls.",
        }
