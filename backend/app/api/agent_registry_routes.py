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


@router.get("/agent-registry/find-capable")
def agent_registry_find_capable(
    capability: str | None = None, source: str | None = None,
    exclude_approval_gated: bool = False, limit: int = 20,
) -> dict:
    # Registered before the {registry_id:path} catch-all below so "find-capable"
    # is never swallowed as a registry_id.
    candidates = agent_registry_service.find_capable(capability, source, exclude_approval_gated, limit)
    return {"candidates": candidates, "count": len(candidates)}


@router.get("/agent-registry/{registry_id:path}")
def agent_registry_get(registry_id: str) -> dict:
    try:
        return agent_registry_service.get(registry_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
