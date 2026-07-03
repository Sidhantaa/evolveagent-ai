from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _enabled_connector(slug: str) -> str:
    connector = client.post("/api/mcp/connectors", json={"slug": slug}).json()
    client.post(f"/api/mcp/connectors/{connector['connector_id']}/enable")
    return connector["connector_id"]


def _execution_request(connector_id: str, action_name: str) -> str:
    return client.post(
        f"/api/mcp/connectors/{connector_id}/execute",
        json={"action_name": action_name},
    ).json()["request_id"]


def test_timeline_aggregates_sources():
    connector_id = _enabled_connector("github")
    _execution_request(connector_id, "draft_pr_comment")
    body = client.get("/api/mcp/audit").json()
    assert body["count"] >= 1
    sources = {e["source"] for e in body["events"]}
    # Connector events + execution requests + governance should all appear over the session.
    assert "connector_event" in sources or "execution_request" in sources


def test_timeline_filter_by_connector():
    connector_id = _enabled_connector("linear")
    _execution_request(connector_id, "list_issues")
    body = client.get(f"/api/mcp/audit?connector_id={connector_id}").json()
    assert all(e.get("connector_id") in (connector_id, None) for e in body["events"])


def test_summary():
    summary = client.get("/api/mcp/audit/summary").json()
    for key in ("total_events", "by_source", "blocked_events", "replay_count", "recent", "note"):
        assert key in summary


def test_export_markdown_and_json():
    md = client.get("/api/mcp/audit/export?format=markdown").json()
    assert md["format"] == "markdown"
    assert "# MCP Audit Timeline" in md["content"]
    js = client.get("/api/mcp/audit/export?format=json").json()
    assert js["format"] == "json"
    assert js["content"].strip().startswith("[")


def test_replay_is_read_only():
    connector_id = _enabled_connector("github")
    request_id = _execution_request(connector_id, "draft_pr_comment")
    replay = client.post("/api/mcp/audit/replay", json={"request_id": request_id}).json()
    assert replay["replay_id"]
    assert replay["replay_only"] is True
    assert "current_plan" in replay
    assert "no action was executed" in replay["note"].lower()
    listed = client.get("/api/mcp/audit/replays").json()
    assert any(r["replay_id"] == replay["replay_id"] for r in listed["replays"])


def test_replay_missing_request_404():
    assert client.post("/api/mcp/audit/replay", json={"request_id": "nope"}).status_code == 404


def test_replay_reflects_policy_change():
    # A policy added after the request should change what replay derives.
    connector_id = _enabled_connector("v46replay")  # custom slug
    request_id = _execution_request(connector_id, "some_action")
    client.post("/api/mcp/policies", json={"name": "block v46replay", "connector_slug": "v46replay", "action": "some_action"})
    replay = client.post("/api/mcp/audit/replay", json={"request_id": request_id}).json()
    assert replay["would_be_allowed"] is False


def test_governance_logged_on_replay():
    connector_id = _enabled_connector("linear")
    request_id = _execution_request(connector_id, "list_issues")
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/mcp/audit/replay", json={"request_id": request_id})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "mcp_replay" in actions


def test_analytics_includes_audit_fields():
    analytics = client.get("/api/analytics").json()
    for key in ("mcp_audit_events", "mcp_replays"):
        assert key in analytics


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/mcp/summary").status_code == 200
    assert client.get("/api/operating-layer/dashboard").status_code == 200
