"""system-prompts routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    system_prompt_registry,
)
from app.models.request_models import (
    UpdateSystemPromptRequest,
)

router = APIRouter()


# NOTE: /agent-jobs/* routes were extracted into app/api/agent_jobs_routes.py (services still live here).


@router.get("/system-prompts")
def list_system_prompts() -> list[dict]:
    return system_prompt_registry.list_prompts()


@router.get("/system-prompts/{agent_name}")
def get_system_prompt(agent_name: str) -> dict:
    prompt = system_prompt_registry.get_prompt(agent_name)
    if not prompt:
        raise HTTPException(status_code=404, detail="System prompt not found")
    return {"agent_name": agent_name, "prompt": prompt}


@router.post("/system-prompts")
def upsert_system_prompt(request: UpdateSystemPromptRequest) -> dict:
    return system_prompt_registry.upsert_prompt(request.agent_name, request.prompt, request.reason)
