"""eval-harness routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    eval_harness_service,
)
from app.models.request_models import (
    EvalSuiteCreateRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v52.0 Evaluation Harness 2.0 — repeatable suites + scorecards + regression.
# ----------------------------------------------------------------------
@router.get("/eval-harness/summary")
def get_eval_harness_summary() -> dict:
    return eval_harness_service.summary()


@router.get("/eval-harness/suites")
def list_eval_suites() -> dict:
    suites = eval_harness_service.list_suites()
    return {"suites": suites, "count": len(suites)}


@router.post("/eval-harness/suites")
def create_eval_suite(request: EvalSuiteCreateRequest) -> dict:
    return eval_harness_service.create_suite(request.model_dump())


@router.post("/eval-harness/suites/{suite_id}/run")
def run_eval_suite(suite_id: str) -> dict:
    try:
        return eval_harness_service.run_suite(suite_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Suite not found") from error


@router.get("/eval-harness/runs")
def list_eval_runs(suite_id: str | None = Query(default=None)) -> dict:
    runs = eval_harness_service.list_runs(suite_id)
    return {"runs": runs, "count": len(runs)}


@router.get("/eval-harness/suites/{suite_id}/regression")
def get_eval_regression(suite_id: str) -> dict:
    return eval_harness_service.regression(suite_id)
