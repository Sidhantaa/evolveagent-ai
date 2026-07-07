"""hardware-companion routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    hardware_companion_service,
)
from app.models.request_models import (
    CompanionReadinessCheckRequest,
    CompanionSessionCreateRequest,
    CompanionSettingsUpdateRequest,
    HardwareDeviceCreateRequest,
    HardwareDeviceUpdateRequest,
)

router = APIRouter()


# NOTE: /organization-os/* routes were extracted into app/api/organization_os_routes.py (services still live here).


# ----------------------------------------------------------------------
# v39.0 AI Hardware / Always-On Companion (readiness/planning only)
# ----------------------------------------------------------------------
@router.get("/hardware-companion/dashboard")
def get_hardware_companion_dashboard() -> dict:
    return hardware_companion_service.dashboard()


@router.get("/hardware-companion/audit")
def get_hardware_companion_audit() -> dict:
    audit = hardware_companion_service.audit_log()
    return {"audit": audit, "count": len(audit)}


@router.get("/hardware-companion/devices")
def list_hardware_companion_devices() -> dict:
    devices = hardware_companion_service.list_devices()
    return {"devices": devices, "count": len(devices)}


@router.post("/hardware-companion/devices")
def create_hardware_companion_device(request: HardwareDeviceCreateRequest) -> dict:
    return hardware_companion_service.create_device(request.model_dump())


@router.patch("/hardware-companion/devices/{device_id}")
def update_hardware_companion_device(device_id: str, request: HardwareDeviceUpdateRequest) -> dict:
    try:
        return hardware_companion_service.update_device(device_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Device not found") from error


@router.get("/hardware-companion/settings")
def get_hardware_companion_settings() -> dict:
    return hardware_companion_service.get_settings()


@router.patch("/hardware-companion/settings")
def update_hardware_companion_settings(request: CompanionSettingsUpdateRequest) -> dict:
    return hardware_companion_service.update_settings(request.model_dump(exclude_unset=True))


@router.get("/hardware-companion/readiness-checks")
def list_hardware_companion_readiness_checks() -> dict:
    checks = hardware_companion_service.list_readiness_checks()
    return {"readiness_checks": checks, "count": len(checks)}


@router.post("/hardware-companion/readiness-checks")
def create_hardware_companion_readiness_check(request: CompanionReadinessCheckRequest | None = None) -> dict:
    device_id = request.device_id if request else None
    return hardware_companion_service.create_readiness_check(device_id)


@router.get("/hardware-companion/sessions")
def list_hardware_companion_sessions() -> dict:
    sessions = hardware_companion_service.list_sessions()
    return {"sessions": sessions, "count": len(sessions)}


@router.post("/hardware-companion/sessions")
def create_hardware_companion_session(request: CompanionSessionCreateRequest) -> dict:
    return hardware_companion_service.create_session(request.model_dump())
