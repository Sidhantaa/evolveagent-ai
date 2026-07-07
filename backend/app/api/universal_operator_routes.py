"""universal-operator routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    universal_operator_service,
)
from app.models.request_models import (
    UniversalActionDecisionRequest,
    UniversalHandoffCreateRequest,
    UniversalSessionCreateRequest,
    UniversalWorkflowCreateRequest,
)

router = APIRouter()


# NOTE: /life-os/* routes were extracted into app/api/life_os_routes.py (services still live here).


# ----------------------------------------------------------------------
# v30.0 Universal App Operator (mock, planning-first; no real app automation)
# ----------------------------------------------------------------------
@router.get("/universal-operator/dashboard")
def get_universal_operator_dashboard() -> dict:
    return universal_operator_service.dashboard()


@router.get("/universal-operator/audit")
def get_universal_operator_audit() -> dict:
    audit = universal_operator_service.audit_log()
    return {"audit": audit, "count": len(audit)}


@router.get("/universal-operator/sessions")
def list_universal_operator_sessions() -> dict:
    sessions = universal_operator_service.list_sessions()
    return {"sessions": sessions, "count": len(sessions)}


@router.post("/universal-operator/sessions")
def create_universal_operator_session(request: UniversalSessionCreateRequest) -> dict:
    return universal_operator_service.create_session(request.model_dump())


@router.get("/universal-operator/workflows")
def list_universal_operator_workflows() -> dict:
    workflows = universal_operator_service.list_workflows()
    return {"workflows": workflows, "count": len(workflows)}


@router.post("/universal-operator/workflows")
def create_universal_operator_workflow(request: UniversalWorkflowCreateRequest) -> dict:
    return universal_operator_service.create_workflow(request.model_dump())


@router.post("/universal-operator/workflows/{workflow_id}/plan")
def plan_universal_operator_workflow(workflow_id: str) -> dict:
    try:
        return universal_operator_service.plan_workflow(workflow_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Workflow not found") from error


@router.post("/universal-operator/actions/{action_id}/decision")
def decide_universal_operator_action(action_id: str, request: UniversalActionDecisionRequest) -> dict:
    try:
        return universal_operator_service.decide_action(action_id, request.decision)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Action not found") from error


@router.get("/universal-operator/handoffs")
def list_universal_operator_handoffs() -> dict:
    handoffs = universal_operator_service.list_handoffs()
    return {"handoffs": handoffs, "count": len(handoffs)}


@router.post("/universal-operator/handoffs")
def create_universal_operator_handoff(request: UniversalHandoffCreateRequest) -> dict:
    return universal_operator_service.create_handoff(request.model_dump())
