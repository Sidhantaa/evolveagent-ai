from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

TASK_PRIORITIES = ["low", "medium", "high"]
TASK_STATUSES = ["todo", "in_progress", "done", "archived"]
IMPORTANCE = ["low", "medium", "high"]
REMINDER_STATUSES = ["open", "done", "snoozed"]
DEADLINE_KINDS = ["school", "work", "personal", "other"]
PRIORITY_WEIGHT = {"low": 1, "medium": 2, "high": 3}


class LifeOSService:
    """v29.0 Real-Time Life Operating System (local planning layer).

    Manages personal schedule items, tasks, reminders/follow-ups, and
    school/work deadlines, and generates a daily plan with a priority ranking.
    Everything is local JSON — there is NO real calendar/email integration and
    nothing is sent anywhere. Stateful actions are governance-logged.
    """

    schedule_file = "life_schedule_items.json"
    tasks_file = "life_tasks.json"
    reminders_file = "life_reminders.json"
    deadlines_file = "life_deadlines.json"
    plans_file = "life_plans.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _today(self):
        return datetime.now(UTC).date()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _enum(self, value, allowed: list[str], default: str) -> str:
        candidate = str(value or "").strip().lower()
        return candidate if candidate in allowed else default

    def _parse_date(self, value):
        if not value:
            return None
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def _days_until(self, value):
        parsed = self._parse_date(value)
        return None if parsed is None else (parsed - self._today()).days

    def _filter_workspace(self, items, workspace_id):
        if not workspace_id:
            return items
        return [item for item in items if item.get("workspace_id") == workspace_id]

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="life_os",
                agent_name="Life OS",
                action_type=action_type,
                tool_used="LifeOSService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Schedule
    # ------------------------------------------------------------------
    def create_schedule_item(self, data: dict) -> dict:
        item = {
            "schedule_id": str(uuid4()),
            "workspace_id": data.get("workspace_id"),
            "title": self._clean(data.get("title"), 200),
            "date": self._clean(data.get("date"), 10) or None,
            "start_time": self._clean(data.get("start_time"), 10),
            "end_time": self._clean(data.get("end_time"), 10),
            "location": self._clean(data.get("location"), 200),
            "notes": self._clean(data.get("notes"), 1000),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.schedule_file, item)
        self._log("life_schedule_created", f"Created schedule item: {item['title'] or item['schedule_id']}.")
        return item

    def list_schedule(self, workspace_id=None) -> list[dict]:
        return self._filter_workspace(self.storage.read_list(self.schedule_file), workspace_id)

    # ------------------------------------------------------------------
    # Tasks (with priority ranking)
    # ------------------------------------------------------------------
    def create_task(self, data: dict) -> dict:
        task = {
            "task_id": str(uuid4()),
            "workspace_id": data.get("workspace_id"),
            "title": self._clean(data.get("title"), 200),
            "due_date": self._clean(data.get("due_date"), 10) or None,
            "priority": self._enum(data.get("priority"), TASK_PRIORITIES, "medium"),
            "importance": self._enum(data.get("importance"), IMPORTANCE, "medium"),
            "status": self._enum(data.get("status"), TASK_STATUSES, "todo"),
            "notes": self._clean(data.get("notes"), 1000),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.tasks_file, task)
        self._log("life_task_created", f"Created task: {task['title'] or task['task_id']}.")
        return task

    def list_tasks(self, workspace_id=None) -> list[dict]:
        return self._filter_workspace(self.storage.read_list(self.tasks_file), workspace_id)

    def update_task(self, task_id: str, updates: dict) -> dict:
        tasks = self.storage.read_list(self.tasks_file)
        task = next((t for t in tasks if t.get("task_id") == task_id), None)
        if task is None:
            raise ValueError("Task not found")
        if updates.get("title") is not None:
            task["title"] = self._clean(updates["title"], 200)
        if updates.get("due_date") is not None:
            task["due_date"] = self._clean(updates["due_date"], 10) or None
        if updates.get("priority") is not None:
            task["priority"] = self._enum(updates["priority"], TASK_PRIORITIES, task["priority"])
        if updates.get("importance") is not None:
            task["importance"] = self._enum(updates["importance"], IMPORTANCE, task["importance"])
        if updates.get("status") is not None:
            task["status"] = self._enum(updates["status"], TASK_STATUSES, task["status"])
        if updates.get("notes") is not None:
            task["notes"] = self._clean(updates["notes"], 1000)
        task["updated_at"] = self._now()
        self.storage.write_list(self.tasks_file, tasks)
        self._log("life_task_updated", f"Updated task {task_id}.")
        return task

    def _task_score(self, task: dict) -> int:
        score = PRIORITY_WEIGHT.get(task.get("priority", "medium"), 2) * 10
        score += PRIORITY_WEIGHT.get(task.get("importance", "medium"), 2) * 6
        days = self._days_until(task.get("due_date"))
        if days is not None:
            if days < 0:
                score += 30  # overdue
            elif days == 0:
                score += 25  # due today
            elif days <= 2:
                score += 15
            elif days <= 7:
                score += 6
        return score

    def ranked_tasks(self, workspace_id=None) -> list[dict]:
        active = [t for t in self.list_tasks(workspace_id) if t.get("status") in {"todo", "in_progress"}]
        ranked = []
        for task in active:
            days = self._days_until(task.get("due_date"))
            ranked.append(
                {
                    "task_id": task.get("task_id"),
                    "title": task.get("title"),
                    "priority": task.get("priority"),
                    "importance": task.get("importance"),
                    "due_date": task.get("due_date"),
                    "days_until_due": days,
                    "overdue": days is not None and days < 0,
                    "priority_score": self._task_score(task),
                }
            )
        ranked.sort(key=lambda item: item["priority_score"], reverse=True)
        return ranked

    # ------------------------------------------------------------------
    # Reminders
    # ------------------------------------------------------------------
    def create_reminder(self, data: dict) -> dict:
        reminder = {
            "reminder_id": str(uuid4()),
            "workspace_id": data.get("workspace_id"),
            "title": self._clean(data.get("title"), 200),
            "remind_on": self._clean(data.get("remind_on"), 10) or None,
            "status": self._enum(data.get("status"), REMINDER_STATUSES, "open"),
            "notes": self._clean(data.get("notes"), 1000),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.reminders_file, reminder)
        self._log("life_reminder_created", f"Created reminder: {reminder['title'] or reminder['reminder_id']}.")
        return reminder

    def list_reminders(self, workspace_id=None) -> list[dict]:
        return self._filter_workspace(self.storage.read_list(self.reminders_file), workspace_id)

    def _due_reminders(self, workspace_id=None) -> list[dict]:
        due = []
        for reminder in self.list_reminders(workspace_id):
            if reminder.get("status") != "open":
                continue
            days = self._days_until(reminder.get("remind_on"))
            if days is not None and days <= 0:
                due.append(reminder)
        return due

    # ------------------------------------------------------------------
    # Deadlines (school/work)
    # ------------------------------------------------------------------
    def create_deadline(self, data: dict) -> dict:
        deadline = {
            "deadline_id": str(uuid4()),
            "workspace_id": data.get("workspace_id"),
            "title": self._clean(data.get("title"), 200),
            "kind": self._enum(data.get("kind"), DEADLINE_KINDS, "other"),
            "due_date": self._clean(data.get("due_date"), 10) or None,
            "course_or_project": self._clean(data.get("course_or_project"), 200),
            "notes": self._clean(data.get("notes"), 1000),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.deadlines_file, deadline)
        self._log("life_deadline_created", f"Created {deadline['kind']} deadline: {deadline['title'] or deadline['deadline_id']}.")
        return deadline

    def list_deadlines(self, workspace_id=None) -> list[dict]:
        deadlines = self._filter_workspace(self.storage.read_list(self.deadlines_file), workspace_id)
        for deadline in deadlines:
            deadline["days_until_due"] = self._days_until(deadline.get("due_date"))
        deadlines.sort(key=lambda item: (item.get("days_until_due") is None, item.get("days_until_due") if item.get("days_until_due") is not None else 0))
        return deadlines

    def _upcoming_deadlines(self, workspace_id=None, within_days: int = 14) -> list[dict]:
        upcoming = []
        for deadline in self.list_deadlines(workspace_id):
            days = deadline.get("days_until_due")
            if days is not None and days <= within_days:
                upcoming.append(deadline)
        return upcoming

    # ------------------------------------------------------------------
    # Daily plan
    # ------------------------------------------------------------------
    def generate_daily_plan(self, workspace_id=None) -> dict:
        today = self._today().isoformat()
        todays_schedule = [s for s in self.list_schedule(workspace_id) if (s.get("date") or "")[:10] == today]
        ranked = self.ranked_tasks(workspace_id)
        due_reminders = self._due_reminders(workspace_id)
        upcoming_deadlines = self._upcoming_deadlines(workspace_id)
        plan = {
            "plan_id": str(uuid4()),
            "workspace_id": workspace_id,
            "date": today,
            "summary": (
                f"{len(todays_schedule)} event(s) today, {len(ranked)} active task(s), "
                f"{len(due_reminders)} reminder(s) due, {len(upcoming_deadlines)} deadline(s) within 2 weeks."
            ),
            "schedule_today": todays_schedule,
            "top_tasks": ranked[:5],
            "reminders_due": due_reminders,
            "upcoming_deadlines": upcoming_deadlines[:5],
            "focus_suggestion": ranked[0]["title"] if ranked else "No active tasks — add tasks or review your week.",
            "created_at": self._now(),
        }
        self.storage.append(self.plans_file, plan)
        self._log("life_daily_plan_created", f"Generated Life OS daily plan for {today}.")
        return plan

    def list_daily_plans(self, workspace_id=None, limit: int = 20) -> list[dict]:
        return list(reversed(self._filter_workspace(self.storage.read_list(self.plans_file), workspace_id)[-limit:]))

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard(self, workspace_id=None) -> dict:
        tasks = self.list_tasks(workspace_id)
        ranked = self.ranked_tasks(workspace_id)
        return {
            "today": self._today().isoformat(),
            "schedule_item_count": len(self.list_schedule(workspace_id)),
            "active_task_count": len(ranked),
            "completed_task_count": sum(1 for t in tasks if t.get("status") == "done"),
            "overdue_task_count": sum(1 for t in ranked if t.get("overdue")),
            "open_reminder_count": sum(1 for r in self.list_reminders(workspace_id) if r.get("status") == "open"),
            "reminders_due_count": len(self._due_reminders(workspace_id)),
            "deadline_count": len(self.list_deadlines(workspace_id)),
            "upcoming_deadline_count": len(self._upcoming_deadlines(workspace_id)),
            "top_tasks": ranked[:5],
            "recommended_next_action": (
                ranked[0]["title"] if ranked else "Add a task or schedule item to start planning your day."
            ),
        }
