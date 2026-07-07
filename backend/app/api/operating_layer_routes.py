"""operating-layer routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    operating_layer_service,
)

router = APIRouter()


# NOTE: /hardware-companion/* routes were extracted into app/api/hardware_companion_routes.py (services still live here).


# ----------------------------------------------------------------------
# v40.0 EvolveAgent AGI-Style Operating Layer (governed orchestration — NOT AGI)
# ----------------------------------------------------------------------
@router.get("/operating-layer/dashboard")
def get_operating_layer_dashboard() -> dict:
    return operating_layer_service.dashboard()


@router.get("/operating-layer/capabilities")
def get_operating_layer_capabilities() -> dict:
    return operating_layer_service.capabilities()


@router.post("/operating-layer/snapshots")
def create_operating_layer_snapshot() -> dict:
    return operating_layer_service.create_snapshot()


@router.get("/operating-layer/snapshots")
def list_operating_layer_snapshots() -> dict:
    snapshots = operating_layer_service.list_snapshots()
    return {"snapshots": snapshots, "count": len(snapshots)}


@router.post("/operating-layer/recommendations")
def create_operating_layer_recommendations() -> dict:
    return operating_layer_service.create_recommendations()


@router.get("/operating-layer/recommendations")
def list_operating_layer_recommendations() -> dict:
    recommendations = operating_layer_service.list_recommendations()
    return {"recommendations": recommendations, "count": len(recommendations)}


@router.post("/operating-layer/report")
def create_operating_layer_report() -> dict:
    return operating_layer_service.create_report()


@router.get("/operating-layer/audit")
def get_operating_layer_audit() -> dict:
    audit = operating_layer_service.audit_log()
    return {"audit": audit, "count": len(audit)}
