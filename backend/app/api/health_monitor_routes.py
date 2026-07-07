"""health-monitor routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    health_monitor_service,
)

router = APIRouter()


# NOTE: /approvals-center/* routes were extracted into app/api/approvals_center_routes.py (services still live here).


# ----------------------------------------------------------------------
# v49.0 Health & Readiness Monitor — read-only scored health dashboard.
# ----------------------------------------------------------------------
@router.get("/health-monitor/dashboard")
def get_health_monitor_dashboard() -> dict:
    return health_monitor_service.dashboard()


@router.get("/health-monitor/snapshots")
def list_health_snapshots() -> dict:
    snapshots = health_monitor_service.list_snapshots()
    return {"snapshots": snapshots, "count": len(snapshots)}


@router.post("/health-monitor/snapshots")
def create_health_snapshot() -> dict:
    return health_monitor_service.create_snapshot()


# NOTE: /retrieval/* routes were extracted into app/api/retrieval_routes.py (services still live here).
