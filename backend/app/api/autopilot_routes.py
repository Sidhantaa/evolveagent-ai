"""autopilot routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from app.api.routes import (
    autopilot_service,
    get_settings,
    update_settings,
)
from app.models.request_models import (
    AutopilotCheckpointDecisionRequest,
    AutopilotRunControlRequest,
    AutopilotRunCreateRequest,
    AutopilotSettingsUpdateRequest,
)

router = APIRouter()


@router.get("/autopilot/settings")
def get_autopilot_settings() -> dict:
    return autopilot_service.get_settings()


@router.patch("/autopilot/settings")
def update_autopilot_settings(request: AutopilotSettingsUpdateRequest) -> dict:
    try:
        return autopilot_service.update_settings(request.model_dump(exclude_none=True))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/autopilot/runs")
def create_autopilot_run(request: AutopilotRunCreateRequest) -> dict:
    return autopilot_service.create_run(
        prompt=request.prompt,
        workspace_id=request.workspace_id,
        mode=request.mode,
        actions=[action.model_dump() for action in request.actions],
    )


@router.get("/autopilot/runs")
def list_autopilot_runs(workspace_id: str | None = Query(default=None)) -> list[dict]:
    return autopilot_service.list_runs(workspace_id)


@router.get("/autopilot/runs/{run_id}")
def get_autopilot_run(run_id: str) -> dict:
    run = autopilot_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Autopilot run not found")
    return run


@router.post("/autopilot/runs/{run_id}/start")
def start_autopilot_run(run_id: str) -> dict:
    try:
        return autopilot_service.start_run(run_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/autopilot/runs/{run_id}/stop")
def stop_autopilot_run(run_id: str, request: AutopilotRunControlRequest | None = None) -> dict:
    try:
        return autopilot_service.stop_run(run_id, reason=request.reason if request else None)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/autopilot/actions")
def list_autopilot_actions(
    run_id: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
) -> list[dict]:
    return autopilot_service.list_actions(run_id=run_id, workspace_id=workspace_id)


@router.get("/autopilot/checkpoints")
def list_autopilot_checkpoints(
    run_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
) -> list[dict]:
    return autopilot_service.list_checkpoints(run_id=run_id, status=status, workspace_id=workspace_id)


@router.post("/autopilot/checkpoints/{checkpoint_id}/decision")
def decide_autopilot_checkpoint(checkpoint_id: str, request: AutopilotCheckpointDecisionRequest) -> dict:
    try:
        return autopilot_service.decide_checkpoint(checkpoint_id, request.decision, request.comment)
    except ValueError as error:
        status_code = 404 if "not found" in str(error).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(error)) from error
