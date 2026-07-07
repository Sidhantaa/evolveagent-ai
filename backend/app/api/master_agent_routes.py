"""master-agent routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    master_agent_service,
)
from app.models.request_models import (
    MasterAgentRouteRequest,
    MasterRouteFeedbackRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# Master Agent — one top-level AI surface routing across all of v1–v60.
# ----------------------------------------------------------------------
@router.post("/master-agent/route")
def master_agent_route(request: MasterAgentRouteRequest) -> dict:
    return master_agent_service.route(
        request.text,
        workspace_id=request.workspace_id,
        voice_used=request.voice_used,
        execute=request.execute,
    )


@router.get("/master-agent/capabilities")
def master_agent_capabilities() -> dict:
    return master_agent_service.capabilities()


@router.post("/master-agent/route/{run_id}/feedback")
def master_agent_route_feedback(run_id: str, request: MasterRouteFeedbackRequest) -> dict:
    try:
        return master_agent_service.record_feedback(run_id, request.correct, request.note, request.correct_domain)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/master-agent/summary")
def master_agent_summary() -> dict:
    return master_agent_service.summary()
