"""Agent Governance routes (v100 stretch) — risk scoring + tighten-only policies
for the Agent Registry. Imports the shared service from routes.py."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.routes import agent_governance_service
from app.models.request_models import AgentPolicyCreateRequest, AgentPolicyUpdateRequest

router = APIRouter()


@router.get("/governance/risk/agents")
def governance_risk_agents(source: str | None = None, min_level: str | None = None, limit: int = 200) -> dict:
    return agent_governance_service.list_agent_risk(source, min_level, limit)


@router.get("/governance/risk/agents/{registry_id:path}")
def governance_risk_agent_detail(registry_id: str) -> dict:
    try:
        return agent_governance_service.get_agent_risk(registry_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/governance/agent-policies")
def list_agent_policies() -> dict:
    return {"policies": agent_governance_service.list_policies()}


@router.post("/governance/agent-policies")
def create_agent_policy(request: AgentPolicyCreateRequest) -> dict:
    return agent_governance_service.create_policy(request.model_dump())


@router.get("/governance/agent-policies/summary")
def agent_policies_summary() -> dict:
    return agent_governance_service.summarize_policies()


@router.get("/governance/agent-policies/{policy_id}")
def get_agent_policy(policy_id: str) -> dict:
    policy = agent_governance_service.get_policy(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.patch("/governance/agent-policies/{policy_id}")
def update_agent_policy(policy_id: str, request: AgentPolicyUpdateRequest) -> dict:
    try:
        return agent_governance_service.update_policy(policy_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
