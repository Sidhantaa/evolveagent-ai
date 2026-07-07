"""doc-intel routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    document_intelligence_service,
)
from app.models.request_models import (
    AtsScoreRequest,
    DocCompareRequest,
    DocQARequest,
    DocTextRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v75.0 Document Intelligence 2.0 — deterministic local document toolkit.
# ----------------------------------------------------------------------
@router.post("/doc-intel/compare")
def doc_intel_compare(request: DocCompareRequest) -> dict:
    return document_intelligence_service.compare(request.text_a, request.text_b)


@router.post("/doc-intel/ats")
def doc_intel_ats(request: AtsScoreRequest) -> dict:
    return document_intelligence_service.ats_score(request.resume_text, request.job_keywords)


@router.post("/doc-intel/contract-risk")
def doc_intel_contract_risk(request: DocTextRequest) -> dict:
    return document_intelligence_service.contract_risk(request.text)


@router.post("/doc-intel/csv-insight")
def doc_intel_csv_insight(request: DocTextRequest) -> dict:
    return document_intelligence_service.csv_insight(request.text)


@router.post("/doc-intel/qa")
def doc_intel_qa(request: DocQARequest) -> dict:
    return document_intelligence_service.qa(request.text, request.question)


@router.get("/doc-intel/summary")
def doc_intel_summary() -> dict:
    return document_intelligence_service.summary()
