"""workspace-templates routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    workspace_templates_service,
)
from app.models.request_models import (
    WorkspaceTemplateCreateRequest,
    WorkspaceTemplateInstantiateRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v57.0 Workspace Templates & Cloning — local templates + instantiate.
# ----------------------------------------------------------------------
@router.get("/workspace-templates/summary")
def get_workspace_templates_summary() -> dict:
    return workspace_templates_service.summary()


@router.get("/workspace-templates")
def list_workspace_templates() -> dict:
    templates = workspace_templates_service.list_templates()
    return {"templates": templates, "count": len(templates)}


@router.post("/workspace-templates")
def create_workspace_template(request: WorkspaceTemplateCreateRequest) -> dict:
    return workspace_templates_service.create_template(request.model_dump())


@router.post("/workspace-templates/{template_id}/instantiate")
def instantiate_workspace_template(template_id: str, request: WorkspaceTemplateInstantiateRequest | None = None) -> dict:
    try:
        return workspace_templates_service.instantiate(template_id, request.model_dump() if request else {})
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Template not found") from error


# NOTE: /scheduled-tasks/* routes were extracted into app/api/scheduled_tasks_routes.py (services still live here).
