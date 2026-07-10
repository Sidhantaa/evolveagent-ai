"""provider-control routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    provider_control_service,
)
from app.models.request_models import (
    ProviderControlUpdateRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v68.0 Real Provider Control Center 2.0 — readiness, model/mode prefs, cost/latency.
# ----------------------------------------------------------------------
@router.get("/provider-control/dashboard")
def provider_control_dashboard() -> dict:
    return provider_control_service.dashboard()


@router.get("/provider-control/summary")
def provider_control_summary() -> dict:
    return provider_control_service.summary()


@router.get("/provider-control/key-check")
def provider_control_key_check() -> dict:
    return provider_control_service.key_check()


@router.get("/provider-control/health")
def provider_control_health() -> dict:
    return provider_control_service.provider_health()


@router.patch("/provider-control")
def provider_control_update(request: ProviderControlUpdateRequest) -> dict:
    return provider_control_service.update(request.model_by_task, request.capability_modes, request.fallback_enabled)
