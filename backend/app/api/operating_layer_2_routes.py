"""operating-layer-2 routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    operating_layer_v2_service,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v55.0 EvolveAgent Operating Layer 2.0 — expanded capability map + scorecard.
# ----------------------------------------------------------------------
@router.get("/operating-layer-2/dashboard")
def get_operating_layer_v2_dashboard() -> dict:
    return operating_layer_v2_service.dashboard()


@router.get("/operating-layer-2/capabilities")
def get_operating_layer_v2_capabilities() -> dict:
    return operating_layer_v2_service.capabilities()


@router.get("/operating-layer-2/scorecard")
def get_operating_layer_v2_scorecard() -> dict:
    return operating_layer_v2_service.scorecard()


@router.get("/operating-layer-2/snapshots")
def list_operating_layer_v2_snapshots() -> dict:
    snapshots = operating_layer_v2_service.list_snapshots()
    return {"snapshots": snapshots, "count": len(snapshots)}


@router.post("/operating-layer-2/snapshots")
def create_operating_layer_v2_snapshot() -> dict:
    return operating_layer_v2_service.create_snapshot()


@router.post("/operating-layer-2/report")
def create_operating_layer_v2_report() -> dict:
    return operating_layer_v2_service.create_report()
