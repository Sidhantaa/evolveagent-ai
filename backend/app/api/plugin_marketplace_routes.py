"""plugin-marketplace routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    plugin_marketplace_service,
)
from app.models.request_models import (
    PluginRegisterRequest,
    PluginToggleRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v86.0 Plugin Marketplace 3.0 — safer plugin catalog (additive; mock test runner).
# ----------------------------------------------------------------------
@router.get("/plugin-marketplace/catalog")
def plugin_marketplace_catalog() -> dict:
    return plugin_marketplace_service.catalog()


@router.post("/plugin-marketplace/register")
def plugin_marketplace_register(request: PluginRegisterRequest) -> dict:
    return plugin_marketplace_service.register(request.name, request.description, request.permissions)


@router.post("/plugin-marketplace/{plugin_id}/toggle")
def plugin_marketplace_toggle(plugin_id: str, request: PluginToggleRequest) -> dict:
    try:
        return plugin_marketplace_service.toggle(plugin_id, request.enabled)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/plugin-marketplace/{plugin_id}/test")
def plugin_marketplace_test(plugin_id: str) -> dict:
    try:
        return plugin_marketplace_service.test_run(plugin_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/plugin-marketplace/activity")
def plugin_marketplace_activity() -> dict:
    return plugin_marketplace_service.activity_log()


@router.get("/plugin-marketplace/summary")
def plugin_marketplace_summary() -> dict:
    return plugin_marketplace_service.summary()
