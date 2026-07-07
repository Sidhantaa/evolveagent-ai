"""integration-hub routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    integration_hub_service,
)

router = APIRouter()


# NOTE: /export-center/* routes were extracted into app/api/export_center_routes.py (services still live here).


# ----------------------------------------------------------------------
# v87.0 Integration Hub 3.0 — read-only integration cards (no secret display).
# ----------------------------------------------------------------------
@router.get("/integration-hub/cards")
def integration_hub_cards() -> dict:
    return integration_hub_service.cards()


@router.post("/integration-hub/{integration_id}/dry-run")
def integration_hub_dry_run(integration_id: str) -> dict:
    try:
        return integration_hub_service.dry_run(integration_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/integration-hub/summary")
def integration_hub_summary() -> dict:
    return integration_hub_service.summary()


# NOTE: /launch-console/* routes were extracted into app/api/launch_console_routes.py (services still live here).
