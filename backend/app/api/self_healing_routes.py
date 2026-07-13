"""self-healing routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    self_healing_service,
)
from app.models.request_models import (
    SelfHealingCheckRequest,
    SelfHealingVerifyRequest,
)

router = APIRouter()


# NOTE: /multimodal/* routes were extracted into app/api/multimodal_routes.py (services still live here).


# ----------------------------------------------------------------------
# v24.0 Self-Healing Project System
# ----------------------------------------------------------------------
@router.get("/self-healing/dashboard")
def get_self_healing_dashboard() -> dict:
    return self_healing_service.dashboard()


@router.get("/self-healing/checks")
def list_self_healing_checks() -> dict:
    checks = self_healing_service.list_checks()
    return {"checks": checks, "count": len(checks)}


@router.post("/self-healing/checks")
def create_self_healing_check(request: SelfHealingCheckRequest) -> dict:
    return self_healing_service.create_check(
        command=request.command,
        mode=request.mode,
        mock_stdout=request.mock_stdout,
        mock_stderr=request.mock_stderr,
        mock_exit_code=request.mock_exit_code,
        workspace_id=request.workspace_id,
    )


@router.get("/self-healing/findings")
def list_self_healing_findings() -> dict:
    findings = self_healing_service.list_findings()
    return {"findings": findings, "count": len(findings)}


@router.post("/self-healing/findings/{finding_id}/repair-task")
def create_self_healing_repair_task(finding_id: str) -> dict:
    try:
        return self_healing_service.create_repair_task(finding_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Finding not found") from error


@router.get("/self-healing/repairs")
def list_self_healing_repairs() -> dict:
    repairs = self_healing_service.list_repairs()
    return {"repairs": repairs, "count": len(repairs)}


@router.get("/self-healing/repairs/{repair_id}")
def get_self_healing_repair(repair_id: str) -> dict:
    repair = self_healing_service.get_repair(repair_id)
    if repair is None:
        raise HTTPException(status_code=404, detail="Repair not found")
    return repair


@router.post("/self-healing/repairs/{repair_id}/verify")
def verify_self_healing_repair(repair_id: str, request: SelfHealingVerifyRequest | None = None) -> dict:
    payload = request or SelfHealingVerifyRequest()
    try:
        return self_healing_service.verify_repair(
            repair_id,
            mode=payload.mode,
            mock_stdout=payload.mock_stdout,
            mock_stderr=payload.mock_stderr,
            mock_exit_code=payload.mock_exit_code,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Repair not found") from error


# NOTE: /device-operator/* routes were extracted into app/api/device_operator_routes.py (services still live here).
