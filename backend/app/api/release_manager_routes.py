"""release-manager routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    release_manager_service,
)
from app.models.request_models import (
    PRSummaryRequest,
    ReleaseNotesRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v89.0 Release Manager — read-only release-prep generators (text only).
# ----------------------------------------------------------------------
@router.get("/release-manager/dashboard")
def release_manager_dashboard() -> dict:
    return release_manager_service.dashboard()


@router.get("/release-manager/changelog")
def release_manager_changelog() -> dict:
    return release_manager_service.changelog()


@router.post("/release-manager/pr-summary")
def release_manager_pr_summary(request: PRSummaryRequest) -> dict:
    return release_manager_service.pr_summary(request.title, request.changes)


@router.post("/release-manager/release-notes")
def release_manager_release_notes(request: ReleaseNotesRequest) -> dict:
    return release_manager_service.release_notes(request.version, request.highlights)


@router.get("/release-manager/summary")
def release_manager_summary() -> dict:
    return release_manager_service.summary()
