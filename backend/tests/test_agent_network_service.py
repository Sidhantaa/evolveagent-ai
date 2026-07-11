import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_custom_agent(**overrides) -> dict:
    tag = uuid.uuid4().hex[:8]
    payload = {
        "name": overrides.get("name", f"Workforce Test Agent {tag}"),
        "role": "Answer questions about testing.",
        "prompt": "You are a test agent. Reply with a short confirmation.",
        "tools_allowed": overrides.get("tools_allowed", [f"capability-{tag}"]),
        "approval_level": overrides.get("approval_level", "read_only"),
    }
    response = client.post("/api/agents/custom", json=payload)
    assert response.status_code == 200
    return response.json()


def _create_contract(**overrides) -> dict:
    payload = {
        "source_agent": overrides.get("source_agent", "Master Orchestrator Agent"),
        "target_agent": overrides.get("target_agent", "Research Agent"),
        "task": overrides.get("task", "Summarize the latest findings"),
        "expected_output": overrides.get("expected_output", "A concise findings summary"),
        "constraints": overrides.get("constraints", ["No external calls"]),
    }
    response = client.post("/api/agent-network/contracts", json=payload)
    assert response.status_code == 200
    return response.json()


def test_create_and_update_contract():
    created = _create_contract()
    assert created["contract_id"]
    assert created["status"] == "draft"
    assert created["constraints"] == ["No external calls"]

    listed = client.get("/api/agent-network/contracts").json()
    assert any(c["contract_id"] == created["contract_id"] for c in listed["contracts"])

    updated = client.patch(f"/api/agent-network/contracts/{created['contract_id']}", json={"status": "sent"}).json()
    assert updated["status"] == "sent"


def test_contract_not_found():
    assert client.patch("/api/agent-network/contracts/missing", json={"status": "sent"}).status_code == 404
    assert client.post("/api/agent-network/contracts/missing/handoff", json={}).status_code == 404


def test_create_handoff():
    contract = _create_contract(task="Summarize findings about agents")
    handoff = client.post(
        f"/api/agent-network/contracts/{contract['contract_id']}/handoff",
        json={"handoff_type": "local", "payload": {"k": "v"}},
    ).json()
    assert handoff["handoff_id"]
    assert handoff["contract_id"] == contract["contract_id"]
    assert handoff["handoff_type"] == "local"
    assert handoff["result"]["output"]
    assert "mock" in handoff["result"]["note"].lower()
    # Contract should advance to completed.
    refreshed = client.get("/api/agent-network/contracts").json()["contracts"]
    target = next(c for c in refreshed if c["contract_id"] == contract["contract_id"])
    assert target["status"] == "completed"


def test_external_mock_handoff_is_labeled():
    contract = _create_contract()
    handoff = client.post(
        f"/api/agent-network/contracts/{contract['contract_id']}/handoff",
        json={"handoff_type": "external_mock", "payload": {}},
    ).json()
    assert handoff["handoff_type"] == "external_mock"
    assert "no real external agent" in handoff["result"]["note"].lower()


def test_verify_handoff():
    contract = _create_contract(task="Summarize findings", expected_output="findings summary")
    handoff = client.post(f"/api/agent-network/contracts/{contract['contract_id']}/handoff", json={}).json()
    verified = client.post(f"/api/agent-network/handoffs/{handoff['handoff_id']}/verify").json()
    assert "verification" in verified
    assert "verified" in verified["verification"]
    assert isinstance(verified["verification"]["checks"], list) and verified["verification"]["checks"]
    assert client.post("/api/agent-network/handoffs/missing/verify").status_code == 404


def test_audit_log_written():
    contract = _create_contract()
    client.post(f"/api/agent-network/contracts/{contract['contract_id']}/handoff", json={})
    audit = client.get("/api/agent-network/audit").json()
    assert audit["count"] >= 1
    event_types = {entry["event_type"] for entry in audit["audit"]}
    assert "contract_created" in event_types or "handoff_created" in event_types


def test_dashboard_shape():
    _create_contract()
    body = client.get("/api/agent-network/dashboard").json()
    for key in ("total_contracts", "contract_status_counts", "total_handoffs", "verified_handoffs", "audit_event_count", "recent_audit"):
        assert key in body
    assert body["total_contracts"] >= 1


