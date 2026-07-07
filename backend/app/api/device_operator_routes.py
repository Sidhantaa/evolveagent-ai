"""device-operator routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    device_operator_service,
)
from app.models.request_models import (
    DeviceConfirmActionRequest,
    DevicePlanRequest,
    DeviceSessionCreateRequest,
)

router = APIRouter()


# NOTE: /company-brain/* routes were extracted into app/api/company_brain_routes.py (services still live here).


# ----------------------------------------------------------------------
# v26.0 Personal Device Operator / Phone Autopilot (mock, planning-first)
# ----------------------------------------------------------------------
@router.get("/device-operator/dashboard")
def get_device_operator_dashboard() -> dict:
    return device_operator_service.dashboard()


@router.get("/device-operator/audit")
def get_device_operator_audit() -> dict:
    audit = device_operator_service.audit_log()
    return {"audit": audit, "count": len(audit)}


@router.get("/device-operator/sessions")
def list_device_operator_sessions() -> dict:
    sessions = device_operator_service.list_sessions()
    return {"sessions": sessions, "count": len(sessions)}


@router.post("/device-operator/sessions")
def create_device_operator_session(request: DeviceSessionCreateRequest) -> dict:
    return device_operator_service.create_session(request.model_dump())


@router.get("/device-operator/sessions/{session_id}")
def get_device_operator_session(session_id: str) -> dict:
    session = device_operator_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/device-operator/sessions/{session_id}/plan")
def plan_device_operator_session(session_id: str, request: DevicePlanRequest) -> dict:
    try:
        return device_operator_service.plan(session_id, request.command, request.screen_text)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Session not found") from error


@router.post("/device-operator/sessions/{session_id}/confirm-action")
def confirm_device_operator_action(session_id: str, request: DeviceConfirmActionRequest) -> dict:
    try:
        return device_operator_service.confirm_action(session_id, request.action_id, request.approve)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Action not found") from error


# NOTE: /saas-builder/* routes were extracted into app/api/saas_builder_routes.py (services still live here).
