"""business-intel routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, Query
from app.api.routes import (
    business_intelligence_service,
)

router = APIRouter()


# NOTE: /productivity/* routes were extracted into app/api/productivity_routes.py (services still live here).


# ----------------------------------------------------------------------
# v78.0 Business Intelligence 2.0 — read-only business analytics (mock forecast).
# ----------------------------------------------------------------------
@router.get("/business-intel/dashboard")
def business_intel_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    return business_intelligence_service.dashboard(workspace_id=workspace_id)


@router.get("/business-intel/report")
def business_intel_report(workspace_id: str | None = Query(default=None)) -> dict:
    return business_intelligence_service.report(workspace_id=workspace_id)


@router.get("/business-intel/summary")
def business_intel_summary() -> dict:
    return business_intelligence_service.summary()


# NOTE: /meeting-intel/* routes were extracted into app/api/meeting_intel_routes.py (services still live here).
