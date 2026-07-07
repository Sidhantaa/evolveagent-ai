"""launch-console routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    product_launch_service,
)

router = APIRouter()


# NOTE: /qa-center/* routes were extracted into app/api/qa_center_routes.py (services still live here).


# ----------------------------------------------------------------------
# v90.0 EvolveAgent Product Launch Console (capstone) — launch-readiness overview.
# ----------------------------------------------------------------------
@router.get("/launch-console/dashboard")
def launch_console_dashboard() -> dict:
    return product_launch_service.dashboard()


@router.get("/launch-console/report")
def launch_console_report() -> dict:
    return product_launch_service.launch_report()


@router.get("/launch-console/summary")
def launch_console_summary() -> dict:
    return product_launch_service.summary()
