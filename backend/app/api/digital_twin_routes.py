"""digital-twin routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, Query
from app.api.routes import (
    digital_twin_service,
)
from app.models.request_models import (
    DigitalTwinUpdateRequest,
)

router = APIRouter()


@router.get("/digital-twin/profile")
def get_digital_twin_profile(workspace_id: str | None = Query(default=None)) -> dict:
    return digital_twin_service.get_profile(workspace_id)


@router.post("/digital-twin/profile/refresh")
def refresh_digital_twin_profile(workspace_id: str | None = Query(default=None)) -> dict:
    return digital_twin_service.refresh_profile(workspace_id)


@router.patch("/digital-twin/profile")
def update_digital_twin_profile(request: DigitalTwinUpdateRequest) -> dict:
    return digital_twin_service.update_profile(
        workspace_id=request.workspace_id,
        updates=request.model_dump(exclude={"workspace_id"}, exclude_none=True),
    )


@router.get("/digital-twin/profile/export")
def export_digital_twin_profile(workspace_id: str | None = Query(default=None)) -> dict:
    return digital_twin_service.export_profile(workspace_id)


@router.post("/digital-twin/profile/reset")
def reset_digital_twin_profile(workspace_id: str | None = Query(default=None)) -> dict:
    return digital_twin_service.reset_profile(workspace_id)


@router.delete("/digital-twin/profile")
def delete_digital_twin_profile(workspace_id: str | None = Query(default=None)) -> dict:
    return digital_twin_service.delete_profile(workspace_id)
