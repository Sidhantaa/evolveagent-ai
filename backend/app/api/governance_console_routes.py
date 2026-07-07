"""governance-console routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, Query
from app.api.routes import (
    governance_console_service,
)

router = APIRouter()


# NOTE: /permissions/* routes were extracted into app/api/permissions_routes.py (services still live here).


# ----------------------------------------------------------------------
# v82.0 Governance Console 3.0 — read-only console over the governance log.
# ----------------------------------------------------------------------
@router.get("/governance-console/dashboard")
def governance_console_dashboard() -> dict:
    return governance_console_service.dashboard()


@router.get("/governance-console/report")
def governance_console_report(format: str = Query(default="markdown", pattern="^(markdown|json)$")) -> dict:
    return governance_console_service.report(fmt=format)


@router.get("/governance-console/summary")
def governance_console_summary() -> dict:
    return governance_console_service.summary()


# NOTE: /integration-hub/* routes were extracted into app/api/integration_hub_routes.py (services still live here).
