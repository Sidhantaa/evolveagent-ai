"""debate routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    debate_simulation_service,
)
from app.models.request_models import (
    DebateConsensusRequest,
    DebateCreateRequest,
)

router = APIRouter()


# NOTE: /app-builder/* routes were extracted into app/api/app_builder_routes.py (services still live here).


@router.get("/debate/summary")
def get_debate_simulation_summary(workspace_id: str | None = Query(default=None)) -> dict:
    return debate_simulation_service.summary(workspace_id)


@router.get("/debate/sessions")
def list_debate_sessions(workspace_id: str | None = Query(default=None)) -> list[dict]:
    return debate_simulation_service.list_debates(workspace_id)


@router.get("/debate/sessions/{debate_id}")
def get_debate_session(debate_id: str) -> dict:
    debate = debate_simulation_service.get_debate(debate_id)
    if not debate:
        raise HTTPException(status_code=404, detail="Debate session not found")
    return debate


@router.post("/debate/sessions")
def create_debate_session(request: DebateCreateRequest) -> dict:
    return debate_simulation_service.create_debate(
        prompt=request.prompt,
        workspace_id=request.workspace_id,
        agents=request.agents,
    )


@router.post("/debate/consensus")
def select_debate_consensus(request: DebateConsensusRequest) -> dict:
    result = debate_simulation_service.consensus_for(request.debate_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Debate session not found"))
    return result
