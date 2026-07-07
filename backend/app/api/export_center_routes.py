"""export-center routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    export_center_service,
)
from app.models.request_models import (
    ExportPackageRequest,
    ExportRequest,
)

router = APIRouter()


# NOTE: /import-center/* routes were extracted into app/api/import_center_routes.py (services still live here).


# ----------------------------------------------------------------------
# v85.0 Export Center — read-only portable exports (markdown/JSON).
# ----------------------------------------------------------------------
@router.post("/export-center/export")
def export_center_export(request: ExportRequest) -> dict:
    try:
        return export_center_service.export(request.kind, request.format, request.workspace_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/export-center/package")
def export_center_package(request: ExportPackageRequest) -> dict:
    return export_center_service.package(request.kinds, request.format, request.workspace_id)


@router.get("/export-center/case-study")
def export_center_case_study() -> dict:
    return export_center_service.case_study()


@router.get("/export-center/summary")
def export_center_summary() -> dict:
    return export_center_service.summary()


# NOTE: /plugin-marketplace/* routes were extracted into app/api/plugin_marketplace_routes.py (services still live here).
