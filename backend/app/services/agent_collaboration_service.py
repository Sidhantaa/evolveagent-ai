from __future__ import annotations

import re
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

_NEGATION = re.compile(r"\b(not|no|never|shouldn't|can't|won't|disagree|oppose|against)\b", re.IGNORECASE)


class AgentCollaborationService:
    """v80.0 Multi-Agent Collaboration 2.0 — make agents collaborate visibly.

    A deterministic, read-only analysis of a set of agent **contributions** on a topic:
    it renders an **agent conversation view**, computes a **consensus summary** (points
    shared across a majority), **disagreement notes** (positions that diverge or negate),
    a **reviewer/auditor pass** (flags contributions lacking evidence), a **final
    decision** (the most central position) with a **rationale**. Role-based — each
    contribution carries a role. No model call; nothing executed. Governance-logged.
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
    def _norm(contributions: list[dict]) -> list[dict]:
        out = []
        for i, c in enumerate(contributions or []):
            if isinstance(c, dict):
                out.append({"role": str(c.get("role") or f"agent{i + 1}")[:60], "position": str(c.get("position") or "")})
        return out

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="agent_collaboration",
                agent_name="Agent Collaboration",
                action_type=action_type,
                tool_used="AgentCollaborationService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def analyze(self, topic: str, contributions: list[dict]) -> dict:
        contribs = self._norm(contributions)
        token_sets = [self._tokens(c["position"]) for c in contribs]
        n = len(contribs)

        # Consensus: tokens present in a majority of contributions.
        consensus_terms = []
        if n:
            from collections import Counter
            counter: Counter = Counter()
            for ts in token_sets:
                counter.update(ts)
            consensus_terms = sorted([term for term, count in counter.items() if count > n / 2])[:15]

        # Disagreements: pairs with low overlap or opposing negation.
        disagreements = []
        for i in range(n):
            for j in range(i + 1, n):
                union = token_sets[i] | token_sets[j]
                overlap = len(token_sets[i] & token_sets[j]) / len(union) if union else 0
                neg_diff = bool(_NEGATION.search(contribs[i]["position"])) != bool(_NEGATION.search(contribs[j]["position"]))
                if overlap < 0.25 or neg_diff:
                    disagreements.append({"between": [contribs[i]["role"], contribs[j]["role"]],
                                          "reason": "opposing stance" if neg_diff else "low overlap",
                                          "overlap": round(overlap, 2)})

        # Reviewer/auditor pass: flag contributions lacking evidence (numbers/citations).
        reviewer_flags = []
        for c in contribs:
            if not re.search(r"\d|https?://|because|evidence|data", c["position"], re.IGNORECASE):
                reviewer_flags.append({"role": c["role"], "flag": "no explicit evidence/reasoning given"})

        # Final decision: the position most central (highest avg overlap with the others).
        final = None
        if n:
            best_idx, best_score = 0, -1.0
            for i in range(n):
                score = 0.0
                for j in range(n):
                    if i == j:
                        continue
                    union = token_sets[i] | token_sets[j]
                    score += (len(token_sets[i] & token_sets[j]) / len(union)) if union else 0
                avg = score / (n - 1) if n > 1 else 1.0
                if avg > best_score:
                    best_idx, best_score = i, avg
            final = {
                "recommended_by": contribs[best_idx]["role"],
                "position": contribs[best_idx]["position"][:300],
                "rationale": f"Most central position (avg overlap {round(best_score, 2)} with peers); "
                             f"{len(consensus_terms)} consensus term(s), {len(disagreements)} disagreement(s).",
            }

        self._log("collaboration_analyzed", f"Analyzed {n} contribution(s) on a topic — {len(disagreements)} disagreement(s).")
        return {
            "topic": topic,
            "conversation": [{"role": c["role"], "position": c["position"][:300]} for c in contribs],
            "consensus_summary": consensus_terms,
            "disagreement_notes": disagreements[:20],
            "reviewer_pass": reviewer_flags,
            "final_decision": final,
            "note": "Deterministic multi-agent analysis of submitted positions — read-only, no model call, nothing executed.",
        }

    def analytics_summary(self) -> dict:
        return {"agent_collaboration_capabilities": 5}

    def summary(self) -> dict:
        return {
            "capabilities": ["conversation_view", "consensus_summary", "disagreement_notes", "reviewer_pass", "final_decision"],
            "note": "Deterministic, read-only multi-agent collaboration analysis — no model call.",
        }