def test_governance_event_written():
    before = client.get("/api/governance").json()["total_events"]
    _create_contract()
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "agent_network_contract_created" in actions


# ------------------------------------------------------------------
# Agent workforce: real execution + real governance enforcement, previously
# both mock-only (handoff) or computed-but-never-checked (governance policy).
# ------------------------------------------------------------------
def test_execute_true_without_target_falls_back_to_mock():
    contract = _create_contract()
    handoff = client.post(
        f"/api/agent-network/contracts/{contract['contract_id']}/handoff",
        json={"execute": True},
    ).json()
    assert handoff["executed"] is False
    assert "no target_registry_id or capability" in handoff["result"]["note"].lower()


def test_execute_declines_when_agent_requires_approval_and_not_approved():
    agent = _create_custom_agent()
    registry_id = f"custom:{agent['agent_id']}"
    contract = _create_contract(task="Do the test task")
    handoff = client.post(
        f"/api/agent-network/contracts/{contract['contract_id']}/handoff",
        json={"execute": True, "target_registry_id": registry_id},
    ).json()
    assert handoff["executed"] is False
    assert "requires approval" in handoff["result"]["note"].lower()


def test_execute_real_dispatches_to_custom_agent_when_approved():
    agent = _create_custom_agent()
    registry_id = f"custom:{agent['agent_id']}"
    contract = _create_contract(task="Do the test task")
    handoff = client.post(
        f"/api/agent-network/contracts/{contract['contract_id']}/handoff",
        json={"execute": True, "target_registry_id": registry_id, "approved": True},
    ).json()
    assert handoff["executed"] is True
    assert handoff["result"]["produced_by"] == agent["name"]
    assert handoff["result"]["output"]
    assert "real execution" in handoff["result"]["note"].lower()


def test_execute_resolves_target_by_capability():
    agent = _create_custom_agent()
    capability = agent["tools_allowed"][0]
    contract = _create_contract(task="Do the capability-routed task")
    handoff = client.post(
        f"/api/agent-network/contracts/{contract['contract_id']}/handoff",
        json={"execute": True, "capability": capability, "approved": True},
    ).json()
    assert handoff["executed"] is True
    assert handoff["result"]["produced_by"] == agent["name"]


def test_execute_unknown_target_registry_id_declines_safely():
    contract = _create_contract()
    handoff = client.post(
        f"/api/agent-network/contracts/{contract['contract_id']}/handoff",
        json={"execute": True, "target_registry_id": "custom:does-not-exist", "approved": True},
    ).json()
    assert handoff["executed"] is False
    assert "not found" in handoff["result"]["note"].lower()


def test_execute_blocked_by_deny_policy_even_when_approved():
    tag = uuid.uuid4().hex[:8]
    agent = _create_custom_agent(name=f"Policy Denied Agent {tag}")
    registry_id = f"custom:{agent['agent_id']}"
    policy = client.post("/api/governance/agent-policies", json={
        "name": f"Deny test {tag}",
        "source": "custom_agents",
        "name_contains": f"policy denied agent {tag}".lower(),
    }).json()
    assert policy["effect"] == "deny"
    contract = _create_contract(task="Should be blocked")
    handoff = client.post(
        f"/api/agent-network/contracts/{contract['contract_id']}/handoff",
        json={"execute": True, "target_registry_id": registry_id, "approved": True},
    ).json()
    assert handoff["executed"] is False
    assert "blocked by policy" in handoff["result"]["note"].lower()


def test_execute_false_with_target_still_mocks():
    agent = _create_custom_agent()
    registry_id = f"custom:{agent['agent_id']}"
    contract = _create_contract()
    handoff = client.post(
        f"/api/agent-network/contracts/{contract['contract_id']}/handoff",
        json={"target_registry_id": registry_id},  # execute defaults to False
    ).json()
    assert handoff["executed"] is False
    assert "mock" in handoff["result"]["note"].lower()


def test_existing_endpoints_still_pass():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/industry-modes/dashboard").status_code == 200
    assert client.get("/api/multimodal/dashboard").status_code == 200
    assert client.get("/api/business/dashboard").status_code == 200
