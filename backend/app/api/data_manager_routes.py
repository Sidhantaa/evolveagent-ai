"""data-manager routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    data_manager_service,
    storage,
)
from app.models.request_models import (
    RedactionPreviewRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v83.0 Local Data Manager — read-only/planning-first storage management.
# ----------------------------------------------------------------------
@router.get("/data-manager/browse")
def data_manager_browse() -> dict:
    return data_manager_service.browse()


@router.get("/data-manager/usage")
def data_manager_usage() -> dict:
    return data_manager_service.usage()


@router.get("/data-manager/cleanup-suggestions")
def data_manager_cleanup() -> dict:
    return data_manager_service.cleanup_suggestions()


@router.post("/data-manager/redaction-preview")
def data_manager_redaction_preview(request: RedactionPreviewRequest) -> dict:
    try:
        return data_manager_service.redaction_preview(request.collection)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/data-manager/summary")
def data_manager_summary() -> dict:
    return data_manager_service.summary()
