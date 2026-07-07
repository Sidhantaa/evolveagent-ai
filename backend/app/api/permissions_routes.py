"""permissions routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    permission_profiles_service,
)
from app.models.request_models import (
    PermissionEvaluateRequest,
    PermissionProfileRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v81.0 Permission System 3.0 — profiles + previewable evaluation (advisory layer).
# ----------------------------------------------------------------------
@router.get("/permissions/profiles")
def list_permission_profiles() -> dict:
    profiles = permission_profiles_service.list_profiles()
    return {"profiles": profiles, "count": len(profiles)}


@router.post("/permissions/profiles")
def create_permission_profile(request: PermissionProfileRequest) -> dict:
    return permission_profiles_service.create_profile(request.model_dump())


@router.delete("/permissions/profiles/{profile_id}")
def delete_permission_profile(profile_id: str) -> dict:
    try:
        return permission_profiles_service.delete_profile(profile_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/permissions/evaluate")
def evaluate_permission(request: PermissionEvaluateRequest) -> dict:
    return permission_profiles_service.evaluate(request.scope_type, request.scope_value, request.action, request.risk_level)


@router.post("/permissions/preview")
def preview_permission(request: PermissionEvaluateRequest) -> dict:
    return permission_profiles_service.preview(request.scope_type, request.scope_value, request.action, request.risk_level)


@router.get("/permissions/summary")
def permissions_summary() -> dict:
    return permission_profiles_service.summary()
