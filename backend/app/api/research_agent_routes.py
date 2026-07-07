"""research-agent routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    research_agent_service,
)
from app.models.request_models import (
    ResearchBriefRequest,
    ResearchSourcesRequest,
    ResearchTextRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v77.0 Research Agent 2.0 — deterministic local research toolkit (read-only).
# ----------------------------------------------------------------------
@router.post("/research-agent/compare")
def research_compare(request: ResearchSourcesRequest) -> dict:
    return research_agent_service.compare_sources(request.sources)


@router.post("/research-agent/claims")
def research_claims(request: ResearchTextRequest) -> dict:
    return research_agent_service.claim_evidence(request.text)


@router.post("/research-agent/contradictions")
def research_contradictions(request: ResearchSourcesRequest) -> dict:
    return research_agent_service.detect_contradictions(request.sources)


@router.post("/research-agent/citation-quality")
def research_citation_quality(request: ResearchSourcesRequest) -> dict:
    return research_agent_service.citation_quality(request.sources)


@router.post("/research-agent/bias")
def research_bias(request: ResearchTextRequest) -> dict:
    return research_agent_service.bias_flags(request.text)


@router.post("/research-agent/brief")
def research_brief(request: ResearchBriefRequest) -> dict:
    return research_agent_service.brief(request.topic, request.sources)


@router.get("/research-agent/summary")
def research_agent_summary() -> dict:
    return research_agent_service.summary()
