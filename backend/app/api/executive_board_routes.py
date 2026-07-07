"""executive-board routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    executive_board_service,
)
from app.models.request_models import (
    ExecutiveBoardSessionCreateRequest,
    ExecutiveBoardVoteRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v35.0 AI Executive Board (advisory only — does not execute actions)
# ----------------------------------------------------------------------
@router.get("/executive-board/dashboard")
def get_executive_board_dashboard() -> dict:
    return executive_board_service.dashboard()


@router.get("/executive-board/sessions")
def list_executive_board_sessions() -> dict:
    sessions = executive_board_service.list_sessions()
    return {"sessions": sessions, "count": len(sessions)}


@router.post("/executive-board/sessions")
def create_executive_board_session(request: ExecutiveBoardSessionCreateRequest) -> dict:
    return executive_board_service.create_session(request.model_dump())


@router.get("/executive-board/reports")
def list_executive_board_reports() -> dict:
    reports = executive_board_service.list_reports()
    return {"reports": reports, "count": len(reports)}


@router.get("/executive-board/recommendations")
def list_executive_board_recommendations() -> dict:
    recommendations = executive_board_service.list_recommendations()
    return {"recommendations": recommendations, "count": len(recommendations)}


@router.get("/executive-board/sessions/{session_id}")
def get_executive_board_session(session_id: str) -> dict:
    session = executive_board_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/executive-board/sessions/{session_id}/review")
def review_executive_board_session(session_id: str) -> dict:
    try:
        return executive_board_service.review(session_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Session not found") from error


@router.post("/executive-board/sessions/{session_id}/vote")
def vote_executive_board_session(session_id: str, request: ExecutiveBoardVoteRequest) -> dict:
    try:
        return executive_board_service.vote(session_id, request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Session not found") from error


@router.post("/executive-board/sessions/{session_id}/report")
def report_executive_board_session(session_id: str) -> dict:
    try:
        return executive_board_service.create_report(session_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Session not found") from error
