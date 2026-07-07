"""learning routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    workspace_service,
    learning_agent,
    prompt_versions,
)
from app.models.request_models import (
    PromptDecisionRequest,
    PromptProposalRequest,
)

router = APIRouter()


@router.get("/learning/report")
def get_learning_report(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return learning_agent.report(workspace_id=resolved)


# NOTE: /digital-twin/* routes were extracted into app/api/digital_twin_routes.py (services still live here).


@router.get("/learning/prompt-versions")
def get_prompt_versions() -> list[dict]:
    return prompt_versions.list_versions()


@router.post("/learning/propose-prompt")
def propose_prompt(request: PromptProposalRequest) -> dict:
    return prompt_versions.propose(request.agent_name, request.reason, request.proposed_prompt)


@router.post("/learning/approve-prompt")
def approve_prompt(request: PromptDecisionRequest) -> dict:
    try:
        return prompt_versions.set_status(request.agent_name, request.version_id, "active")
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/learning/reject-prompt")
def reject_prompt(request: PromptDecisionRequest) -> dict:
    try:
        return prompt_versions.set_status(request.agent_name, request.version_id, "rejected")
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/learning/rollback-prompt")
def rollback_prompt(request: PromptDecisionRequest) -> dict:
    try:
        return prompt_versions.rollback(request.agent_name, request.version_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
