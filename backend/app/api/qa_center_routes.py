"""qa-center routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, status
from app.api.routes import (
    qa_center_service,
)
from app.models.request_models import (
    QARecordRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v88.0 Quality Assurance Center — verification matrix + release readiness.
# ----------------------------------------------------------------------
@router.get("/qa-center/dashboard")
def qa_center_dashboard() -> dict:
    return qa_center_service.dashboard()


@router.get("/qa-center/matrix")
def qa_center_matrix() -> dict:
    return qa_center_service.verification_matrix()


@router.post("/qa-center/record")
def qa_center_record(request: QARecordRequest) -> dict:
    return qa_center_service.record(request.feature_key, request.status, request.note)


@router.get("/qa-center/summary")
def qa_center_summary() -> dict:
    return qa_center_service.summary()


# NOTE: /release-manager/* routes were extracted into app/api/release_manager_routes.py (services still live here).
