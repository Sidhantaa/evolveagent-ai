from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_templates():
    t = client.get("/api/agent-studio/templates").json()
    assert t["count"] >= 3
    keys = {x["key"] for x in t["templates"]}
    assert "chief_of_staff" in keys


def test_create_and_get_agent():
    created = client.post("/api/agent-studio/agents", json={
        "name": "My Research Agent", "role": "dig up sources",
        "personality": {"tone": "direct", "verbosity": "high"}, "tools": ["retrieval", "search"],
    }).json()
    assert created["version"] == 1
    assert created["personality"]["tone"] == "direct"
    got = client.get(f"/api/agent-studio/agents/{created['agent_id']}").json()
    assert got["name"] == "My Research Agent"


def test_risky_allowed_action_forced_to_approval():
    created = client.post("/api/agent-studio/agents", json={
        "name": "Sender", "role": "x", "guardrails": {"allowed_actions": ["send_email", "read_file"]},
    }).json()
    assert "send_email" in created["guardrails"]["requires_approval"]  # risky → forced to approval


def test_update_bumps_version():
    created = client.post("/api/agent-studio/agents", json={"name": "V", "role": "a"}).json()
    updated = client.put(f"/api/agent-studio/agents/{created['agent_id']}", json={"name": "V2", "role": "b"}).json()
    assert updated["version"] == 2 and updated["name"] == "V2"


def test_mock_test_is_safe():
    created = client.post("/api/agent-studio/agents", json={"name": "T", "role": "help", "tools": ["goals"]}).json()
    r = client.post(f"/api/agent-studio/agents/{created['agent_id']}/test", json={"prompt": "send an email to the team"}).json()
    assert "simulated_response" in r
    assert "no real llm" in r["note"].lower()
    assert r["requires_approval"] is True  # risky prompt held


def test_evaluate_scores_examples():
    created = client.post("/api/agent-studio/agents", json={
        "name": "E", "role": "kubernetes migration expert",
        "examples": [{"input": "how", "output": "migrate services to kubernetes with helm"}],
        "test_cases": [{"input": "q", "expected": "kubernetes migrate"}],
    }).json()
    ev = client.post(f"/api/agent-studio/agents/{created['agent_id']}/evaluate").json()
    assert ev["score"] is not None and 0 <= ev["score"] <= 100


def test_publish_and_import():
    created = client.post("/api/agent-studio/agents", json={"name": "P", "role": "x"}).json()
    pub = client.post(f"/api/agent-studio/agents/{created['agent_id']}/publish-local").json()
    assert pub["published_local"] is True
    imp = client.post("/api/agent-studio/import", json={"profile": {"name": "Imported", "role": "y", "guardrails": {"allowed_actions": ["delete_all"]}}}).json()
    assert imp["name"] == "Imported"
    assert "delete_all" in imp["guardrails"]["requires_approval"]  # sanitized on import


def test_import_invalid_400():
    assert client.post("/api/agent-studio/import", json={"profile": {}}).status_code == 400


def test_summary_analytics_governance():
    client.post("/api/agent-studio/agents", json={"name": "G", "role": "x"})
    assert "total_agents" in client.get("/api/agent-studio/summary").json()
    assert "agent_studio_agents" in client.get("/api/analytics").json()
    after = client.get("/api/governance").json()
    assert "agent_created" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/git-intel/status").status_code == 200
    assert client.get("/api/master-agent/summary").status_code == 200
