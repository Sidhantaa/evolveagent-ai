"""data-export routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    data_export_service,
)
from app.models.request_models import (
    DataImportRequest,
)

router = APIRouter()


# NOTE: /workspace-templates/* routes were extracted into app/api/workspace_templates_routes.py (services still live here).


# ----------------------------------------------------------------------
# v59.0 Data Export & Backup — local bundle export/import (non-destructive).
# ----------------------------------------------------------------------
@router.get("/data-export/summary")
def get_data_export_summary() -> dict:
    return data_export_service.summary()


@router.post("/data-export/bundle")
def export_data_bundle() -> dict:
    return data_export_service.export_bundle()


@router.post("/data-export/import")
def import_data_bundle(request: DataImportRequest) -> dict:
    try:
        return data_export_service.import_bundle(request.bundle)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


# NOTE: /master-agent/* routes were extracted into app/api/master_agent_routes.py (services still live here).
