"""agent-studio routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    agent_profile_service,
)
from app.models.request_models import (
    AgentImportRequest,
    AgentProfileRequest,
    AgentRollbackRequest,
    AgentTestRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# Agent Studio (Phase 2) — build-your-own-agent (config-only, mock test/eval).
# ----------------------------------------------------------------------
@router.get("/agent-studio/templates")
def agent_studio_templates() -> dict:
    return agent_profile_service.templates()


@router.get("/agent-studio/agents")
def agent_studio_list() -> dict:
    return agent_profile_service.list_agents()


@router.post("/agent-studio/agents")
def agent_studio_create(request: AgentProfileRequest) -> dict:
    return agent_profile_service.create(request.model_dump())


@router.get("/agent-studio/agents/{agent_id}")
def agent_studio_get(agent_id: str) -> dict:
    try:
        return agent_profile_service.get(agent_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.put("/agent-studio/agents/{agent_id}")
def agent_studio_update(agent_id: str, request: AgentProfileRequest) -> dict:
    try:
        return agent_profile_service.update(agent_id, request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/agent-studio/agents/{agent_id}/test")
def agent_studio_test(agent_id: str, request: AgentTestRequest) -> dict:
    try:
        return agent_profile_service.test(agent_id, request.prompt)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/agent-studio/agents/{agent_id}/evaluate")
def agent_studio_evaluate(agent_id: str) -> dict:
    try:
        return agent_profile_service.evaluate(agent_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/agent-studio/agents/{agent_id}/publish-local")
def agent_studio_publish(agent_id: str) -> dict:
    try:
        return agent_profile_service.publish_local(agent_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/agent-studio/agents/{agent_id}/duplicate")
def agent_studio_duplicate(agent_id: str) -> dict:
    try:
        return agent_profile_service.duplicate(agent_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/agent-studio/agents/{agent_id}/versions")
def agent_studio_versions(agent_id: str) -> dict:
    try:
        return agent_profile_service.versions(agent_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/agent-studio/agents/{agent_id}/rollback")
def agent_studio_rollback(agent_id: str, request: AgentRollbackRequest) -> dict:
    try:
        return agent_profile_service.rollback(agent_id, request.version)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/agent-studio/agents/{agent_id}/preview")
def agent_studio_preview(agent_id: str) -> dict:
    try:
        return agent_profile_service.preview(agent_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/agent-studio/import")
def agent_studio_import(request: AgentImportRequest) -> dict:
    try:
        return agent_profile_service.import_profile(request.profile)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/agent-studio/summary")
def agent_studio_summary() -> dict:
    return agent_profile_service.summary()


# NOTE: Voice Console, Durable Workflows and Marketplace Hub routes were
# extracted into app/api/feature_routes.py (services still live here).


# NOTE: Design Agent, Git reader, Repo Finder, Adaptive Learning and Today routes
# were extracted into app/api/discovery_routes.py (services still live here).
