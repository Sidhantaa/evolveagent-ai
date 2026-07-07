"""tools routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    tool_execution_service,
    plugin_loader,
    tool_registry,
)
from app.models.request_models import (
    RegisterToolRequest,
)

router = APIRouter()


@router.get("/tools")
def list_tools(include_disabled: bool = Query(default=False)) -> list[dict]:
    plugin_loader.load_plugins()
    return tool_registry.list_tools(include_disabled=include_disabled)


@router.get("/tools/history")
def list_tool_execution_history(
    workspace_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict]:
    return tool_execution_service.list_history(workspace_id=workspace_id, limit=limit)


@router.get("/tools/summary")
def get_tool_execution_summary(workspace_id: str | None = Query(default=None)) -> dict:
    return tool_execution_service.summary(workspace_id=workspace_id)


@router.get("/tools/history/{execution_id}")
def get_tool_execution(execution_id: str) -> dict:
    execution = tool_execution_service.get(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Tool execution not found")
    return execution


@router.post("/tools/register")
def register_tool(request: RegisterToolRequest) -> dict:
    try:
        return tool_registry.register_tool(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tools/{name}")
def get_tool(name: str) -> dict:
    tool = tool_registry.get_tool(name)
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool
