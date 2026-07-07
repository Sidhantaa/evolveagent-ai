from fastapi.testclient import TestClient

from app.main import app
from app.services.agent_governance_service import AgentGovernanceService
from app.services.agent_registry_service import AgentRegistryService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

client = TestClient(app)


def _services(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    s.write_list("agent_profiles.json", [{
        "agent_id": "a1", "name": "Sender", "role": "outreach", "published_local": True,
        "guardrails": {"requires_approval": ["send_email"]}, "evaluation": {"score": 90},
        "tools": ["retrieval", "email"],
    }, {
        "agent_id": "a2", "name": "Reader", "role": "read only", "published_local": True,
        "guardrails": {}, "evaluation": {"score": 95}, "tools": [],
    }])
    s.write_list("custom_agents.json", [])
    s.write_list("agent_departments.json", [])
    g = GovernanceService(s)
    registry = AgentRegistryService(s, g)
    return s, g, registry, AgentGovernanceService(s, g, registry)


def test_approval_gated_agent_scores_higher_and_requires_approval(tmp_path):
    _, _, _, gov = _services(tmp_path)
    risk = gov.list_agent_risk()
    by_name = {a["name"]: a for a in risk["agents"]}
    assert by_name["Sender"]["requires_approval"] is True
    assert by_name["Sender"]["risk_score"] > by_name["Reader"]["risk_score"]
    assert by_name["Reader"]["requires_approval"] is False  # no gate, no high risk


def test_high_quality_lowers_score_low_quality_raises_it(tmp_path):
    _, _, _, gov = _services(tmp_path)
    low = gov.score_agent({"quality_score": 20})
    high = gov.score_agent({"quality_score": 95})
    baseline = gov.score_agent({})
    assert low["score"] > baseline["score"] > high["score"]


def test_get_agent_risk_not_found_raises(tmp_path):
    _, _, _, gov = _services(tmp_path)
    import pytest
    with pytest.raises(ValueError):
        gov.get_agent_risk("studio:does-not-exist")


def test_policy_is_deny_only_and_never_widens_access(tmp_path):
    _, _, _, gov = _services(tmp_path)
    policy = gov.create_policy({"name": "block outreach", "source": "agent_studio", "name_contains": "sender"})
    assert policy["effect"] == "deny"
    updated = gov.update_policy(policy["policy_id"], {"enabled": True})
    assert updated["effect"] == "deny"  # cannot be changed even via update


def test_policy_blocks_matching_agent_only(tmp_path):
    _, _, registry, gov = _services(tmp_path)
    gov.create_policy({"name": "no senders", "source": "agent_studio", "name_contains": "sender"})
    sender = gov.get_agent_risk("studio:a1")
    reader = gov.get_agent_risk("studio:a2")
    assert sender["policy_allowed"] is False and sender["policy_id"]
    assert reader["policy_allowed"] is True


def test_approval_gated_requires_approval_even_if_policy_allows(tmp_path):
    # A policy that ALLOWS (i.e., doesn't match) never removes the approval_gated
    # requirement -- there is no "allow" effect that could loosen this.
    _, _, _, gov = _services(tmp_path)
    sender = gov.get_agent_risk("studio:a1")
    assert sender["policy_allowed"] is True  # no matching deny policy
    assert sender["requires_approval"] is True  # but still gated, from its own flag


def test_disabled_policy_does_not_block(tmp_path):
    _, _, _, gov = _services(tmp_path)
    p = gov.create_policy({"name": "no senders", "source": "agent_studio", "name_contains": "sender"})
    gov.update_policy(p["policy_id"], {"enabled": False})
    sender = gov.get_agent_risk("studio:a1")
    assert sender["policy_allowed"] is True


def test_min_level_filters_risk_list(tmp_path):
    _, _, _, gov = _services(tmp_path)
    all_agents = gov.list_agent_risk()["count"]
    medium_plus = gov.list_agent_risk(min_level="medium")["count"]
    assert medium_plus <= all_agents


def test_endpoints_end_to_end():
    risk = client.get("/api/governance/risk/agents").json()
    assert "agents" in risk and "by_level" in risk
    created = client.post("/api/governance/agent-policies", json={"name": "e2e deny", "source": "*", "risk_level": "*"}).json()
    assert created["effect"] == "deny"
    fetched = client.get(f"/api/governance/agent-policies/{created['policy_id']}").json()
    assert fetched["policy_id"] == created["policy_id"]
    updated = client.patch(f"/api/governance/agent-policies/{created['policy_id']}", json={"enabled": False}).json()
    assert updated["enabled"] is False
    assert client.get("/api/governance/agent-policies/does-not-exist").status_code == 404
    summary = client.get("/api/governance/agent-policies/summary").json()
    assert summary["effect"] == "deny_only"
    assert "agent_governance_policies" in client.get("/api/analytics").json()


def test_existing_endpoints_still_work():
    assert client.get("/api/agent-registry").status_code == 200
    assert client.get("/api/mcp/adapter/status").status_code == 200
