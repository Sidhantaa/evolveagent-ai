from __future__ import annotations

from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Rule-based improvement hints keyed by observed weakness.
PROMPT_HINTS = {
    "low_score": "Tighten the system prompt: add explicit success criteria and a short output format.",
    "high_latency": "Reduce scope or context size for this agent; consider a faster model for its task type.",
    "regressed": "Recent outputs dropped — review recent prompt/context changes and add a regression eval case.",
}


class AgentQualityService:
    """v72.0 Agent Quality Optimizer — improve agent outputs over time.

    A read-only analysis over recorded run analytics and human feedback:
    per-agent **score trends**, **weak-agent detection**, rule-based **prompt
    improvement suggestions**, **best agent by task type**, **regression checks**
    (recent window vs previous), and **human-feedback correlation** (ratings vs
    judge scores). It computes from existing data only and never changes prompts or
    runs anything. Governance-logged.
    """

    analytics_file = "agent_analytics.json"
    feedback_file = "feedback.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _records(self) -> list[dict]:
        rows = [r for r in self.storage.read_list(self.analytics_file) if isinstance(r, dict)]
        rows.sort(key=lambda r: r.get("created_at", ""))
        return rows

    @staticmethod
    def _scale(value: float, is_unit: bool) -> float:
        return round(value * 100, 1) if is_unit else round(value, 1)

    def _agent_scores(self, rows: list[dict]) -> tuple[dict, bool]:
        # agent -> list of scores; detect 0-1 vs 0-100 scale.
        per_agent: dict[str, list[float]] = {}
        max_seen = 0.0
        for row in rows:
            scores = row.get("per_agent_scores") or {}
            if isinstance(scores, dict):
                for agent, score in scores.items():
                    try:
                        value = float(score)
                    except (TypeError, ValueError):
                        continue
                    per_agent.setdefault(agent, []).append(value)
                    max_seen = max(max_seen, value)
        return per_agent, max_seen <= 1.0

    def dashboard(self) -> dict:
        rows = self._records()
        per_agent, is_unit = self._agent_scores(rows)

        # Score trends + weak-agent detection (normalized to 0-100).
        trends = []
        weak = []
        for agent, scores in per_agent.items():
            if not scores:
                continue
            avg = sum(scores) / len(scores)
            recent = scores[-10:]
            recent_avg = sum(recent) / len(recent)
            avg100 = self._scale(avg, is_unit)
            recent100 = self._scale(recent_avg, is_unit)
            trends.append({"agent": agent, "runs": len(scores), "avg_score": avg100, "recent_avg": recent100,
                           "trend": "up" if recent_avg > avg else "down" if recent_avg < avg else "flat"})
            if recent100 < 60:
                weak.append({"agent": agent, "recent_avg": recent100, "suggestion": PROMPT_HINTS["low_score"]})
        trends.sort(key=lambda t: t["avg_score"], reverse=True)

        # Regression checks: previous window vs recent window.
        regressions = []
        for agent, scores in per_agent.items():
            if len(scores) >= 8:
                mid = len(scores) // 2
                prev = sum(scores[:mid]) / mid
                rec = sum(scores[mid:]) / (len(scores) - mid)
                if rec < prev * 0.9:
                    regressions.append({"agent": agent, "previous": self._scale(prev, is_unit), "recent": self._scale(rec, is_unit),
                                        "suggestion": PROMPT_HINTS["regressed"]})

        return {
            "score_trends": trends,
            "weak_agents": weak,
            "regressions": regressions,
            "best_by_task": self.best_by_task(rows, is_unit),
            "feedback_correlation": self.feedback_correlation(rows),
            "agents_tracked": len(per_agent),
            "score_scale": "0-1 (normalized to 0-100)" if is_unit else "0-100",
            "note": "Read-only analysis of recorded analytics + feedback — no prompts are changed and nothing is executed.",
        }

    def best_by_task(self, rows: list[dict] | None = None, is_unit: bool | None = None) -> list[dict]:
        rows = rows if rows is not None else self._records()
        if is_unit is None:
            _, is_unit = self._agent_scores(rows)
        by_task: dict[str, dict[str, list[float]]] = {}
        for row in rows:
            task = row.get("task_type") or "unknown"
            scores = row.get("per_agent_scores") or {}
            if isinstance(scores, dict):
                for agent, score in scores.items():
                    try:
                        value = float(score)
                    except (TypeError, ValueError):
                        continue
                    by_task.setdefault(task, {}).setdefault(agent, []).append(value)
        result = []
        for task, agents in by_task.items():
            ranked = sorted(((a, sum(v) / len(v)) for a, v in agents.items()), key=lambda x: x[1], reverse=True)
            if ranked:
                best_agent, best_score = ranked[0]
                result.append({"task_type": task, "best_agent": best_agent, "avg_score": self._scale(best_score, is_unit)})
        result.sort(key=lambda r: r["task_type"])
        return result

    def feedback_correlation(self, rows: list[dict] | None = None) -> dict:
        rows = rows if rows is not None else self._records()
        judge_by_run = {r.get("run_id"): r.get("overall_judge_score") for r in rows if r.get("run_id")}
        pos = neg = 0
        pos_judge: list[float] = []
        neg_judge: list[float] = []
        for fb in self.storage.read_list(self.feedback_file):
            if not isinstance(fb, dict):
                continue
            rating = str(fb.get("rating", "")).lower()
            judge = judge_by_run.get(fb.get("run_id"))
            if judge is None:
                continue
            try:
                judge = float(judge)
            except (TypeError, ValueError):
                continue
            if rating in ("up", "positive", "1", "good", "thumbs_up"):
                pos += 1
                pos_judge.append(judge)
            elif rating in ("down", "negative", "0", "bad", "thumbs_down"):
                neg += 1
                neg_judge.append(judge)
        return {
            "positive_feedback": pos,
            "negative_feedback": neg,
            "avg_judge_when_positive": round(sum(pos_judge) / len(pos_judge), 2) if pos_judge else None,
            "avg_judge_when_negative": round(sum(neg_judge) / len(neg_judge), 2) if neg_judge else None,
            "aligned": (sum(pos_judge) / len(pos_judge) if pos_judge else 0) >= (sum(neg_judge) / len(neg_judge) if neg_judge else 0),
        }

    def _log(self) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="agent_quality",
                agent_name="Agent Quality Optimizer",
                action_type="agent_quality_analyzed",
                tool_used="AgentQualityService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason="Analyzed agent quality trends, weak agents, regressions, and feedback correlation.",
            )
        )

    def summary(self) -> dict:
        self._log()
        dash = self.dashboard()
        return {
            "agents_tracked": dash["agents_tracked"],
            "weak_agent_count": len(dash["weak_agents"]),
            "regression_count": len(dash["regressions"]),
            "top_agent": dash["score_trends"][0] if dash["score_trends"] else None,
            "note": dash["note"],
        }

    def analytics_summary(self) -> dict:
        per_agent, _ = self._agent_scores(self._records())
        return {"agent_quality_agents_tracked": len(per_agent)}
