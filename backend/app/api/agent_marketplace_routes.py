"""agent-marketplace routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    agent_marketplace_service,
    workspace_service,
)
from app.models.request_models import (
    AgentPackInstallRequest,
    AgentTeamCreateRequest,
    AgentTeamImportRequest,
    AgentTeamRatingRequest,
    AgentTeamUpdateRequest,
)

router = APIRouter()


@router.get("/agent-marketplace/dashboard")
def get_agent_marketplace_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    return agent_marketplace_service.dashboard(workspace_id=workspace_id)


@router.get("/agent-marketplace/packs")
def list_agent_marketplace_packs() -> list[dict]:
    return agent_marketplace_service.list_packs()


@router.get("/agent-marketplace/packs/{pack_id}")
def get_agent_marketplace_pack(pack_id: str) -> dict:
    pack = agent_marketplace_service.get_pack(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="Agent skill pack not found")
    return pack


@router.get("/agent-marketplace/permission-profiles")
def list_agent_marketplace_permission_profiles() -> list[dict]:
    return agent_marketplace_service.permission_profiles()


@router.get("/agent-marketplace/teams")
def list_agent_marketplace_teams(workspace_id: str | None = Query(default=None)) -> list[dict]:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return agent_marketplace_service.list_teams(workspace_id=resolved)


@router.post("/agent-marketplace/teams")
def create_agent_marketplace_team(request: AgentTeamCreateRequest) -> dict:
    return agent_marketplace_service.create_team(request.model_dump())


@router.patch("/agent-marketplace/teams/{team_id}")
def update_agent_marketplace_team(team_id: str, request: AgentTeamUpdateRequest) -> dict:
    team = agent_marketplace_service.update_team(team_id, request.model_dump(exclude_unset=True))
    if team is None:
        raise HTTPException(status_code=404, detail="Agent team not found")
    return team


@router.post("/agent-marketplace/teams/import")
def import_agent_marketplace_team(request: AgentTeamImportRequest) -> dict:
    return agent_marketplace_service.import_team(request.payload, workspace_id=request.workspace_id)


@router.get("/agent-marketplace/teams/{team_id}/export")
def export_agent_marketplace_team(team_id: str) -> dict:
    exported = agent_marketplace_service.export_team(team_id)
    if exported is None:
        raise HTTPException(status_code=404, detail="Agent team not found")
    return exported


@router.post("/agent-marketplace/teams/{team_id}/rate")
def rate_agent_marketplace_team(team_id: str, request: AgentTeamRatingRequest) -> dict:
    try:
        return agent_marketplace_service.rate_team(
            team_id=team_id,
            rating=request.rating,
            review=request.review or "",
            workspace_id=request.workspace_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/agent-marketplace/packs/{pack_id}/install")
def install_agent_marketplace_pack(pack_id: str, request: AgentPackInstallRequest) -> dict:
    try:
        return agent_marketplace_service.install_pack(pack_id=pack_id, workspace_id=request.workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
