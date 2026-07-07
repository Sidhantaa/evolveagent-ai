"""project-manager routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    project_manager_service,
    workspace_service,
)
from app.models.request_models import (
    ProjectReportRequest,
    ProjectRiskRequest,
    ProjectRiskUpdateRequest,
)

router = APIRouter()


# NOTE: /evaluation/* routes were extracted into app/api/evaluation_routes.py (services still live here).


@router.get("/project-manager/timeline")
def get_project_timeline(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return project_manager_service.timeline(workspace_id=resolved)


@router.get("/project-manager/resources")
def get_project_resources(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return project_manager_service.resource_allocation(workspace_id=resolved)


@router.get("/project-manager/risks")
def get_project_risks(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return project_manager_service.risk_register(workspace_id=resolved)


@router.post("/project-manager/risks")
def create_project_risk(request: ProjectRiskRequest) -> dict:
    resolved = workspace_service.resolve_workspace_id(request.workspace_id) if request.workspace_id else None
    return project_manager_service.create_risk(
        title=request.title,
        description=request.description,
        severity=request.severity,
        mitigation=request.mitigation,
        goal_id=request.goal_id,
        workspace_id=resolved,
    )


@router.patch("/project-manager/risks/{risk_id}")
def update_project_risk(risk_id: str, request: ProjectRiskUpdateRequest) -> dict:
    try:
        return project_manager_service.update_risk(
            risk_id, request.model_dump(exclude_none=True)
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/project-manager/reports")
def get_project_reports(workspace_id: str | None = Query(default=None)) -> list[dict]:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return project_manager_service.list_status_reports(workspace_id=resolved)


@router.post("/project-manager/reports")
def generate_project_report(request: ProjectReportRequest) -> dict:
    resolved = workspace_service.resolve_workspace_id(request.workspace_id) if request.workspace_id else None
    return project_manager_service.generate_status_report(workspace_id=resolved)


@router.get("/project-manager/dashboard")
def get_project_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return project_manager_service.dashboard(workspace_id=resolved)
