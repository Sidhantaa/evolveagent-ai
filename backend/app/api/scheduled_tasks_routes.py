"""scheduled-tasks routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from app.api.routes import (
    scheduled_tasks_service,
    scheduler_tick_worker,
)
from app.models.request_models import (
    ScheduledTaskCreateRequest,
    ScheduledTaskToggleRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v58.0 Scheduled Tasks — local registry, planning-first triggers (no daemon).
# v120: an optional workflow_definition_id makes trigger() start a real
# (still approval-gated) durable workflow run; the tick worker below is the
# first real background scheduler in the app, opt-in and off by default.
# ----------------------------------------------------------------------
@router.get("/scheduled-tasks/summary")
def get_scheduled_tasks_summary() -> dict:
    return scheduled_tasks_service.summary()


@router.get("/scheduled-tasks/tick-status")
def get_scheduler_tick_status() -> dict:
    return scheduler_tick_worker.status()


@router.post("/scheduled-tasks/tick-now")
def run_scheduler_tick_now() -> dict:
    """Manually run one tick (fires currently-due tasks) without waiting for the
    background loop — useful for testing/demoing even when the loop is off."""
    fired = scheduler_tick_worker.tick_once()
    return {"fired": fired, "count": len(fired)}


@router.get("/scheduled-tasks/runs")
def list_scheduled_task_runs(task_id: str | None = Query(default=None)) -> dict:
    runs = scheduled_tasks_service.list_runs(task_id)
    return {"runs": runs, "count": len(runs)}


@router.get("/scheduled-tasks")
def list_scheduled_tasks() -> dict:
    tasks = scheduled_tasks_service.list_tasks()
    return {"tasks": tasks, "count": len(tasks)}


@router.post("/scheduled-tasks")
def create_scheduled_task(request: ScheduledTaskCreateRequest) -> dict:
    return scheduled_tasks_service.create_task(request.model_dump())


@router.patch("/scheduled-tasks/{task_id}")
def toggle_scheduled_task(task_id: str, request: ScheduledTaskToggleRequest) -> dict:
    try:
        return scheduled_tasks_service.set_enabled(task_id, request.enabled)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Task not found") from error


@router.post("/scheduled-tasks/{task_id}/trigger")
def trigger_scheduled_task(task_id: str) -> dict:
    try:
        return scheduled_tasks_service.trigger(task_id)
    except ValueError as error:
        detail = str(error)
        status = 404 if "not found" in detail.lower() else 409
        raise HTTPException(status_code=status, detail=detail) from error
