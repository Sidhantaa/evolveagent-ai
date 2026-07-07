"""import-center routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    import_center_service,
)
from app.models.request_models import (
    ImportCommitRequest,
    ImportPreviewRequest,
)

router = APIRouter()


# NOTE: /data-manager/* routes were extracted into app/api/data_manager_routes.py (services still live here).


# ----------------------------------------------------------------------
# v84.0 Import Center — validate + sanitize + preview before saving.
# ----------------------------------------------------------------------
@router.post("/import-center/preview")
def import_center_preview(request: ImportPreviewRequest) -> dict:
    try:
        return import_center_service.preview(request.kind, request.content)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/import-center/commit")
def import_center_commit(request: ImportCommitRequest) -> dict:
    try:
        return import_center_service.commit(request.kind, request.content, request.workspace_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/import-center/records")
def import_center_records(kind: str | None = Query(default=None)) -> dict:
    return import_center_service.list_records(kind=kind)


@router.get("/import-center/summary")
def import_center_summary() -> dict:
    return import_center_service.summary()
