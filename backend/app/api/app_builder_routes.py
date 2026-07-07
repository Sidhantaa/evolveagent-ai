"""app-builder routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    app_builder_service,
)
from app.models.request_models import (
    AppBuilderPlanRequest,
    AppBuilderScaffoldRequest,
    AppBuilderWizardRequest,
)

router = APIRouter()


# NOTE: /quality/* routes were extracted into app/api/quality_routes.py (services still live here).


@router.get("/app-builder/templates")
def list_app_builder_templates() -> list[dict]:
    return app_builder_service.list_templates()


@router.get("/app-builder/plans")
def list_app_builder_plans(workspace_id: str | None = Query(default=None)) -> list[dict]:
    return app_builder_service.list_plans(workspace_id)


@router.get("/app-builder/plans/{plan_id}")
def get_app_builder_plan(plan_id: str) -> dict:
    plan = app_builder_service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="App builder plan not found")
    return plan


@router.post("/app-builder/plan")
def create_app_builder_plan(request: AppBuilderPlanRequest) -> dict:
    return app_builder_service.create_plan(
        prompt=request.prompt,
        stack_id=request.stack_id,
        workspace_id=request.workspace_id,
    )


@router.post("/app-builder/wizard")
def update_app_builder_wizard(request: AppBuilderWizardRequest) -> dict:
    return app_builder_service.update_wizard(request.model_dump())


@router.post("/app-builder/scaffold")
def scaffold_app_builder_plan(request: AppBuilderScaffoldRequest) -> dict:
    return app_builder_service.scaffold(plan_id=request.plan_id, approved=request.approved)
