from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.goal_service import GoalService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

EFFORT_POINTS = {"small": 1, "low": 1, "medium": 3, "large": 5, "high": 5}
SEVERITY_ORDER = {"high": 3, "medium": 2, "low": 1}


class ProjectManagerService:
    """v14.0 Full AI Project Manager.

    Aggregates existing goals, task graphs, run analytics, and governance into a
    single project-management surface: timeline + milestones, resource allocation,
    a risk register, stakeholder status reports, and a unified dashboard. It reads
    existing data and persists only its own risk and report records.
    """

    risks_file = "project_risks.json"
    reports_file = "project_status_reports.json"

    def __init__(
        self,
        storage: StorageService,
        goal_service: GoalService,
        governance_service: GovernanceService,
    ):
        self.storage = storage
        self.goals = goal_service
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _workspace_filter(self, items: list[dict], workspace_id: str | None) -> list[dict]:
        if not workspace_id:
            return items
        return [item for item in items if item.get("workspace_id") == workspace_id]

    def _tasks_for(self, goal_id: str) -> list[dict]:
        graph = next(
            (item for item in self.storage.read_list("task_graphs.json") if item.get("goal_id") == goal_id),
            None,
        )
        return graph.get("tasks", []) if graph else []

    # ------------------------------------------------------------------
    # EVO: Timeline and milestones
    # ------------------------------------------------------------------
    def timeline(self, workspace_id: str | None = None) -> dict:
        goals = self.goals.list_goals(workspace_id)
        milestones = []
        for goal in goals:
            tasks = self._tasks_for(goal.get("goal_id"))
            status_counts = Counter(task.get("status", "pending") for task in tasks)
            phases = []
            seen_phases: set[str] = set()
            for task in tasks:
                phase = task.get("phase") or "Planning"
                if phase not in seen_phases:
                    seen_phases.add(phase)
                    phases.append(phase)
            progress = goal.get("progress_percent", 0)
            milestone_status = (
                "completed"
                if progress >= 100
                else "at_risk"
                if goal.get("risk_level") == "high" and progress < 50
                else "in_progress"
                if progress > 0
                else "not_started"
            )
            milestones.append(
                {
                    "goal_id": goal.get("goal_id"),
                    "title": goal.get("title"),
                    "status": milestone_status,
                    "goal_status": goal.get("status"),
                    "progress_percent": progress,
                    "risk_level": goal.get("risk_level", "low"),
                    "task_count": len(tasks),
                    "completed_tasks": status_counts.get("done", 0),
                    "blocked_tasks": status_counts.get("blocked", 0),
                    "phases": phases,
                    "created_at": goal.get("created_at"),
                    "updated_at": goal.get("updated_at"),
                }
            )
        milestones.sort(key=lambda item: item.get("created_at") or "")
        completed = sum(1 for item in milestones if item["status"] == "completed")
        average_progress = (
            round(sum(item["progress_percent"] for item in milestones) / len(milestones))
            if milestones
            else 0
        )
        return {
            "workspace_id": workspace_id,
            "milestone_count": len(milestones),
            "completed_milestones": completed,
            "average_progress": average_progress,
            "at_risk_milestones": sum(1 for item in milestones if item["status"] == "at_risk"),
            "milestones": milestones,
        }

    # ------------------------------------------------------------------
    # EVO: Resource allocation view
    # ------------------------------------------------------------------
    def resource_allocation(self, workspace_id: str | None = None) -> dict:
        goals = self.goals.list_goals(workspace_id)
        analytics = self._workspace_filter(self.storage.read_list("agent_analytics.json"), workspace_id)
        latency_total = sum(
            item.get("latency_ms", 0)
            for item in analytics
            if isinstance(item.get("latency_ms"), (int, float))
        )
        agent_load: Counter = Counter()
        allocations = []
        total_effort = 0
        for goal in goals:
            if goal.get("status") == "archived":
                continue
            tasks = self._tasks_for(goal.get("goal_id"))
            effort_points = sum(EFFORT_POINTS.get(task.get("estimated_effort", "medium"), 3) for task in tasks)
            agents = list(goal.get("recommended_agents") or [])
            for task in tasks:
                agent = task.get("recommended_agent")
                if agent:
                    agents.append(agent)
                    agent_load[agent] += EFFORT_POINTS.get(task.get("estimated_effort", "medium"), 3)
            unique_agents = sorted(set(agents))
            total_effort += effort_points
            allocations.append(
                {
                    "goal_id": goal.get("goal_id"),
                    "title": goal.get("title"),
                    "status": goal.get("status"),
                    "progress_percent": goal.get("progress_percent", 0),
                    "task_count": len(tasks),
                    "effort_points": effort_points,
                    "assigned_agents": unique_agents,
                    "agent_count": len(unique_agents),
                }
            )
        allocations.sort(key=lambda item: item["effort_points"], reverse=True)
        return {
            "workspace_id": workspace_id,
            "total_effort_points": total_effort,
            "active_goal_count": len(allocations),
            "tracked_run_count": len(analytics),
            "total_latency_ms": round(latency_total, 2),
            "agent_load": [
                {"agent": agent, "effort_points": points}
                for agent, points in agent_load.most_common(12)
            ],
            "allocations": allocations,
        }

    # ------------------------------------------------------------------
    # EVO: Risk register
    # ------------------------------------------------------------------
    def _derived_risks(self, workspace_id: str | None) -> list[dict]:
        derived = []
        for goal in self.goals.list_goals(workspace_id):
            if goal.get("status") == "archived":
                continue
            tasks = self._tasks_for(goal.get("goal_id"))
            blocked = [task for task in tasks if task.get("status") == "blocked"]
            if goal.get("risk_level") == "high":
                derived.append(
                    {
                        "title": f"High-risk goal: {goal.get('title')}",
                        "description": "Goal is flagged high risk and may need closer oversight.",
                        "severity": "high",
                        "goal_id": goal.get("goal_id"),
                        "mitigation": "Review scope and add human checkpoints before risky actions.",
                        "source": "auto",
                    }
                )
            if blocked:
                derived.append(
                    {
                        "title": f"Blocked tasks in {goal.get('title')}",
                        "description": f"{len(blocked)} task(s) are blocked.",
                        "severity": "medium",
                        "goal_id": goal.get("goal_id"),
                        "mitigation": "Resolve blockers or re-sequence dependent work.",
                        "source": "auto",
                    }
                )
        return derived

    def risk_register(self, workspace_id: str | None = None) -> dict:
        stored = self._workspace_filter(self.storage.read_list(self.risks_file), workspace_id)
        open_stored = [item for item in stored if item.get("status") != "resolved"]
        derived = self._derived_risks(workspace_id)
        combined = open_stored + derived
        combined.sort(key=lambda item: SEVERITY_ORDER.get(item.get("severity", "low"), 1), reverse=True)
        return {
            "workspace_id": workspace_id,
            "open_risk_count": len(combined),
            "severity_counts": dict(Counter(item.get("severity", "low") for item in combined)),
            "tracked_risks": list(reversed(stored[-50:])),
            "risks": combined,
        }

    def create_risk(
        self,
        title: str,
        description: str = "",
        severity: str = "medium",
        mitigation: str = "",
        goal_id: str | None = None,
        workspace_id: str | None = None,
    ) -> dict:
        risk = {
            "risk_id": str(uuid4()),
            "workspace_id": workspace_id,
            "title": title,
            "description": description,
            "severity": severity if severity in SEVERITY_ORDER else "medium",
            "mitigation": mitigation,
            "goal_id": goal_id,
            "status": "open",
            "source": "manual",
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.risks_file, risk)
        self._log("project_risk_created", workspace_id, f"Logged project risk: {title}.")
        return risk

    def update_risk(self, risk_id: str, updates: dict) -> dict:
        risks = self.storage.read_list(self.risks_file)
        risk = next((item for item in risks if item.get("risk_id") == risk_id), None)
        if risk is None:
            raise ValueError("Risk not found")
        for key in ("title", "description", "mitigation", "goal_id"):
            if updates.get(key) is not None:
                risk[key] = updates[key]
        if updates.get("severity") in SEVERITY_ORDER:
            risk["severity"] = updates["severity"]
        if updates.get("status") in {"open", "monitoring", "resolved"}:
            risk["status"] = updates["status"]
        risk["updated_at"] = self._now()
        self.storage.write_list(self.risks_file, risks)
        self._log("project_risk_updated", risk.get("workspace_id"), f"Updated project risk {risk_id}.")
        return risk

    # ------------------------------------------------------------------
    # EVO: Stakeholder status reports
    # ------------------------------------------------------------------
    def generate_status_report(self, workspace_id: str | None = None) -> dict:
        timeline = self.timeline(workspace_id)
        resources = self.resource_allocation(workspace_id)
        risks = self.risk_register(workspace_id)
        goals = self.goals.list_goals(workspace_id)
        status_counts = Counter(goal.get("status", "active") for goal in goals)
        top_risks = risks["risks"][:5]
        highlights = [
            f"{timeline['completed_milestones']} of {timeline['milestone_count']} milestones complete "
            f"({timeline['average_progress']}% average progress).",
            f"{resources['active_goal_count']} active goal(s) with {resources['total_effort_points']} effort points planned.",
            f"{risks['open_risk_count']} open risk(s) tracked.",
        ]
        report = {
            "report_id": str(uuid4()),
            "workspace_id": workspace_id,
            "period": "weekly",
            "generated_at": self._now(),
            "headline": (
                f"{timeline['average_progress']}% average progress across "
                f"{timeline['milestone_count']} milestone(s)"
            ),
            "goal_status_counts": dict(status_counts),
            "milestone_summary": {
                "total": timeline["milestone_count"],
                "completed": timeline["completed_milestones"],
                "at_risk": timeline["at_risk_milestones"],
                "average_progress": timeline["average_progress"],
            },
            "resource_summary": {
                "active_goals": resources["active_goal_count"],
                "total_effort_points": resources["total_effort_points"],
                "tracked_runs": resources["tracked_run_count"],
            },
            "open_risk_count": risks["open_risk_count"],
            "top_risks": [
                {"title": item.get("title"), "severity": item.get("severity")}
                for item in top_risks
            ],
            "highlights": highlights,
        }
        self.storage.append(self.reports_file, report)
        self._log("project_status_report_generated", workspace_id, "Generated stakeholder status report.")
        return report

    def list_status_reports(self, workspace_id: str | None = None, limit: int = 20) -> list[dict]:
        reports = self._workspace_filter(self.storage.read_list(self.reports_file), workspace_id)
        return list(reversed(reports[-limit:]))

    # ------------------------------------------------------------------
    # EVO: Linear / Mission Control unified view
    # ------------------------------------------------------------------
    def dashboard(self, workspace_id: str | None = None) -> dict:
        timeline = self.timeline(workspace_id)
        resources = self.resource_allocation(workspace_id)
        risks = self.risk_register(workspace_id)
        reports = self.list_status_reports(workspace_id, limit=1)
        goals = self.goals.list_goals(workspace_id)
        linked = self._workspace_filter(self.storage.read_list("linear_links.json"), workspace_id)
        return {
            "workspace_id": workspace_id,
            "goal_count": len(goals),
            "active_goal_count": resources["active_goal_count"],
            "milestone_summary": {
                "total": timeline["milestone_count"],
                "completed": timeline["completed_milestones"],
                "at_risk": timeline["at_risk_milestones"],
                "average_progress": timeline["average_progress"],
            },
            "resource_summary": {
                "total_effort_points": resources["total_effort_points"],
                "agent_load": resources["agent_load"][:5],
            },
            "risk_summary": {
                "open_risk_count": risks["open_risk_count"],
                "severity_counts": risks["severity_counts"],
            },
            "linked_linear_issue_count": len(linked),
            "latest_report": reports[0] if reports else None,
            "upcoming_milestones": [
                item for item in timeline["milestones"] if item["status"] in {"in_progress", "not_started", "at_risk"}
            ][:6],
        }

    def _log(self, action_type: str, workspace_id: str | None, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                workspace_id=workspace_id,
                task_type="project_manager",
                agent_name="AI Project Manager",
                action_type=action_type,
                tool_used="ProjectManagerService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )
