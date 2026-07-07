"""departments routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    agent_department_service,
)
from app.models.request_models import (
    DepartmentCollaborationRequest,
    DepartmentCreateRequest,
    DepartmentRunRequest,
    DepartmentUpdateRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v16.0 Multi-Agent Organization (departments / managers / workers / reviewers / auditors)
# ----------------------------------------------------------------------
@router.get("/departments")
def list_departments(include_archived: bool = Query(default=False)) -> dict:
    departments = agent_department_service.list_departments(include_archived=include_archived)
    return {"departments": departments, "count": len(departments), **agent_department_service.analytics_summary()}


@router.post("/departments")
def create_department(request: DepartmentCreateRequest) -> dict:
    return agent_department_service.create_department(
        name=request.name,
        description=request.description,
        manager_agent=request.manager_agent,
        worker_agents=request.worker_agents,
        reviewer_agents=request.reviewer_agents,
        auditor_agents=request.auditor_agents,
        allowed_tools=request.allowed_tools,
        permission_level=request.permission_level,
    )


@router.get("/departments/templates")
def get_department_templates() -> dict:
    templates = agent_department_service.templates()
    return {"templates": templates, "count": len(templates)}


@router.post("/departments/templates/seed")
def seed_department_templates() -> dict:
    return agent_department_service.seed_templates()


@router.get("/departments/runs")
def list_department_runs() -> dict:
    runs = agent_department_service.list_runs()
    return {"runs": runs, "count": len(runs)}


@router.get("/departments/collaborations")
def list_department_collaborations() -> dict:
    collaborations = agent_department_service.list_collaborations()
    return {"collaborations": collaborations, "count": len(collaborations)}


@router.post("/departments/collaborations")
def create_department_collaboration(request: DepartmentCollaborationRequest) -> dict:
    return agent_department_service.plan_collaboration(
        goal=request.goal,
        departments=request.departments,
        lead_department=request.lead_department,
    )


@router.get("/departments/{department_id}")
def get_department(department_id: str) -> dict:
    department = agent_department_service.get_department(department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


@router.patch("/departments/{department_id}")
def update_department(department_id: str, request: DepartmentUpdateRequest) -> dict:
    try:
        return agent_department_service.update_department(department_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/departments/{department_id}")
def archive_department(department_id: str) -> dict:
    try:
        return agent_department_service.archive_department(department_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/departments/{department_id}/runs")
def create_department_run(department_id: str, request: DepartmentRunRequest) -> dict:
    try:
        return agent_department_service.plan_run(department_id, request.task)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
