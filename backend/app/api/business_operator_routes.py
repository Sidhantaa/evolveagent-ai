"""business-operator routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    business_operator_advanced_service,
)
from app.models.request_models import (
    BusinessApprovalCreateRequest,
    BusinessApprovalDecisionRequest,
    BusinessReportCreateRequest,
    BusinessWorkflowCreateRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v33.0 AI Business Operator Advanced (extends v18; draft-only)
# ----------------------------------------------------------------------
@router.get("/business-operator/dashboard")
def get_business_operator_dashboard() -> dict:
    return business_operator_advanced_service.dashboard()


@router.get("/business-operator/audit")
def get_business_operator_audit() -> dict:
    audit = business_operator_advanced_service.audit_log()
    return {"audit": audit, "count": len(audit)}


@router.get("/business-operator/workflows")
def list_business_operator_workflows() -> dict:
    workflows = business_operator_advanced_service.list_workflows()
    return {"workflows": workflows, "count": len(workflows)}


@router.post("/business-operator/workflows")
def create_business_operator_workflow(request: BusinessWorkflowCreateRequest) -> dict:
    return business_operator_advanced_service.create_workflow(request.model_dump())


@router.get("/business-operator/reports")
def list_business_operator_reports() -> dict:
    reports = business_operator_advanced_service.list_reports()
    return {"reports": reports, "count": len(reports)}


@router.post("/business-operator/reports")
def create_business_operator_report(request: BusinessReportCreateRequest | None = None) -> dict:
    return business_operator_advanced_service.create_report(request.model_dump() if request else {})


@router.get("/business-operator/kpi-snapshots")
def list_business_operator_kpi_snapshots() -> dict:
    snapshots = business_operator_advanced_service.list_kpi_snapshots()
    return {"kpi_snapshots": snapshots, "count": len(snapshots)}


@router.post("/business-operator/kpi-snapshots")
def create_business_operator_kpi_snapshot() -> dict:
    return business_operator_advanced_service.create_kpi_snapshot()


@router.get("/business-operator/approvals")
def list_business_operator_approvals() -> dict:
    approvals = business_operator_advanced_service.list_approvals()
    return {"approvals": approvals, "count": len(approvals)}


@router.post("/business-operator/approvals")
def create_business_operator_approval(request: BusinessApprovalCreateRequest) -> dict:
    return business_operator_advanced_service.create_approval(request.model_dump())


@router.patch("/business-operator/approvals/{approval_id}")
def update_business_operator_approval(approval_id: str, request: BusinessApprovalDecisionRequest) -> dict:
    try:
        return business_operator_advanced_service.update_approval(approval_id, request.decision)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Approval not found") from error
