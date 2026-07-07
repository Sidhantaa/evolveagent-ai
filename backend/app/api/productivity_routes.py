"""productivity routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, Query
from app.api.routes import (
    personal_productivity_service,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v74.0 Personal Productivity Brain — what should I work on now? (read-only).
# ----------------------------------------------------------------------
@router.get("/productivity")
def productivity_brain(workspace_id: str | None = Query(default=None)) -> dict:
    return personal_productivity_service.brain(workspace_id=workspace_id)


@router.get("/productivity/what-now")
def productivity_what_now(workspace_id: str | None = Query(default=None)) -> dict:
    return personal_productivity_service.what_now(workspace_id=workspace_id)


@router.get("/productivity/summary")
def productivity_summary() -> dict:
    return personal_productivity_service.summary()


# NOTE: /code-intel/* routes were extracted into app/api/code_intel_routes.py (services still live here).
