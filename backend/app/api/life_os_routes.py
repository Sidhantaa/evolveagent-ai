"""life-os routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    life_os_service,
)
from app.models.request_models import (
    LifeDailyPlanRequest,
    LifeDeadlineCreateRequest,
    LifeReminderCreateRequest,
    LifeScheduleCreateRequest,
    LifeTaskCreateRequest,
    LifeTaskUpdateRequest,
)

router = APIRouter()


# NOTE: /avatar/* routes were extracted into app/api/avatar_routes.py (services still live here).


# ----------------------------------------------------------------------
# v29.0 Real-Time Life Operating System (local planning — no calendar/email)
# ----------------------------------------------------------------------
@router.get("/life-os/dashboard")
def get_life_os_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    return life_os_service.dashboard(workspace_id)


@router.get("/life-os/schedule")
def list_life_schedule(workspace_id: str | None = Query(default=None)) -> dict:
    items = life_os_service.list_schedule(workspace_id)
    return {"schedule": items, "count": len(items)}


@router.post("/life-os/schedule")
def create_life_schedule(request: LifeScheduleCreateRequest) -> dict:
    return life_os_service.create_schedule_item(request.model_dump())


@router.get("/life-os/tasks")
def list_life_tasks(workspace_id: str | None = Query(default=None)) -> dict:
    tasks = life_os_service.list_tasks(workspace_id)
    ranked = life_os_service.ranked_tasks(workspace_id)
    return {"tasks": tasks, "ranked": ranked, "count": len(tasks)}


@router.post("/life-os/tasks")
def create_life_task(request: LifeTaskCreateRequest) -> dict:
    return life_os_service.create_task(request.model_dump())


@router.patch("/life-os/tasks/{task_id}")
def update_life_task(task_id: str, request: LifeTaskUpdateRequest) -> dict:
    try:
        return life_os_service.update_task(task_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Task not found") from error


@router.get("/life-os/reminders")
def list_life_reminders(workspace_id: str | None = Query(default=None)) -> dict:
    reminders = life_os_service.list_reminders(workspace_id)
    return {"reminders": reminders, "count": len(reminders)}


@router.post("/life-os/reminders")
def create_life_reminder(request: LifeReminderCreateRequest) -> dict:
    return life_os_service.create_reminder(request.model_dump())


@router.get("/life-os/deadlines")
def list_life_deadlines(workspace_id: str | None = Query(default=None)) -> dict:
    deadlines = life_os_service.list_deadlines(workspace_id)
    return {"deadlines": deadlines, "count": len(deadlines)}


@router.post("/life-os/deadlines")
def create_life_deadline(request: LifeDeadlineCreateRequest) -> dict:
    return life_os_service.create_deadline(request.model_dump())


@router.post("/life-os/daily-plan")
def create_life_daily_plan(request: LifeDailyPlanRequest | None = None) -> dict:
    workspace_id = request.workspace_id if request else None
    return life_os_service.generate_daily_plan(workspace_id)
