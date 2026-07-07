"""chief-of-staff routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    chief_of_staff_service,
)
from app.models.request_models import (
    ChiefFollowupCreateRequest,
    ChiefFollowupUpdateRequest,
    ChiefPlanRequest,
)

router = APIRouter()


# NOTE: /business/* routes were extracted into app/api/business_routes.py (services still live here).


# ----------------------------------------------------------------------
# v19.0 AI Chief of Staff
# ----------------------------------------------------------------------
@router.get("/chief-of-staff/dashboard")
def get_chief_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    return chief_of_staff_service.dashboard(workspace_id)


@router.post("/chief-of-staff/daily-plan")
def create_chief_daily_plan(request: ChiefPlanRequest | None = None) -> dict:
    workspace_id = request.workspace_id if request else None
    return chief_of_staff_service.generate_daily_plan(workspace_id)


@router.get("/chief-of-staff/daily-plans")
def list_chief_daily_plans(workspace_id: str | None = Query(default=None)) -> dict:
    plans = chief_of_staff_service.list_daily_plans(workspace_id)
    return {"daily_plans": plans, "count": len(plans)}


@router.post("/chief-of-staff/weekly-plan")
def create_chief_weekly_plan(request: ChiefPlanRequest | None = None) -> dict:
    workspace_id = request.workspace_id if request else None
    return chief_of_staff_service.generate_weekly_plan(workspace_id)


@router.get("/chief-of-staff/weekly-plans")
def list_chief_weekly_plans(workspace_id: str | None = Query(default=None)) -> dict:
    plans = chief_of_staff_service.list_weekly_plans(workspace_id)
    return {"weekly_plans": plans, "count": len(plans)}


@router.get("/chief-of-staff/priorities")
def get_chief_priorities(workspace_id: str | None = Query(default=None)) -> dict:
    items = chief_of_staff_service.rank_priorities(workspace_id, log=True)
    return {"priority_items": items, "count": len(items)}


@router.get("/chief-of-staff/followups")
def list_chief_followups(workspace_id: str | None = Query(default=None)) -> dict:
    followups = chief_of_staff_service.list_followups(workspace_id)
    overdue = chief_of_staff_service.overdue_followups(workspace_id)
    return {"followups": followups, "count": len(followups), "overdue_count": len(overdue)}


@router.post("/chief-of-staff/followups")
def create_chief_followup(request: ChiefFollowupCreateRequest) -> dict:
    return chief_of_staff_service.create_followup(request.model_dump())


@router.patch("/chief-of-staff/followups/{followup_id}")
def update_chief_followup(followup_id: str, request: ChiefFollowupUpdateRequest) -> dict:
    try:
        return chief_of_staff_service.update_followup(followup_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Follow-up not found") from error


# NOTE: /business-simulator/* routes were extracted into app/api/business_simulator_routes.py (services still live here).
