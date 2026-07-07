"""notifications-inbox routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    notifications_inbox_service,
)

router = APIRouter()


# NOTE: /provider-control/* routes were extracted into app/api/provider_control_routes.py (services still live here).


# ----------------------------------------------------------------------
# v69.0 Unified Notifications Inbox 2.0 — actionable alerts (additive to v56).
# ----------------------------------------------------------------------
@router.post("/notifications-inbox/generate")
def notifications_inbox_generate() -> dict:
    return notifications_inbox_service.generate()


@router.get("/notifications-inbox")
def notifications_inbox_list(
    severity: str | None = Query(default=None),
    include_resolved: bool = Query(default=False),
) -> dict:
    return notifications_inbox_service.list_items(severity=severity, include_resolved=include_resolved)


@router.get("/notifications-inbox/summary")
def notifications_inbox_summary() -> dict:
    return notifications_inbox_service.summary()


@router.post("/notifications-inbox/{item_id}/resolve")
def notifications_inbox_resolve(item_id: str) -> dict:
    try:
        return notifications_inbox_service.resolve(item_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
