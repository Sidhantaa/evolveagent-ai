"""evaluation routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    evaluation_lab_service,
    workspace_service,
    PlainTextResponse,
)
from app.models.request_models import (
    EvaluationABTestRequest,
    EvaluationRunRequest,
)

router = APIRouter()


@router.get("/evaluation/benchmarks")
def get_evaluation_benchmarks(task_type: str | None = Query(default=None)) -> dict:
    benchmarks = evaluation_lab_service.list_benchmarks(task_type=task_type)
    return {"benchmarks": benchmarks, "count": len(benchmarks)}


@router.post("/evaluation/runs")
def create_evaluation_run(request: EvaluationRunRequest) -> dict:
    resolved = workspace_service.resolve_workspace_id(request.workspace_id) if request.workspace_id else None
    try:
        return evaluation_lab_service.create_run(
            benchmark_id=request.benchmark_id,
            task_type=request.task_type,
            workspace_id=resolved,
            notes=request.notes,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/evaluation/runs")
def get_evaluation_runs(
    workspace_id: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    runs = evaluation_lab_service.list_runs(workspace_id=resolved, limit=limit)
    return {"workspace_id": resolved, "runs": runs, "count": len(runs)}


@router.get("/evaluation/dashboard")
def get_evaluation_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return evaluation_lab_service.dashboard(workspace_id=resolved)


@router.post("/evaluation/ab-tests")
def create_evaluation_ab_test(request: EvaluationABTestRequest) -> dict:
    resolved = workspace_service.resolve_workspace_id(request.workspace_id) if request.workspace_id else None
    return evaluation_lab_service.create_ab_test(
        name=request.name,
        variant_a=request.variant_a,
        variant_b=request.variant_b,
        metric=request.metric,
        workspace_id=resolved,
    )


@router.get("/evaluation/ab-tests")
def get_evaluation_ab_tests(
    workspace_id: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    records = evaluation_lab_service.list_ab_tests(workspace_id=resolved, limit=limit)
    return {"workspace_id": resolved, "ab_tests": records, "count": len(records)}


@router.get("/evaluation/regressions")
def get_evaluation_regressions(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return evaluation_lab_service.regressions(workspace_id=resolved)


@router.get("/evaluation/export")
def export_evaluation_results(
    workspace_id: str | None = Query(default=None),
    format: str = Query(default="json", pattern="^(json|csv)$"),
) -> PlainTextResponse:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    content = evaluation_lab_service.export(workspace_id=resolved, format=format)
    media_type = "application/json" if format == "json" else "text/csv"
    extension = "json" if format == "json" else "csv"
    return PlainTextResponse(
        content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="evolveagent-evaluation.{extension}"'},
    )
