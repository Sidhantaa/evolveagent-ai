"""Agent Registry routes — unified read-only agent discovery (v100)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.routes import agent_registry_service

router = APIRouter()


@router.get("/agent-registry")
def agent_registry_list(source: str | None = None, q: str | None = None, limit: int = 200) -> dict:
    return agent_registry_service.list_agents(source, q, limit)


@router.get("/agent-registry/summary")
def agent_registry_summary() -> dict:
    return agent_registry_service.summary()


@router.get("/agent-registry/{registry_id:path}")
def agent_registry_get(registry_id: str) -> dict:
    try:
        return agent_registry_service.get(registry_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
