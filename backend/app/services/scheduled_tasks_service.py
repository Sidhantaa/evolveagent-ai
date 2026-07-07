from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

SCHEDULES = ["manual", "hourly", "daily", "weekly"]
ACTION_TYPES = ["plan", "note", "approval_required"]
# Nominal seconds per schedule for "due" estimation (informational only).
_SCHEDULE_SECONDS = {"hourly": 3600, "daily": 86400, "weekly": 604800}


class ScheduledTasksService:
    """v58.0 Scheduled Tasks (local, planning-first) — v120: real triggers.

    A local registry of scheduled tasks. A task records a schedule (manual/
    hourly/daily/weekly) and an action. There is still **no daemon by default**:
    ``due_tasks`` is informational only, and firing a task only ever happens via
    an explicit ``trigger()`` call — either a user/API call, or (v120, opt-in)
    ``SchedulerTickWorker`` periodically calling ``trigger()`` for due tasks.

    v120: a task may declare a ``workflow_definition_id`` (from
    ``DurableWorkflowService``). When set, ``trigger`` starts a **real** durable
    workflow run instead of the original planning-first mock note — but that run
    is still governed entirely by the workflow engine's own rules: risky/action
    steps still halt at ``waiting_approval`` and are never auto-approved just
    because a schedule fired them. Tasks without a linked workflow behave exactly
    as before (unchanged, backward-compatible mock run). Stateful actions are
    governance-logged.
    """

    tasks_file = "scheduled_tasks.json"
    runs_file = "scheduled_task_runs.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, workflows=None):
        self.storage = storage
        self.governance = governance_service
        # Optional DurableWorkflowService — enables real (still approval-gated) runs.
        self.workflows = workflows

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _enum(self, value, allowed: list[str], default: str) -> str:
        candidate = str(value or "").strip().lower()
        return candidate if candidate in allowed else default

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="scheduled_tasks",
                agent_name="Scheduled Tasks",
                action_type=action_type,
                tool_used="ScheduledTasksService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=3,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------
    def create_task(self, data: dict) -> dict:
        data = data or {}
        task = {
            "task_id": str(uuid4()),
            "name": self._clean(data.get("name"), 160) or "Scheduled task",
            "schedule": self._enum(data.get("schedule"), SCHEDULES, "manual"),
            "action_type": self._enum(data.get("action_type"), ACTION_TYPES, "plan"),
            "detail": self._clean(data.get("detail"), 2000),
            "workflow_definition_id": self._clean(data.get("workflow_definition_id"), 80) or None,
            "enabled": bool(data.get("enabled", True)),
            "last_triggered_at": None,
            "trigger_count": 0,
            "created_at": self._now(),
        }
        self.storage.append(self.tasks_file, task)
        self._log("scheduled_task_created", f"Created scheduled task '{task['name']}' ({task['schedule']}).")
        return task

    def list_tasks(self) -> list[dict]:
        return self.storage.read_list(self.tasks_file)

    def get_task(self, task_id: str) -> dict | None:
        return next((t for t in self.list_tasks() if t.get("task_id") == task_id), None)

    def set_enabled(self, task_id: str, enabled: bool) -> dict:
        tasks = self.list_tasks()
        task = next((t for t in tasks if t.get("task_id") == task_id), None)
        if task is None:
            raise ValueError("Task not found")
        task["enabled"] = bool(enabled)
        self.storage.write_list(self.tasks_file, tasks)
        self._log("scheduled_task_updated", f"{'Enabled' if enabled else 'Disabled'} scheduled task {task_id}.")
        return task

    # ------------------------------------------------------------------
    # Trigger (planning-first mock run — never real background execution)
    # ------------------------------------------------------------------
    def trigger(self, task_id: str) -> dict:
        tasks = self.list_tasks()
        task = next((t for t in tasks if t.get("task_id") == task_id), None)
        if task is None:
            raise ValueError("Task not found")
        if not task.get("enabled", True):
            raise ValueError("Task is disabled")

        workflow_definition_id = task.get("workflow_definition_id")
        if workflow_definition_id and self.workflows is not None:
            run = self._trigger_real_workflow(task_id, task, workflow_definition_id)
        else:
            run = self._trigger_mock(task_id, task)

        task["last_triggered_at"] = self._now()
        task["trigger_count"] = task.get("trigger_count", 0) + 1
        self.storage.write_list(self.tasks_file, tasks)
        self._log("scheduled_task_triggered", f"Triggered scheduled task {task_id} → {run['status']}.")
        return run

    def _trigger_mock(self, task_id: str, task: dict) -> dict:
        """Original planning-first mock run — unchanged for tasks with no linked workflow."""
        action_type = task.get("action_type")
        if action_type == "approval_required":
            status, note = "approval_required", "Risky action — held for explicit human approval; not executed."
        elif action_type == "note":
            status, note = "noted", "Informational scheduled step."
        else:
            status, note = "planned", "Planned (mock) — no real action performed."
        run = {
            "run_id": str(uuid4()),
            "task_id": task_id,
            "task_name": task.get("name"),
            "status": status,
            "executed": False,
            "workflow_run_id": None,
            "note": note,
            "created_at": self._now(),
        }
        self.storage.append(self.runs_file, run)
        return run

    def _trigger_real_workflow(self, task_id: str, task: dict, workflow_definition_id: str) -> dict:
        """v120: start a REAL durable workflow run. Still fully governed by that
        engine's own approval gates — firing a schedule is not an approval."""
        try:
            workflow_run = self.workflows.start_run({"definition_id": workflow_definition_id})
            status = workflow_run.get("status", "running")
            note = (f"Started durable workflow run (status={status}). "
                    "Any risky/action step still halts for explicit approval.")
            executed = status == "completed"
        except ValueError as exc:
            status, note, executed = "failed", f"Could not start linked workflow: {exc}", False
            workflow_run = None
        run = {
            "run_id": str(uuid4()),
            "task_id": task_id,
            "task_name": task.get("name"),
            "status": status,
            "executed": executed,
            "workflow_run_id": (workflow_run or {}).get("run_id"),
            "note": note,
            "created_at": self._now(),
        }
        self.storage.append(self.runs_file, run)
        return run

    def list_runs(self, task_id: str | None = None, limit: int = 50) -> list[dict]:
        runs = self.storage.read_list(self.runs_file)
        if task_id:
            runs = [r for r in runs if r.get("task_id") == task_id]
        return list(reversed(runs[-limit:]))

    # ------------------------------------------------------------------
    # Due (informational only — never auto-runs)
    # ------------------------------------------------------------------
    def _is_due(self, task: dict) -> bool:
        if not task.get("enabled", True) or task.get("schedule") == "manual":
            return False
        seconds = _SCHEDULE_SECONDS.get(task.get("schedule"), 0)
        if not seconds:
            return False
        last = task.get("last_triggered_at")
        if not last:
            return True
        try:
            last_dt = datetime.fromisoformat(last)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=UTC)
        except (ValueError, TypeError):
            return True
        return (datetime.now(UTC) - last_dt).total_seconds() >= seconds

    def due_tasks(self) -> list[dict]:
        return [{"task_id": t["task_id"], "name": t.get("name"), "schedule": t.get("schedule")} for t in self.list_tasks() if self._is_due(t)]

    # ------------------------------------------------------------------
    # Summary + analytics
    # ------------------------------------------------------------------
    def summary(self) -> dict:
        tasks = self.list_tasks()
        return {
            "task_count": len(tasks),
            "enabled_count": sum(1 for t in tasks if t.get("enabled", True)),
            "due_count": len(self.due_tasks()),
            "run_count": len(self.storage.read_list(self.runs_file)),
            "note": "Planning-first — no real background scheduler or execution. Triggers produce mock/planned runs; risky steps require approval.",
        }

    def analytics_summary(self) -> dict:
        return {
            "scheduled_tasks": len(self.list_tasks()),
            "scheduled_task_runs": len(self.storage.read_list(self.runs_file)),
            "scheduled_tasks_due": len(self.due_tasks()),
        }
