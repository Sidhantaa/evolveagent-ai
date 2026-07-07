"""saas-builder routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    saas_builder_service,
)
from app.models.request_models import (
    SaaSFeedbackCreateRequest,
    SaaSProjectCreateRequest,
)

router = APIRouter()


# NOTE: /universal-operator/* routes were extracted into app/api/universal_operator_routes.py (services still live here).


# ----------------------------------------------------------------------
# v32.0 Autonomous SaaS Builder (planning/drafting only — no deploy/payments)
# ----------------------------------------------------------------------
@router.get("/saas-builder/dashboard")
def get_saas_builder_dashboard() -> dict:
    return saas_builder_service.dashboard()


@router.get("/saas-builder/projects")
def list_saas_projects() -> dict:
    projects = saas_builder_service.list_projects()
    return {"projects": projects, "count": len(projects)}


@router.post("/saas-builder/projects")
def create_saas_project(request: SaaSProjectCreateRequest) -> dict:
    return saas_builder_service.create_project(request.model_dump())


@router.get("/saas-builder/projects/{project_id}")
def get_saas_project(project_id: str) -> dict:
    project = saas_builder_service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _saas_step(handler, project_id: str) -> dict:
    try:
        return handler(project_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Project not found") from error


@router.post("/saas-builder/projects/{project_id}/validate")
def validate_saas_project(project_id: str) -> dict:
    return _saas_step(saas_builder_service.validate, project_id)


@router.post("/saas-builder/projects/{project_id}/roadmap")
def roadmap_saas_project(project_id: str) -> dict:
    return _saas_step(saas_builder_service.roadmap, project_id)


@router.post("/saas-builder/projects/{project_id}/architecture")
def architecture_saas_project(project_id: str) -> dict:
    return _saas_step(saas_builder_service.architecture, project_id)


@router.post("/saas-builder/projects/{project_id}/launch-assets")
def launch_assets_saas_project(project_id: str) -> dict:
    return _saas_step(saas_builder_service.launch_assets, project_id)


@router.post("/saas-builder/projects/{project_id}/feedback")
def create_saas_feedback(project_id: str, request: SaaSFeedbackCreateRequest) -> dict:
    try:
        return saas_builder_service.create_feedback(project_id, request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Project not found") from error


@router.get("/saas-builder/projects/{project_id}/feedback")
def list_saas_feedback(project_id: str) -> dict:
    if saas_builder_service.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    feedback = saas_builder_service.list_feedback(project_id)
    return {"feedback": feedback, "count": len(feedback)}
# v31.0 AI Team Lead / Manager Mode
