"""code-intel routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    code_intelligence_service,
)
from app.models.request_models import (
    CodeAnalyzeRequest,
    CodeTextRequest,
)

router = APIRouter()


# NOTE: /doc-intel/* routes were extracted into app/api/doc_intel_routes.py (services still live here).


# ----------------------------------------------------------------------
# v76.0 Code Intelligence 2.0 — static analysis of submitted code (read-only).
# ----------------------------------------------------------------------
@router.post("/code-intel/analyze")
def code_intel_analyze(request: CodeAnalyzeRequest) -> dict:
    return code_intelligence_service.analyze(request.code, request.language)


@router.post("/code-intel/routes")
def code_intel_routes(request: CodeTextRequest) -> dict:
    return code_intelligence_service.route_map(request.code)


@router.post("/code-intel/dependencies")
def code_intel_dependencies(request: CodeTextRequest) -> dict:
    return code_intelligence_service.dependencies(request.code)


@router.post("/code-intel/test-coverage")
def code_intel_test_coverage(request: CodeTextRequest) -> dict:
    return code_intelligence_service.test_coverage(request.code)


@router.get("/code-intel/summary")
def code_intel_summary() -> dict:
    return code_intelligence_service.summary()


# NOTE: /research-agent/* routes were extracted into app/api/research_agent_routes.py (services still live here).
