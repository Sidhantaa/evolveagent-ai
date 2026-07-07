"""company-brain routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    company_brain_service,
)
from app.models.request_models import (
    CompanyDecisionRequest,
    CompanyReportRequest,
    CompanyStrategyRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v25.0 AI Company Brain
# ----------------------------------------------------------------------
@router.get("/company-brain/dashboard")
def get_company_brain_dashboard() -> dict:
    return company_brain_service.dashboard()


@router.post("/company-brain/strategy")
def create_company_brain_strategy(request: CompanyStrategyRequest) -> dict:
    return company_brain_service.create_strategy(request.model_dump())


@router.get("/company-brain/strategy")
def list_company_brain_strategy() -> dict:
    strategy = company_brain_service.list_strategy()
    return {"strategy": strategy, "count": len(strategy)}


@router.post("/company-brain/decisions")
def create_company_brain_decision(request: CompanyDecisionRequest) -> dict:
    return company_brain_service.create_decision(request.model_dump())


@router.get("/company-brain/decisions")
def list_company_brain_decisions() -> dict:
    decisions = company_brain_service.list_decisions()
    return {"decisions": decisions, "count": len(decisions)}


@router.post("/company-brain/reports")
def create_company_brain_report(request: CompanyReportRequest | None = None) -> dict:
    return company_brain_service.create_report()


@router.get("/company-brain/reports")
def list_company_brain_reports() -> dict:
    reports = company_brain_service.list_reports()
    return {"reports": reports, "count": len(reports)}
