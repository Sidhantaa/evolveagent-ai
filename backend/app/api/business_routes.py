"""business routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    business_operator_service,
)
from app.models.request_models import (
    BusinessDocumentCreateRequest,
    BusinessDocumentUpdateRequest,
    BusinessLeadCreateRequest,
    BusinessLeadUpdateRequest,
    BusinessMarketingItemCreateRequest,
    BusinessMarketingItemUpdateRequest,
    BusinessProposalCreateRequest,
    BusinessProposalUpdateRequest,
    BusinessSupportCaseCreateRequest,
    BusinessSupportCaseUpdateRequest,
)

router = APIRouter()


# NOTE: /departments/* routes were extracted into app/api/departments_routes.py (services still live here).


# ----------------------------------------------------------------------
# v18.0 Real Business Automation Layer (Business Operator)
# ----------------------------------------------------------------------
@router.get("/business/dashboard")
def get_business_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    return business_operator_service.dashboard(workspace_id)


@router.get("/business/leads")
def list_business_leads(workspace_id: str | None = Query(default=None)) -> dict:
    leads = business_operator_service.list_leads(workspace_id)
    return {"leads": leads, "count": len(leads)}


@router.post("/business/leads")
def create_business_lead(request: BusinessLeadCreateRequest) -> dict:
    return business_operator_service.create_lead(request.model_dump())


@router.patch("/business/leads/{lead_id}")
def update_business_lead(lead_id: str, request: BusinessLeadUpdateRequest) -> dict:
    try:
        return business_operator_service.update_lead(lead_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Lead not found") from error


@router.get("/business/support-cases")
def list_business_support_cases(workspace_id: str | None = Query(default=None)) -> dict:
    cases = business_operator_service.list_support_cases(workspace_id)
    return {"support_cases": cases, "count": len(cases)}


@router.post("/business/support-cases")
def create_business_support_case(request: BusinessSupportCaseCreateRequest) -> dict:
    return business_operator_service.create_support_case(request.model_dump())


@router.patch("/business/support-cases/{case_id}")
def update_business_support_case(case_id: str, request: BusinessSupportCaseUpdateRequest) -> dict:
    try:
        return business_operator_service.update_support_case(case_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Support case not found") from error


@router.get("/business/documents")
def list_business_documents(workspace_id: str | None = Query(default=None)) -> dict:
    documents = business_operator_service.list_documents(workspace_id)
    return {"documents": documents, "count": len(documents)}


@router.post("/business/documents")
def create_business_document(request: BusinessDocumentCreateRequest) -> dict:
    return business_operator_service.process_document(request.model_dump())


@router.patch("/business/documents/{document_id}")
def update_business_document(document_id: str, request: BusinessDocumentUpdateRequest) -> dict:
    try:
        return business_operator_service.update_document(document_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Document not found") from error


@router.get("/business/proposals")
def list_business_proposals(workspace_id: str | None = Query(default=None)) -> dict:
    proposals = business_operator_service.list_proposals(workspace_id)
    return {"proposals": proposals, "count": len(proposals)}


@router.post("/business/proposals")
def create_business_proposal(request: BusinessProposalCreateRequest) -> dict:
    return business_operator_service.create_proposal(request.model_dump())


@router.patch("/business/proposals/{proposal_id}")
def update_business_proposal(proposal_id: str, request: BusinessProposalUpdateRequest) -> dict:
    try:
        return business_operator_service.update_proposal(proposal_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Proposal not found") from error


@router.get("/business/marketing-calendar")
def list_business_marketing_items(workspace_id: str | None = Query(default=None)) -> dict:
    items = business_operator_service.list_marketing_items(workspace_id)
    return {"marketing_items": items, "count": len(items)}


@router.post("/business/marketing-calendar")
def create_business_marketing_item(request: BusinessMarketingItemCreateRequest) -> dict:
    return business_operator_service.create_marketing_item(request.model_dump())


@router.patch("/business/marketing-calendar/{item_id}")
def update_business_marketing_item(item_id: str, request: BusinessMarketingItemUpdateRequest) -> dict:
    try:
        return business_operator_service.update_marketing_item(item_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Marketing item not found") from error
