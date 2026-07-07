"""approvals-center routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from app.api.routes import (
    unified_approvals_service,
)
from app.models.request_models import (
    ApprovalDecisionRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v48.0 Unified Approvals Center — one queue across all approval sources.
# (Distinct /approvals-center prefix to avoid the pre-existing /approvals workflow.)
# ----------------------------------------------------------------------
@router.get("/approvals-center/summary")
def get_approvals_center_summary() -> dict:
    return unified_approvals_service.summary()


@router.get("/approvals-center")
def list_approvals_center(source: str | None = Query(default=None)) -> dict:
    items = unified_approvals_service.list_pending(source)
    return {"items": items, "count": len(items)}


@router.post("/approvals-center/approve")
def approve_approvals_center(request: ApprovalDecisionRequest) -> dict:
    try:
        return unified_approvals_service.approve(request.source, request.item_id)
    except ValueError as error:
        detail = str(error)
        status = 404 if "not found" in detail.lower() else 409
        raise HTTPException(status_code=status, detail=detail) from error


@router.post("/approvals-center/reject")
def reject_approvals_center(request: ApprovalDecisionRequest) -> dict:
    try:
        return unified_approvals_service.reject(request.source, request.item_id)
    except ValueError as error:
        detail = str(error)
        status = 404 if "not found" in detail.lower() else 409
        raise HTTPException(status_code=status, detail=detail) from error
