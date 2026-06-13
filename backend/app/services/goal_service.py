from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GoalResult, GoalTask, TaskGraph
from app.services.storage_service import StorageService


class GoalService:
    def __init__(self, storage: StorageService):
        self.storage = storage

    def create_from_plan(
        self,
        planner_result: dict,
        source_session_id: str | None = None,
        source_message_id: str | None = None,
        tags: list[str] | None = None,
        workspace_id: str | None = None,
    ) -> tuple[GoalResult, TaskGraph]:
        now = datetime.now(UTC).isoformat()
        goal_id = str(uuid4())
        tasks = [
            GoalTask(
                **{
                    **task,
                    "task_id": task.get("task_id") or str(uuid4()),
                    "created_at": now,
                    "updated_at": now,
                }
            )
            for task in planner_result.get("tasks", [])
        ]
        goal = GoalResult(
            goal_id=goal_id,
            workspace_id=workspace_id,
            title=planner_result.get("goal_title") or "New Mission",
            description=planner_result.get("goal_summary") or "",
            status="active",
            created_at=now,
            updated_at=now,
            source_session_id=source_session_id,
            source_message_id=source_message_id,
            progress_percent=0,
            risk_level=planner_result.get("risk_level", "low"),
            recommended_agents=planner_result.get("recommended_agents", []),
            tags=tags or [],
            next_best_task=planner_result.get("next_best_task"),
        )
        task_graph = TaskGraph(goal_id=goal_id, workspace_id=workspace_id, tasks=tasks)
        goals = self.storage.read_list("goals.json")
        goals.append(goal.model_dump())
        self.storage.write_list("goals.json", goals)
        graphs = self.storage.read_list("task_graphs.json")
        graphs.append(task_graph.model_dump())
        self.storage.write_list("task_graphs.json", graphs)
        return goal, task_graph

    def create_manual(
        self,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        workspace_id: str | None = None,
    ) -> tuple[GoalResult, TaskGraph]:
        planner_result = {
            "goal_title": title,
            "goal_summary": description,
            "tasks": [],
            "recommended_agents": [],
            "risk_level": "low",
            "next_best_task": None,
        }
        return self.create_from_plan(planner_result, tags=tags, workspace_id=workspace_id)

    def list_goals(self, workspace_id: str | None = None) -> list[dict]:
        goals = [self.with_progress(item) for item in self.storage.read_list("goals.json")]
        if workspace_id:
            goals = [item for item in goals if item.get("workspace_id") == workspace_id]
        return sorted(goals, key=lambda item: item.get("updated_at") or "", reverse=True)

    def get_goal(self, goal_id: str) -> tuple[dict, dict] | None:
        goal = next((item for item in self.storage.read_list("goals.json") if item.get("goal_id") == goal_id), None)
        graph = next((item for item in self.storage.read_list("task_graphs.json") if item.get("goal_id") == goal_id), None)
        if goal is None:
            return None
        graph = graph or {"goal_id": goal_id, "tasks": []}
        return self.with_progress(goal), graph

    def update_goal(self, goal_id: str, updates: dict) -> dict | None:
        goals = self.storage.read_list("goals.json")
        goal = next((item for item in goals if item.get("goal_id") == goal_id), None)
        if goal is None:
            return None
        for key in ("title", "description", "status", "tags"):
            if key in updates and updates[key] is not None:
                goal[key] = updates[key]
        goal["updated_at"] = datetime.now(UTC).isoformat()
        self.storage.write_list("goals.json", goals)
        return self.with_progress(goal)

    def archive_goal(self, goal_id: str) -> dict | None:
        return self.update_goal(goal_id, {"status": "archived"})

    def add_task(self, goal_id: str, task_data: dict) -> GoalTask | None:
        graphs = self.storage.read_list("task_graphs.json")
        graph = next((item for item in graphs if item.get("goal_id") == goal_id), None)
        if graph is None:
            return None
        now = datetime.now(UTC).isoformat()
        task = GoalTask(
            task_id=str(uuid4()),
            title=task_data.get("title", "New task"),
            description=task_data.get("description", ""),
            phase=task_data.get("phase", "Planning"),
            status="pending",
            priority=task_data.get("priority", "medium"),
            depends_on=task_data.get("depends_on", []),
            recommended_agent=task_data.get("recommended_agent", "Strategy Agent"),
            estimated_effort=task_data.get("estimated_effort", "medium"),
            requires_approval=task_data.get("requires_approval", False),
            automation_supported=task_data.get("automation_supported", False),
            created_at=now,
            updated_at=now,
        )
        graph.setdefault("tasks", []).append(task.model_dump())
        self.storage.write_list("task_graphs.json", graphs)
        self.touch_goal(goal_id)
        return task

    def update_task(self, goal_id: str, task_id: str, updates: dict) -> GoalTask | None:
        graphs = self.storage.read_list("task_graphs.json")
        graph = next((item for item in graphs if item.get("goal_id") == goal_id), None)
        if graph is None:
            return None
        task = next((item for item in graph.get("tasks", []) if item.get("task_id") == task_id), None)
        if task is None:
            return None
        allowed = {
            "title",
            "description",
            "phase",
            "status",
            "priority",
            "depends_on",
            "recommended_agent",
            "estimated_effort",
            "requires_approval",
            "automation_supported",
            "last_run_id",
            "last_result_summary",
        }
        for key in allowed:
            if key in updates and updates[key] is not None:
                task[key] = updates[key]
        task["updated_at"] = datetime.now(UTC).isoformat()
        self.storage.write_list("task_graphs.json", graphs)
        self.touch_goal(goal_id)
        return GoalTask(**task)

    def get_task(self, goal_id: str, task_id: str) -> dict | None:
        result = self.get_goal(goal_id)
        if result is None:
            return None
        _, graph = result
        return next((item for item in graph.get("tasks", []) if item.get("task_id") == task_id), None)

    def touch_goal(self, goal_id: str) -> None:
        goals = self.storage.read_list("goals.json")
        goal = next((item for item in goals if item.get("goal_id") == goal_id), None)
        if goal is not None:
            goal["updated_at"] = datetime.now(UTC).isoformat()
            progress = self.calculate_progress(goal_id)
            goal["progress_percent"] = progress
            self.storage.write_list("goals.json", goals)

    def calculate_progress(self, goal_id: str) -> int:
        graph = next((item for item in self.storage.read_list("task_graphs.json") if item.get("goal_id") == goal_id), None)
        tasks = graph.get("tasks", []) if graph else []
        if not tasks:
            return 0
        done = sum(1 for item in tasks if item.get("status") == "done")
        return round((done / len(tasks)) * 100)

    def with_progress(self, goal: dict) -> dict:
        if goal.get("goal_id"):
            goal = {**goal, "progress_percent": self.calculate_progress(goal["goal_id"])}
        return goal
