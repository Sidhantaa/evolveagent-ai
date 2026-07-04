from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_suggests_github_for_pr_task():
    result = client.post("/api/mcp/suggest", json={"task": "plan a GitHub pull request workflow"}).json()
    slugs = {s["slug"] for s in result["suggestions"]}
    assert "github" in slugs
    gh = next(s for s in result["suggestions"] if s["slug"] == "github")
    assert any(k["key_name"] == "GITHUB_TOKEN" for k in gh["required_keys"])
    assert "never" in result["note"].lower()


def test_suggests_multiple_for_multi_tool_task():
    result = client.post("/api/mcp/suggest", json={"task": "open a github issue and post to slack"}).json()
    slugs = {s["slug"] for s in result["suggestions"]}
    assert "github" in slugs
    assert "slack" in slugs


def test_key_readiness_reports_boolean_not_value(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "secret-value-should-never-leak-99")
    result = client.post("/api/mcp/suggest", json={"task": "create a github pull request"}).json()
    assert "secret-value-should-never-leak-99" not in str(result)
    gh = next(s for s in result["suggestions"] if s["slug"] == "github")
    assert gh["keys_ready"] is True
    assert gh["required_keys"][0]["is_set"] is True


def test_missing_key_reported():
    result = client.post("/api/mcp/suggest", json={"task": "export a report to notion"}).json()
    notion = next((s for s in result["suggestions"] if s["slug"] == "notion"), None)
    assert notion is not None
    assert "NOTION_API_KEY" in notion["missing_keys"] or notion["keys_ready"]


def test_no_match_returns_empty():
    result = client.post("/api/mcp/suggest", json={"task": "write me a poem about the ocean"}).json()
    assert result["suggestion_count"] == 0


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/mcp/suggest", json={"task": "connect github"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "mcp_suggested" in actions


def test_existing_endpoints_still_work():
    assert client.get("/api/mcp/summary").status_code == 200
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
