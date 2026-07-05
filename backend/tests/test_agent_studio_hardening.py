from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make(name="Base", role="help with things"):
    return client.post("/api/agent-studio/agents", json={"name": name, "role": role, "tools": ["retrieval"]}).json()


def test_duplicate_creates_independent_copy():
    src = _make("Original", "do research")
    dup = client.post(f"/api/agent-studio/agents/{src['agent_id']}/duplicate").json()
    assert dup["agent_id"] != src["agent_id"]
    assert dup["name"] == "Original (copy)"
    assert dup["version"] == 1 and dup["role"] == "do research"


def test_versions_recorded_on_update():
    a = _make("Vers", "v1 role")
    client.put(f"/api/agent-studio/agents/{a['agent_id']}", json={"name": "Vers", "role": "v2 role"})
    client.put(f"/api/agent-studio/agents/{a['agent_id']}", json={"name": "Vers", "role": "v3 role"})
    v = client.get(f"/api/agent-studio/agents/{a['agent_id']}/versions").json()
    assert v["current_version"] == 3
    assert v["count"] == 2  # v1 and v2 snapshotted
    assert {s["version"] for s in v["versions"]} == {1, 2}


def test_rollback_restores_prior_config():
    a = _make("Roll", "original role")
    client.put(f"/api/agent-studio/agents/{a['agent_id']}", json={"name": "Roll", "role": "changed role"})
    # roll back to version 1's config
    rolled = client.post(f"/api/agent-studio/agents/{a['agent_id']}/rollback", json={"version": 1}).json()
    assert rolled["role"] == "original role"
    assert rolled["version"] == 3  # rollback is itself a new version


def test_rollback_missing_version_400():
    a = _make("NoHist", "x")
    assert client.post(f"/api/agent-studio/agents/{a['agent_id']}/rollback", json={"version": 9}).status_code == 400


def test_preview_assembles_context():
    a = client.post("/api/agent-studio/agents", json={
        "name": "Prev", "role": "summarize docs", "tools": ["retrieval"],
        "examples": [{"input": "how?", "output": "use retrieval then summarize"}],
    }).json()
    p = client.get(f"/api/agent-studio/agents/{a['agent_id']}/preview").json()
    assert "Prev" in p["preview"] and "summarize docs" in p["preview"]
    assert p["example_count"] == 1


def test_evaluate_reports_grade_and_missing_keywords():
    a = client.post("/api/agent-studio/agents", json={
        "name": "Eval", "role": "kubernetes helm migration",
        "examples": [{"input": "how", "output": "migrate with helm to kubernetes"}],
        "test_cases": [{"input": "q", "expected": "kubernetes helm nonexistentword"}],
    }).json()
    ev = client.post(f"/api/agent-studio/agents/{a['agent_id']}/evaluate").json()
    assert ev["grade"] in {"A", "B", "C", "D", "F"}
    assert "nonexistentword" in ev["case_scores"][0]["missing_keywords"]


def test_existing_endpoints_still_work():
    assert client.get("/api/agent-studio/summary").status_code == 200
    assert client.get("/api/repo-finder/status").status_code == 200
