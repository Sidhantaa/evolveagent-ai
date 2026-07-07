"""industry-modes routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    industry_mode_service,
)
from app.models.request_models import (
    IndustryModeRunRequest,
    IndustryModeUpdateRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v22.0 Industry Workflow Modes
# ----------------------------------------------------------------------
@router.get("/industry-modes/dashboard")
def get_industry_modes_dashboard() -> dict:
    return industry_mode_service.dashboard()


@router.get("/industry-modes/runs")
def list_industry_mode_runs() -> dict:
    runs = industry_mode_service.list_runs()
    return {"runs": runs, "count": len(runs)}


@router.post("/industry-modes/seed")
def seed_industry_modes() -> dict:
    return industry_mode_service.seed_modes()


@router.get("/industry-modes")
def list_industry_modes() -> dict:
    modes = industry_mode_service.list_modes()
    return {"modes": modes, "count": len(modes)}


@router.get("/industry-modes/{mode_id}")
def get_industry_mode(mode_id: str) -> dict:
    mode = industry_mode_service.get_mode(mode_id)
    if mode is None:
        raise HTTPException(status_code=404, detail="Mode not found")
    return mode


@router.patch("/industry-modes/{mode_id}")
def update_industry_mode(mode_id: str, request: IndustryModeUpdateRequest) -> dict:
    try:
        return industry_mode_service.update_mode(mode_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Mode not found") from error


@router.post("/industry-modes/{mode_id}/run")
def run_industry_mode(mode_id: str, request: IndustryModeRunRequest) -> dict:
    try:
        return industry_mode_service.run_mode(mode_id, request.prompt, request.workspace_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Mode not found") from error


# NOTE: /agent-network/* routes were extracted into app/api/agent_network_routes.py (services still live here).
