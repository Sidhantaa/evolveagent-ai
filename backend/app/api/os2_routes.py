"""os2 routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    evolveagent_os2_service,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v60.0 EvolveAgent OS 2.0 — unified command center + final report (capstone).
# ----------------------------------------------------------------------
@router.get("/os2/dashboard")
def get_os2_dashboard() -> dict:
    return evolveagent_os2_service.dashboard()


@router.get("/os2/command-center")
def get_os2_command_center() -> dict:
    return evolveagent_os2_service.command_center()


@router.get("/os2/snapshots")
def list_os2_snapshots() -> dict:
    snapshots = evolveagent_os2_service.list_snapshots()
    return {"snapshots": snapshots, "count": len(snapshots)}


@router.post("/os2/snapshots")
def create_os2_snapshot() -> dict:
    return evolveagent_os2_service.create_snapshot()


@router.post("/os2/report")
def create_os2_report() -> dict:
    return evolveagent_os2_service.create_report()
