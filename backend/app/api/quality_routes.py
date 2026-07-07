"""quality routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from app.api.routes import (
    git_service,
    linear_service,
    test_quality_service,
    LinearServiceError,
    safe_command_runner,
)
from app.models.request_models import (
    QualityLinearSummaryRequest,
    QualityRunRequest,
    TestSuggestionRequest,
)

router = APIRouter()


@router.get("/quality/status")
def get_quality_status() -> dict:
    return test_quality_service.summary()


@router.post("/quality/suggest-tests")
def suggest_quality_tests(request: TestSuggestionRequest) -> dict:
    files = request.changed_files or git_service.list_changed_files()
    return test_quality_service.suggest_tests(files)


@router.post("/quality/run")
def run_quality_checks(request: QualityRunRequest | None = None) -> dict:
    payload = request or QualityRunRequest()
    commands = payload.commands or ["pytest", "npm run build"]
    if any(not safe_command_runner.is_allowed(command) for command in commands):
        raise HTTPException(status_code=400, detail="Quality checks can only run allowlisted commands.")
    return test_quality_service.run_quality_checks(commands=commands, issue_id=payload.issue_id)


@router.get("/quality/flaky-tests")
def get_flaky_tests() -> dict:
    return {"flaky_tests": test_quality_service.detect_flaky_tests()}


@router.get("/quality/gate")
def get_quality_gate() -> dict:
    latest = test_quality_service.latest_run()
    if not latest:
        return {
            "passed": False,
            "blocked": True,
            "reason": "No quality run has been recorded yet.",
            "latest_run": None,
        }
    return {**latest.get("quality_gate", {}), "latest_run": latest}


@router.post("/quality/linear-summary")
def post_quality_linear_summary(request: QualityLinearSummaryRequest) -> dict:
    runs = test_quality_service.list_runs(100)
    run = None
    if request.quality_run_id:
        run = next((item for item in runs if item.get("quality_run_id") == request.quality_run_id), None)
    else:
        run = test_quality_service.latest_run()
    if not run:
        raise HTTPException(status_code=404, detail="Quality run not found")
    try:
        comment = linear_service.add_linear_comment(request.issue_id, run.get("regression_summary", "Quality run completed."))
    except LinearServiceError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"posted": True, "issue_id": request.issue_id, "quality_run_id": run.get("quality_run_id"), "comment": comment}
