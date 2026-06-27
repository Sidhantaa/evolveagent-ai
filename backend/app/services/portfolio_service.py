from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService
from app.services.workspace_service import WorkspaceService

RATING_THRESHOLDS = [
    (85, "excellent"),
    (70, "good"),
    (50, "watch"),
]


class PortfolioService:
    """v14.5 Portfolio Mode.

    Additive aggregation layer across every workspace/project. It reads existing
    collections (workspaces, goals, task graphs, analytics, feedback, risks,
    reports, evaluation runs, governance) and produces multi-project dashboards,
    cross-project analytics, a portfolio health score, executive summaries, and
    JSON/Markdown exports. It persists only its own executive reports.
    """

    reports_file = "portfolio_reports.json"

    def __init__(
        self,
        storage: StorageService,
        workspace_service: WorkspaceService,
        governance_service: GovernanceService,
    ):
        self.storage = storage
        self.workspaces = workspace_service
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _by_workspace(self, filename: str) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for item in self.storage.read_list(filename):
            grouped[item.get("workspace_id")].append(item)
        return grouped

    def _tasks_for_goal(self, graphs: list[dict], goal_id: str) -> list[dict]:
        graph = next((item for item in graphs if item.get("goal_id") == goal_id), None)
        return graph.get("tasks", []) if graph else []

    # ------------------------------------------------------------------
    # Per-workspace rollups (shared by dashboard + analytics + health)
    # ------------------------------------------------------------------
    def _collect(self) -> dict:
        workspaces = self.workspaces.list_workspaces(include_archived=True)
        goals_by_ws = self._by_workspace("goals.json")
        graphs = self.storage.read_list("task_graphs.json")
        analytics_by_ws = self._by_workspace("agent_analytics.json")
        feedback_by_ws = self._by_workspace("feedback.json")
        risks_by_ws = self._by_workspace("project_risks.json")
        governance_by_ws = self._by_workspace("governance_log.json")

        summaries = []
        for workspace in workspaces:
            workspace_id = workspace.get("workspace_id")
            goals = goals_by_ws.get(workspace_id, [])
            runs = analytics_by_ws.get(workspace_id, [])
            feedback = feedback_by_ws.get(workspace_id, [])
            risks = [risk for risk in risks_by_ws.get(workspace_id, []) if risk.get("status") != "resolved"]
            governance = governance_by_ws.get(workspace_id, [])

            total_tasks = completed_tasks = blocked_tasks = 0
            completed_goals = active_goals = 0
            for goal in goals:
                tasks = self._tasks_for_goal(graphs, goal.get("goal_id"))
                total_tasks += len(tasks)
                completed_tasks += sum(1 for task in tasks if task.get("status") == "done")
                blocked_tasks += sum(1 for task in tasks if task.get("status") == "blocked")
                progress = (
                    round((sum(1 for task in tasks if task.get("status") == "done") / len(tasks)) * 100)
                    if tasks
                    else goal.get("progress_percent", 0)
                )
                if progress >= 100:
                    completed_goals += 1
                elif goal.get("status") != "archived":
                    active_goals += 1

            scores = [
                run.get("overall_judge_score")
                for run in runs
                if isinstance(run.get("overall_judge_score"), (int, float))
            ]
            average_score = round(sum(scores) / len(scores), 2) if scores else 0
            fallback_count = sum(1 for run in runs if run.get("fallback_used"))
            blocked_actions = sum(1 for event in governance if event.get("blocked"))

            summaries.append(
                {
                    "workspace_id": workspace_id,
                    "name": workspace.get("name"),
                    "status": workspace.get("status", "active"),
                    "goal_count": len(goals),
                    "active_goals": active_goals,
                    "completed_goals": completed_goals,
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "blocked_tasks": blocked_tasks,
                    "task_completion_rate": round((completed_tasks / total_tasks) * 100, 2) if total_tasks else 0,
                    "run_count": len(runs),
                    "average_judge_score": average_score,
                    "fallback_count": fallback_count,
                    "open_risk_count": len(risks),
                    "high_risk_count": sum(1 for risk in risks if risk.get("severity") == "high"),
                    "feedback": dict(Counter(item.get("rating", "unknown") for item in feedback)),
                    "blocked_action_count": blocked_actions,
                    "runs": runs,
                    "risks": risks,
                    "feedback_items": feedback,
                }
            )
        return {"workspaces": workspaces, "summaries": summaries, "graphs": graphs}

    # ------------------------------------------------------------------
    # EVO-314: Multi-project dashboard
    # ------------------------------------------------------------------
    def dashboard(self) -> dict:
        collected = self._collect()
        summaries = collected["summaries"]
        all_scores = [
            score
            for summary in summaries
            for score in (
                [run.get("overall_judge_score") for run in summary["runs"] if isinstance(run.get("overall_judge_score"), (int, float))]
            )
        ]
        governance = self.storage.read_list("governance_log.json")
        return {
            "total_workspaces": len(summaries),
            "active_workspaces": sum(1 for item in summaries if item["status"] != "archived"),
            "total_goals": sum(item["goal_count"] for item in summaries),
            "active_goals": sum(item["active_goals"] for item in summaries),
            "completed_goals": sum(item["completed_goals"] for item in summaries),
            "total_tasks": sum(item["total_tasks"] for item in summaries),
            "completed_tasks": sum(item["completed_tasks"] for item in summaries),
            "blocked_tasks": sum(item["blocked_tasks"] for item in summaries),
            "total_runs": sum(item["run_count"] for item in summaries),
            "average_judge_score": round(sum(all_scores) / len(all_scores), 2) if all_scores else 0,
            "open_risks": sum(item["open_risk_count"] for item in summaries),
            "high_risks": sum(item["high_risk_count"] for item in summaries),
            "recent_governance_events": [
                {
                    "action_type": event.get("action_type"),
                    "agent_name": event.get("agent_name"),
                    "blocked": event.get("blocked", False),
                    "workspace_id": event.get("workspace_id"),
                }
                for event in list(reversed(governance))[:10]
            ],
            "workspace_summaries": [self._public_summary(item) for item in summaries],
        }

    def _public_summary(self, summary: dict) -> dict:
        return {key: value for key, value in summary.items() if key not in {"runs", "risks", "feedback_items"}}

    # ------------------------------------------------------------------
    # EVO-315: Cross-project analytics
    # ------------------------------------------------------------------
    def analytics(self) -> dict:
        collected = self._collect()
        summaries = collected["summaries"]
        agent_counter: Counter = Counter()
        task_type_counter: Counter = Counter()
        for summary in summaries:
            for run in summary["runs"]:
                for agent in run.get("agents_used", []) or []:
                    agent_counter[agent] += 1
                task_type_counter[run.get("task_type", "unknown")] += 1
        return {
            "runs_by_workspace": {item["name"]: item["run_count"] for item in summaries},
            "average_score_by_workspace": {item["name"]: item["average_judge_score"] for item in summaries},
            "goal_completion_by_workspace": {
                item["name"]: {"completed": item["completed_goals"], "total": item["goal_count"]}
                for item in summaries
            },
            "task_completion_by_workspace": {
                item["name"]: {"completed": item["completed_tasks"], "total": item["total_tasks"]}
                for item in summaries
            },
            "risk_count_by_workspace": {item["name"]: item["open_risk_count"] for item in summaries},
            "feedback_by_workspace": {item["name"]: item["feedback"] for item in summaries},
            "top_agents": [{"agent": agent, "runs": count} for agent, count in agent_counter.most_common(10)],
            "top_task_types": [{"task_type": task, "runs": count} for task, count in task_type_counter.most_common(10)],
        }

    # ------------------------------------------------------------------
    # EVO-316: Portfolio health score
    # ------------------------------------------------------------------
    def health(self) -> dict:
        collected = self._collect()
        summaries = collected["summaries"]
        total_tasks = sum(item["total_tasks"] for item in summaries)
        completed_tasks = sum(item["completed_tasks"] for item in summaries)
        blocked_tasks = sum(item["blocked_tasks"] for item in summaries)
        high_risks = sum(item["high_risk_count"] for item in summaries)
        open_risks = sum(item["open_risk_count"] for item in summaries)
        fallback_count = sum(item["fallback_count"] for item in summaries)
        blocked_actions = sum(item["blocked_action_count"] for item in summaries)
        all_scores = [run.get("overall_judge_score") for item in summaries for run in item["runs"] if isinstance(run.get("overall_judge_score"), (int, float))]
        average_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0
        completion_rate = round((completed_tasks / total_tasks) * 100, 2) if total_tasks else 0
        summary_workspace_ids = {item.get("workspace_id") for item in summaries}
        regressions = [
            regression
            for regression in self.storage.read_list("evaluation_regressions.json")
            if regression.get("workspace_id") in summary_workspace_ids
        ]

        drivers: list[str] = []
        risks: list[str] = []
        recommendations: list[str] = []

        score = 60.0
        if total_tasks:
            score += (completion_rate - 50) * 0.3
            if completion_rate >= 70:
                drivers.append(f"Strong task completion ({completion_rate}%).")
            elif completion_rate < 40:
                risks.append(f"Low task completion ({completion_rate}%).")
                recommendations.append("Prioritize finishing in-progress tasks before starting new goals.")
        if average_score:
            score += (average_score - 70) * 0.25
            if average_score >= 80:
                drivers.append(f"High average judge score ({average_score}).")
            elif average_score < 65:
                risks.append(f"Average judge score is low ({average_score}).")
                recommendations.append("Review low-scoring workflows in the Evaluation Lab.")
        score -= min(blocked_tasks, 20) * 1.0
        score -= min(high_risks, 10) * 2.0
        score -= min(fallback_count, 20) * 0.5
        score -= min(blocked_actions, 20) * 0.5
        score -= min(len(regressions), 10) * 1.0

        if blocked_tasks:
            risks.append(f"{blocked_tasks} blocked task(s) across the portfolio.")
            recommendations.append("Resolve blockers or re-sequence dependent work.")
        if high_risks:
            risks.append(f"{high_risks} high-severity risk(s) open.")
            recommendations.append("Add mitigations for high-severity risks in the Project Manager.")
        if regressions:
            risks.append(f"{len(regressions)} evaluation regression(s) recorded.")
        if not drivers:
            drivers.append("Portfolio is active; keep collecting runs and feedback to strengthen signals.")
        if not recommendations:
            recommendations.append("Maintain current cadence; no critical issues detected.")

        score = max(0, min(100, round(score)))
        rating = next((label for threshold, label in RATING_THRESHOLDS if score >= threshold), "at_risk")
        return {
            "score": score,
            "rating": rating,
            "drivers": drivers,
            "risks": risks,
            "recommendations": recommendations,
            "metrics": {
                "task_completion_rate": completion_rate,
                "blocked_tasks": blocked_tasks,
                "high_risks": high_risks,
                "open_risks": open_risks,
                "average_judge_score": average_score,
                "fallback_count": fallback_count,
                "blocked_actions": blocked_actions,
                "regressions": len(regressions),
            },
        }

    # ------------------------------------------------------------------
    # EVO-317: Executive summary
    # ------------------------------------------------------------------
    def generate_executive_summary(self) -> dict:
        dashboard = self.dashboard()
        health = self.health()
        analytics = self.analytics()
        top_agents = ", ".join(item["agent"] for item in analytics["top_agents"][:3]) or "no agents yet"
        summary_text = (
            f"Portfolio spans {dashboard['total_workspaces']} workspace(s) with "
            f"{dashboard['active_goals']} active goal(s) and {dashboard['completed_goals']} completed. "
            f"Health is {health['rating']} ({health['score']}/100) with an average judge score of "
            f"{dashboard['average_judge_score']}."
        )
        highlights = [
            f"{dashboard['completed_tasks']} of {dashboard['total_tasks']} tasks complete.",
            f"{dashboard['total_runs']} run(s) recorded; top agents: {top_agents}.",
            f"Health rating: {health['rating']} ({health['score']}/100).",
        ]
        next_actions = list(health["recommendations"])
        report = {
            "report_id": str(uuid4()),
            "title": "Portfolio Executive Summary",
            "summary": summary_text,
            "highlights": highlights,
            "risks": health["risks"],
            "next_actions": next_actions,
            "score": health["score"],
            "rating": health["rating"],
            "created_at": self._now(),
        }
        self.storage.append(self.reports_file, report)
        self._log("portfolio_report_generated", "Generated portfolio executive summary.")
        return report

    def list_reports(self, limit: int = 20) -> list[dict]:
        reports = self.storage.read_list(self.reports_file)
        return list(reversed(reports[-limit:]))

    # ------------------------------------------------------------------
    # EVO-318: Portfolio export
    # ------------------------------------------------------------------
    def export(self, format: str = "json") -> str:
        payload = {
            "generated_at": self._now(),
            "dashboard": self.dashboard(),
            "analytics": self.analytics(),
            "health": self.health(),
            "recent_reports": self.list_reports(limit=5),
        }
        if format == "markdown":
            return self._to_markdown(payload)
        return json.dumps(payload, indent=2)

    def _to_markdown(self, payload: dict) -> str:
        dashboard = payload["dashboard"]
        health = payload["health"]
        analytics = payload["analytics"]
        lines = [
            "# Portfolio Executive Summary",
            "",
            f"_Generated {payload['generated_at']}_",
            "",
            f"**Health:** {health['rating']} ({health['score']}/100)",
            "",
            "## Overview",
            f"- Workspaces: {dashboard['total_workspaces']} ({dashboard['active_workspaces']} active)",
            f"- Goals: {dashboard['total_goals']} (active {dashboard['active_goals']}, completed {dashboard['completed_goals']})",
            f"- Tasks: {dashboard['completed_tasks']}/{dashboard['total_tasks']} complete, {dashboard['blocked_tasks']} blocked",
            f"- Runs: {dashboard['total_runs']} · Avg judge score: {dashboard['average_judge_score']}",
            f"- Risks: {dashboard['open_risks']} open ({dashboard['high_risks']} high)",
            "",
            "## Workspaces",
        ]
        for summary in dashboard["workspace_summaries"]:
            lines.append(
                f"- **{summary['name']}** — goals {summary['completed_goals']}/{summary['goal_count']}, "
                f"tasks {summary['completed_tasks']}/{summary['total_tasks']}, "
                f"avg score {summary['average_judge_score']}, risks {summary['open_risk_count']}"
            )
        lines += ["", "## Health Drivers"]
        lines += [f"- {driver}" for driver in health["drivers"]]
        lines += ["", "## Risks"]
        lines += [f"- {risk}" for risk in health["risks"]] or ["- None recorded"]
        lines += ["", "## Recommendations"]
        lines += [f"- {item}" for item in health["recommendations"]]
        lines += ["", "## Top Agents"]
        lines += [f"- {item['agent']}: {item['runs']} run(s)" for item in analytics["top_agents"][:5]] or ["- None yet"]
        return "\n".join(lines) + "\n"

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                workspace_id=None,
                task_type="portfolio",
                agent_name="Portfolio Mode",
                action_type=action_type,
                tool_used="PortfolioService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )
