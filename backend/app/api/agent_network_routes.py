"""agent-network routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    agent_network_service,
)
from app.models.request_models import (
    AgentContractCreateRequest,
    AgentContractUpdateRequest,
    AgentHandoffCreateRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v23.0 Agent-to-Agent Network
# ----------------------------------------------------------------------
@router.get("/agent-network/dashboard")
def get_agent_network_dashboard() -> dict:
    return agent_network_service.dashboard()


@router.get("/agent-network/audit")
def get_agent_network_audit() -> dict:
    audit = agent_network_service.audit_log()
    return {"audit": audit, "count": len(audit)}


@router.get("/agent-network/contracts")
def list_agent_network_contracts() -> dict:
    contracts = agent_network_service.list_contracts()
    return {"contracts": contracts, "count": len(contracts)}


@router.post("/agent-network/contracts")
def create_agent_network_contract(request: AgentContractCreateRequest) -> dict:
    return agent_network_service.create_contract(request.model_dump())


@router.patch("/agent-network/contracts/{contract_id}")
def update_agent_network_contract(contract_id: str, request: AgentContractUpdateRequest) -> dict:
    try:
        return agent_network_service.update_contract(contract_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Contract not found") from error


@router.post("/agent-network/contracts/{contract_id}/handoff")
def create_agent_network_handoff(contract_id: str, request: AgentHandoffCreateRequest | None = None) -> dict:
    handoff_type = request.handoff_type if request else "local"
    payload = request.payload if request else {}
    target_registry_id = request.target_registry_id if request else None
    capability = request.capability if request else None
    execute = request.execute if request else False
    approved = request.approved if request else False
    try:
        return agent_network_service.create_handoff(
            contract_id, handoff_type, payload,
            target_registry_id=target_registry_id, execute=execute, approved=approved, capability=capability,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Contract not found") from error


@router.post("/agent-network/handoffs/{handoff_id}/verify")
def verify_agent_network_handoff(handoff_id: str) -> dict:
    try:
        return agent_network_service.verify_handoff(handoff_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Handoff not found") from error
