"""meeting-intel routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    meeting_intelligence_service,
)
from app.models.request_models import (
    MeetingAnalyzeRequest,
    MeetingToGoalRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v79.0 Meeting Intelligence 2.0 — deterministic transcript extraction (read-only).
# ----------------------------------------------------------------------
@router.post("/meeting-intel/analyze")
def meeting_intel_analyze(request: MeetingAnalyzeRequest) -> dict:
    return meeting_intelligence_service.analyze(request.transcript)


@router.post("/meeting-intel/to-goal")
def meeting_intel_to_goal(request: MeetingToGoalRequest) -> dict:
    return meeting_intelligence_service.to_goal_plan(request.transcript, request.title)


@router.get("/meeting-intel/summary")
def meeting_intel_summary() -> dict:
    return meeting_intelligence_service.summary()
