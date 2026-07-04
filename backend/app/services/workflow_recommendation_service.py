from __future__ import annotations

import re
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Workflow templates per task type: ordered steps, base complexity, and time estimate.
WORKFLOW_TEMPLATES = {
    "coding": {
        "steps": ["Clarify requirements", "Inspect the relevant code", "Draft the change", "Add/adjust tests", "Review & explain (no unsafe edits)"],
        "complexity": "medium", "est_minutes": 20, "risk": "low",
    },
    "research": {
        "steps": ["Frame the question", "Retrieve local sources", "Synthesize with citations", "Flag gaps & risks", "Summarize"],
        "complexity": "medium", "est_minutes": 15, "risk": "low",
    },
    "business": {
        "steps": ["Define the goal", "Draft the artifact (proposal/plan)", "Estimate impact (mock)", "Hold sends/payments for approval", "Summarize next actions"],
        "complexity": "high", "est_minutes": 25, "risk": "medium",
    },
    "data_analysis": {
        "steps": ["Load the dataset locally", "Profile & clean", "Compute insights", "Visualize (describe)", "Report findings"],
        "complexity": "medium", "est_minutes": 18, "risk": "low",
    },
    "general": {
        "steps": ["Understand the request", "Plan the approach", "Draft the answer", "Check against safety/approvals", "Summarize"],
        "complexity": "low", "est_minutes": 10, "risk": "low",
    },
}

_TASK_KEYWORDS = {
    "coding": ["code", "function", "bug", "refactor", "api", "test", "python", "javascript", "deploy"],
    "research": ["research", "find", "compare", "summarize", "explain", "sources", "documentation"],
    "business": ["proposal", "invoice", "lead", "marketing", "campaign", "revenue", "customer", "sales"],
    "data_analysis": ["data", "csv", "dataset", "analyze", "chart", "metric", "trend", "report"],
}

_RISKY_VERBS = ["send", "email", "pay", "purchase", "delete", "remove", "deploy", "post", "publish", "charge", "transfer"]


class WorkflowRecommendationService:
    """v73.0 Workflow Recommendation Engine — suggest the best workflow for a goal.

    Given a goal (and optional task type), it classifies the task, returns a
    **recommended workflow** (ordered expected steps), surfaces **similar past runs**
    (from the Master Agent route history by keyword overlap), and estimates **risk
    level**, **approval requirements**, and **time/complexity**. It is read-only and
    planning-only — it recommends, it does not execute. Governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {t for t in re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).split() if len(t) > 2}

    def _classify(self, goal: str) -> str:
        haystack = f" {(goal or '').lower()} "
        best, best_hits = "general", 0
        for task, keywords in _TASK_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in haystack)
            if hits > best_hits:
                best, best_hits = task, hits
        return best

    def _similar_runs(self, goal: str) -> list[dict]:
        terms = self._tokens(goal)
        scored = []
        for run in self.storage.read_list("master_agent_runs.json"):
            if not isinstance(run, dict):
                continue
            overlap = terms & self._tokens(run.get("request", ""))
            if overlap:
                scored.append({"request": (run.get("request") or "")[:120], "domain": run.get("primary_domain"),
                               "score": len(overlap), "requires_approval": run.get("requires_approval")})
        scored.sort(key=lambda s: s["score"], reverse=True)
        return scored[:5]

    def recommend(self, goal: str, task_type: str | None = None) -> dict:
        goal = (goal or "").strip()
        task = task_type if task_type in WORKFLOW_TEMPLATES else self._classify(goal)
        template = WORKFLOW_TEMPLATES[task]

        # Risk / approval detection from the goal text.
        haystack = f" {goal.lower()} "
        risky_verbs = [v for v in _RISKY_VERBS if v in haystack]
        requires_approval = bool(risky_verbs) or template["risk"] == "medium"
        risk_level = "high" if risky_verbs else template["risk"]

        similar = self._similar_runs(goal)
        # Blend the base estimate with observed complexity from similar runs.
        est_minutes = template["est_minutes"] + (5 if len(similar) == 0 else 0)

        self.governance.log_event(
            GovernanceEvent(
                task_type="workflow_recommendation",
                agent_name="Workflow Recommender",
                action_type="workflow_recommended",
                tool_used="WorkflowRecommendationService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=4 if requires_approval else 2,
                reason=f"Recommended a '{task}' workflow ({len(template['steps'])} steps).",
            )
        )
        return {
            "goal": goal,
            "task_type": task,
            "recommended_workflow": template["steps"],
            "expected_step_count": len(template["steps"]),
            "risk_level": risk_level,
            "requires_approval": requires_approval,
            "approval_reason": (f"Goal implies a real-world action ({', '.join(sorted(set(risky_verbs)))})." if risky_verbs
                                else "Sensitive task type — sends/payments held for approval." if requires_approval else None),
            "estimated_minutes": est_minutes,
            "complexity": template["complexity"],
            "similar_past_runs": similar,
            "note": "Read-only recommendation — planning only; nothing is executed, and risky steps require approval.",
        }

    def analytics_summary(self) -> dict:
        return {"workflow_templates": len(WORKFLOW_TEMPLATES)}

    def summary(self) -> dict:
        return {
            "task_types": list(WORKFLOW_TEMPLATES.keys()),
            "template_count": len(WORKFLOW_TEMPLATES),
            "note": "Recommends the best workflow (steps, risk, approvals, time) for a goal — read-only, planning-only.",
        }
