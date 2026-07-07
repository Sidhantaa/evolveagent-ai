"""research routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    research_search_service,
    research_session_service,
)
from app.models.request_models import (
    ResearchCitationCreateRequest,
    ResearchSearchRequest,
    ResearchSessionCreateRequest,
    ResearchSourceCreateRequest,
)

router = APIRouter()


@router.get("/research/sessions")
def list_research_sessions(workspace_id: str | None = Query(default=None)) -> list[dict]:
    return research_session_service.list_sessions(workspace_id)


@router.post("/research/sessions")
def create_research_session(request: ResearchSessionCreateRequest) -> dict:
    return research_session_service.create_session(
        query=request.query,
        workspace_id=request.workspace_id,
        require_approval=request.require_approval,
        notes=request.notes,
    )


@router.get("/research/sessions/{research_id}")
def get_research_session(research_id: str) -> dict:
    session = research_session_service.get_session(research_id)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")
    return session


@router.post("/research/sessions/{research_id}/approve")
def approve_research_session(research_id: str) -> dict:
    session = research_session_service.approve_session(research_id, approved=True)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")
    return session


@router.post("/research/sessions/{research_id}/reject")
def reject_research_session(research_id: str) -> dict:
    session = research_session_service.approve_session(research_id, approved=False)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")
    return session


@router.post("/research/sessions/{research_id}/sources")
def add_research_source(research_id: str, request: ResearchSourceCreateRequest) -> dict:
    source = research_session_service.add_source(research_id, request.model_dump())
    if not source:
        raise HTTPException(status_code=404, detail="Research session not found")
    return source


@router.get("/research/sessions/{research_id}/sources")
def list_research_sources(research_id: str) -> list[dict]:
    if not research_session_service.get_session(research_id):
        raise HTTPException(status_code=404, detail="Research session not found")
    return research_session_service.list_sources(research_id)


@router.post("/research/sessions/{research_id}/citations")
def add_research_citation(research_id: str, request: ResearchCitationCreateRequest) -> dict:
    citation = research_session_service.add_citation(research_id, request.model_dump())
    if not citation:
        raise HTTPException(status_code=404, detail="Research session or source not found")
    return citation


@router.get("/research/sessions/{research_id}/citations")
def list_research_citations(research_id: str) -> list[dict]:
    if not research_session_service.get_session(research_id):
        raise HTTPException(status_code=404, detail="Research session not found")
    return research_session_service.list_citations(research_id)


@router.get("/research/sessions/{research_id}/report")
def get_research_report(research_id: str) -> dict:
    report = research_session_service.generate_report(research_id)
    if not report:
        raise HTTPException(status_code=404, detail="Research session not found")
    return report


@router.post("/research/search")
def run_controlled_search(request: ResearchSearchRequest) -> dict:
    return research_search_service.search(
        query=request.query,
        workspace_id=request.workspace_id,
        max_results=request.max_results,
    )


@router.post("/research/sessions/{research_id}/search")
def run_session_controlled_search(research_id: str, request: ResearchSearchRequest) -> dict:
    session = research_session_service.get_session(research_id)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    search_res = research_search_service.search(
        query=request.query,
        workspace_id=request.workspace_id,
        max_results=request.max_results,
    )

    added_sources = []
    for item in search_res["results"]:
        payload = {
            "title": item["title"],
            "url": item["url"],
            "publisher": item["publisher"],
            "snippet": item["snippet"],
            "fetched": True,
        }
        source = research_session_service.add_source(research_id, payload)
        if source:
            added_sources.append(source)

    research_search_service.log_sources_added(
        research_id=research_id,
        query=request.query,
        workspace_id=session.get("workspace_id"),
        num_sources=len(search_res["results"]),
    )

    updated_session = research_session_service.get_session(research_id)
    if not updated_session:
        raise HTTPException(status_code=404, detail="Research session not found")
    return {
        **updated_session,
        "search_result": search_res,
        "sources_added": added_sources,
    }
