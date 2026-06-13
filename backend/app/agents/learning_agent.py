from collections import Counter, defaultdict

from app.services.storage_service import StorageService


class LearningAgent:
    name = "Learning Agent"

    def __init__(self, storage: StorageService):
        self.storage = storage

    def report(self, workspace_id: str | None = None) -> dict:
        runs = self.filter_workspace(self.storage.read_list("agent_analytics.json"), workspace_id)
        feedback = self.filter_workspace(self.storage.read_list("feedback.json"), workspace_id)
        strategies = self.filter_workspace(self.storage.read_list("workflow_strategies.json"), workspace_id)
        model_stats = self.filter_workspace(self.storage.read_list("model_performance.json"), workspace_id)
        goals = self.filter_workspace(self.storage.read_list("goals.json"), workspace_id)
        task_graphs = self.filter_workspace(self.storage.read_list("task_graphs.json"), workspace_id)
        custom_agents = self.filter_workspace(self.storage.read_list("custom_agents.json"), workspace_id)
        user_preferences = sorted(
            self.filter_workspace(self.storage.read_list("user_preferences.json"), workspace_id),
            key=lambda item: item.get("score", 0),
            reverse=True,
        )

        agent_scores: dict[str, list[float]] = {}
        agent_scores_by_task: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        for run in runs:
            task_type = run.get("task_type", "unknown")
            for score in run.get("per_agent_scores", []):
                average = (score.get("usefulness_score", 0) + score.get("clarity_score", 0)) / 2
                agent_name = score.get("agent_name", "Unknown Agent")
                agent_scores.setdefault(agent_name, []).append(average)
                agent_scores_by_task[task_type][agent_name].append(average)
        averaged_agents = [
            {"agent_name": name, "average_score": round(sum(values) / len(values), 2), "samples": len(values)}
            for name, values in agent_scores.items()
            if values
        ]
        averaged_agents.sort(key=lambda item: item["average_score"], reverse=True)
        strongest_by_task = self.task_agent_rankings(agent_scores_by_task, strongest=True)
        weakest_by_task = self.task_agent_rankings(agent_scores_by_task, strongest=False)

        task_scores: dict[str, list[float]] = {}
        for run in runs:
            task_scores.setdefault(run.get("task_type", "unknown"), []).append(run.get("overall_judge_score", 0))
        worst_task_types = [
            {"task_type": name, "average_score": round(sum(values) / len(values), 2)}
            for name, values in task_scores.items()
            if values
        ]
        worst_task_types.sort(key=lambda item: item["average_score"])
        feedback_counts = Counter(item.get("rating", "unknown") for item in feedback)
        best_workflows = sorted(strategies, key=lambda item: item.get("average_score", 0), reverse=True)[:5]
        worst_workflows = sorted(strategies, key=lambda item: item.get("average_score", 100))[:5]

        return {
            "workspace_id": workspace_id,
            "total_runs_analyzed": len(runs),
            "strongest_agents": averaged_agents[:5],
            "weakest_agents": list(reversed(averaged_agents[-5:])),
            "strongest_agents_by_task_type": strongest_by_task,
            "weakest_agents_by_task_type": weakest_by_task,
            "best_workflows": best_workflows,
            "best_workflows_by_task_type": best_workflows,
            "worst_workflows_by_task_type": worst_workflows,
            "worst_task_types": worst_task_types[:5],
            "recurring_failure_reasons": self.failure_reasons(runs, strategies, model_stats),
            "prompt_improvement_suggestions": self.prompt_suggestions(averaged_agents),
            "model_routing_suggestions": self.model_suggestions(model_stats, runs),
            "user_feedback_patterns": [
                {"rating": rating, "count": count} for rating, count in feedback_counts.most_common()
            ],
            "user_preference_patterns": user_preferences[:8],
            "recommended_next_actions": self.next_actions(worst_workflows, model_stats, user_preferences),
            "recommended_custom_agents": self.custom_agent_recommendations(runs, custom_agents),
            "workflow_improvements_for_goals": self.goal_workflow_suggestions(goals, task_graphs),
            "recurring_goal_blockers": self.goal_blockers(task_graphs),
            "active_prompt_versions": [
                item for item in self.storage.read_list("prompt_versions.json") if item.get("status") == "active"
            ],
            "proposed_prompt_versions": [
                item for item in self.storage.read_list("prompt_versions.json") if item.get("status") == "proposed"
            ],
            **self.linear_insights(workspace_id),
        }

    def linear_insights(self, workspace_id: str | None = None) -> dict:
        links = self.filter_workspace(self.storage.read_list("linear_links.json"), workspace_id)
        linear_runs = [item for item in self.filter_workspace(self.storage.read_list("agent_analytics.json"), workspace_id) if item.get("task_type") == "linear_task"]
        blockers = [
            {"reason": note.get("note"), "issue": link.get("linear_identifier")}
            for link in links
            if link.get("status") in {"failed", "blocked"}
            for note in (link.get("notes") or [])[-1:]
        ]
        agent_scores: dict[str, list[float]] = defaultdict(list)
        for run in linear_runs:
            for score in run.get("per_agent_scores", []):
                average = (score.get("usefulness_score", 0) + score.get("clarity_score", 0)) / 2
                agent_scores[score.get("agent_name", "Unknown Agent")].append(average)
        best_agents = sorted(
            (
                {"agent_name": name, "average_score": round(sum(values) / len(values), 2)}
                for name, values in agent_scores.items()
                if values
            ),
            key=lambda item: item["average_score"],
            reverse=True,
        )
        return {
            "linear_tasks_synced": len(links),
            "linear_tasks_completed": sum(1 for item in links if item.get("status") == "completed"),
            "recurring_linear_blockers": blockers[:5],
            "best_agents_for_linear_tasks": best_agents[:5],
            "linear_task_completion_performance": {
                "runs": len(linear_runs),
                "completed_links": sum(1 for item in links if item.get("status") == "completed"),
            },
            "recommended_linear_workflow_improvements": [
                "Run one Linear subtask per execution and review approval plans before apply.",
                "Keep AUTO_GIT_PUSH=false until commits and tests are stable.",
            ],
        }

    @staticmethod
    def filter_workspace(items: list[dict], workspace_id: str | None = None) -> list[dict]:
        if not workspace_id:
            return items
        return [item for item in items if item.get("workspace_id") == workspace_id]

    @staticmethod
    def task_agent_rankings(agent_scores_by_task: dict, strongest: bool) -> list[dict]:
        rows = []
        for task_type, agents in agent_scores_by_task.items():
            averaged = [
                {
                    "agent_name": name,
                    "average_score": round(sum(values) / len(values), 2),
                    "samples": len(values),
                }
                for name, values in agents.items()
                if values
            ]
            averaged.sort(key=lambda item: item["average_score"], reverse=strongest)
            if averaged:
                rows.append({"task_type": task_type, "agents": averaged[:3]})
        return sorted(rows, key=lambda item: item["task_type"])

    @staticmethod
    def failure_reasons(runs: list[dict], strategies: list[dict], model_stats: list[dict]) -> list[dict]:
        reasons = Counter()
        for run in runs:
            if run.get("overall_judge_score", 100) < 75:
                reasons["low_judge_score"] += 1
            if run.get("fallback_used"):
                reasons["provider_fallback_used"] += 1
            if run.get("file_context_used") and run.get("overall_judge_score", 100) < 80:
                reasons["file_context_answer_needs_review"] += 1
        for strategy in strategies:
            if strategy.get("fallback_rate", 0) > 0.25:
                reasons["high_workflow_fallback_rate"] += 1
            if strategy.get("feedback_positive_rate", 1) < 0.5 and strategy.get("feedback_count", 0) >= 2:
                reasons["low_positive_feedback_rate"] += 1
        for model in model_stats:
            if model.get("fallback_count", 0) > 0:
                reasons["model_route_fallback"] += 1
        if not reasons:
            return [{"reason": "No recurring failures detected yet.", "count": 0}]
        return [{"reason": reason, "count": count} for reason, count in reasons.most_common(6)]

    @staticmethod
    def prompt_suggestions(averaged_agents: list[dict]) -> list[str]:
        weak = [item for item in averaged_agents if item.get("average_score", 100) < 78]
        if not weak:
            return ["No urgent prompt changes. Keep collecting feedback and judge scores."]
        return [
            f"Review the {item['agent_name']} prompt; its average evaluation score is {item['average_score']}."
            for item in weak[:3]
        ]

    @staticmethod
    def model_suggestions(model_stats: list[dict], runs: list[dict] | None = None) -> list[dict]:
        if not model_stats:
            return [{"category": "general", "recommendation": "No model routing data yet."}]
        aggregate = [item for item in model_stats if item.get("provider_model")]
        tournament = [item for item in model_stats if item.get("record_type") == "consensus_candidate"]
        fastest = min(aggregate, key=lambda item: item.get("average_latency_ms", 999999), default=None)
        reliable = sorted(
            aggregate,
            key=lambda item: (item.get("fallback_count", 0) / max(item.get("run_count", 1), 1), -item.get("run_count", 0)),
        )
        winner_counts = Counter(
            f"{item.get('provider')}:{item.get('model')}"
            for item in tournament
            if item.get("selected_as_winner")
        )
        consensus_winner = winner_counts.most_common(1)[0][0] if winner_counts else None
        by_task = LearningAgent.best_model_by_task(tournament)
        suggestions = []
        for task_type in ["coding", "writing", "document_analysis", "recording_summary", "app_automation"]:
            key = "general"
            if task_type == "coding":
                key = by_task.get("coding") or by_task.get("code_review") or consensus_winner or (reliable[0].get("provider_model") if reliable else None)
            elif task_type == "writing":
                key = by_task.get("general") or by_task.get("system_explanation") or consensus_winner or (reliable[0].get("provider_model") if reliable else None)
            elif task_type == "document_analysis":
                key = by_task.get("document_analysis") or by_task.get("file_summary") or by_task.get("resume_review") or consensus_winner or (reliable[0].get("provider_model") if reliable else None)
            elif task_type == "recording_summary":
                key = by_task.get("recording_summary") or consensus_winner or (reliable[0].get("provider_model") if reliable else None)
            elif task_type == "app_automation":
                key = by_task.get("app_automation") or consensus_winner or (reliable[0].get("provider_model") if reliable else None)
            suggestions.append(
                {
                    "category": task_type,
                    "recommendation": f"Prefer {key} for {task_type} tasks based on stored performance." if key else f"Collect more runs before selecting a model for {task_type}.",
                }
            )
        if fastest:
            suggestions.append({"category": "fastest_provider", "recommendation": f"Fastest observed route: {fastest.get('provider_model')} at {fastest.get('average_latency_ms')} ms average."})
        if reliable:
            suggestions.append({"category": "most_reliable_provider", "recommendation": f"Most reliable observed route: {reliable[0].get('provider_model')} with {reliable[0].get('fallback_count', 0)} fallback(s)."})
        fallback_heavy = [item for item in model_stats if item.get("fallback_count", 0) > 0]
        if fallback_heavy:
            suggestions.append({"category": "fallback", "recommendation": "Check provider configuration because at least one model route used fallback."})
        return suggestions

    @staticmethod
    def best_model_by_task(tournament: list[dict]) -> dict[str, str]:
        scores: dict[str, Counter] = defaultdict(Counter)
        for item in tournament:
            if not item.get("selected_as_winner"):
                continue
            task_type = item.get("task_type", "general")
            scores[task_type][f"{item.get('provider')}:{item.get('model')}"] += 1
        return {
            task_type: counter.most_common(1)[0][0]
            for task_type, counter in scores.items()
            if counter
        }

    @staticmethod
    def next_actions(worst_workflows: list[dict], model_stats: list[dict], user_preferences: list[dict]) -> list[str]:
        actions = []
        if worst_workflows:
            actions.append(f"Review the {worst_workflows[0].get('task_type')} workflow; it has the lowest stored average score.")
        if any(item.get("fallback_count", 0) > 0 for item in model_stats):
            actions.append("Verify provider keys and SDK availability to reduce mock fallbacks.")
        if user_preferences:
            top = user_preferences[0].get("preference")
            actions.append(f"Consider formatting future answers around the observed preference: {top}.")
        actions.append("Keep prompt changes in proposed status until manually approved.")
        return actions

    @staticmethod
    def custom_agent_recommendations(runs: list[dict], custom_agents: list[dict]) -> list[dict]:
        if not custom_agents:
            return [{"recommendation": "Create custom agents from templates for repeated workflows.", "agent_name": None}]
        usage = Counter(item.get("custom_agent_name") for item in runs if item.get("custom_agent_used"))
        enabled = [item for item in custom_agents if item.get("enabled", True)]
        rows = []
        for agent in enabled[:6]:
            count = usage.get(agent.get("name"), 0)
            rows.append(
                {
                    "agent_name": agent.get("name"),
                    "usage_count": count,
                    "recommendation": (
                        f"Keep using {agent.get('name')} for related goal tasks."
                        if count
                        else f"Try {agent.get('name')} on a suitable Mission Control task to collect performance data."
                    ),
                }
            )
        return rows

    @staticmethod
    def goal_workflow_suggestions(goals: list[dict], task_graphs: list[dict]) -> list[str]:
        tasks = [task for graph in task_graphs for task in graph.get("tasks", [])]
        if not goals:
            return ["No goals created yet. Use Goal Mode to build a task graph from a larger objective."]
        suggestions = []
        pending = sum(1 for task in tasks if task.get("status") == "pending")
        blocked = sum(1 for task in tasks if task.get("status") == "blocked")
        if pending:
            suggestions.append(f"{pending} Mission Control task(s) are pending; run the highest-priority next task.")
        if blocked:
            suggestions.append(f"{blocked} task(s) are blocked; review dependencies or approval requirements.")
        completed_goals = sum(1 for goal in goals if goal.get("status") == "completed")
        if completed_goals:
            suggestions.append(f"{completed_goals} completed goal(s) can be used as examples for future task graph structure.")
        return suggestions or ["Goal workflows look healthy. Continue collecting task outcomes and feedback."]

    @staticmethod
    def goal_blockers(task_graphs: list[dict]) -> list[dict]:
        blocked = [
            {
                "goal_id": graph.get("goal_id"),
                "task_id": task.get("task_id"),
                "title": task.get("title"),
                "phase": task.get("phase"),
                "reason": "Task status is blocked.",
            }
            for graph in task_graphs
            for task in graph.get("tasks", [])
            if task.get("status") == "blocked"
        ]
        return blocked[:8] or [{"reason": "No recurring goal blockers detected yet.", "count": 0}]
