from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _enabled_connector(slug: str) -> str:
    connector = client.post("/api/mcp/connectors", json={"slug": slug}).json()
    client.post(f"/api/mcp/connectors/{connector['connector_id']}/enable")
    return connector["connector_id"]


def _pending_request(connector_id: str, action_name: str) -> str:
    request = client.post(
        f"/api/mcp/connectors/{connector_id}/execute",
        json={"action_name": action_name},
    ).json()
    assert request["status"] == "pending_approval"
    return request["request_id"]


def test_inbox_lists_pending_with_enrichment():
    connector_id = _enabled_connector("github")
    request_id = _pending_request(connector_id, "draft_pr_comment")
    inbox = client.get("/api/mcp/inbox").json()
    item = next((i for i in inbox["items"] if i["item_id"] == request_id), None)
    assert item is not None
    assert item["source"] == "mcp_execution"
    assert item["connector_name"]  # enriched with connector name
    assert item["risk_level"] in ("low", "medium", "high")
    assert "priority" in item and "age_seconds" in item
    assert item["recommended_action"]


def test_inbox_prioritizes_high_risk_first():
    # Filesystem is high-risk; GitHub is medium.
    fs = _enabled_connector("filesystem")
    gh = _enabled_connector("github")
    _pending_request(gh, "draft_pr_comment")           # medium
    _pending_request(fs, "propose_file_edit")          # high
    items = client.get("/api/mcp/inbox").json()["items"]
    # The first item should be the highest priority (high risk).
    assert items[0]["risk_level"] == "high"
    priorities = [i["priority"] for i in items]
    assert priorities == sorted(priorities, reverse=True)


def test_inbox_risk_filter():
    fs = _enabled_connector("filesystem")
    _pending_request(fs, "propose_file_edit")  # high
    high = client.get("/api/mcp/inbox?risk_level=high").json()
    assert all(i["risk_level"] == "high" for i in high["items"])
    assert high["count"] >= 1


def test_inbox_summary():
    connector_id = _enabled_connector("linear")
    _pending_request(connector_id, "update_status_with_approval")
    summary = client.get("/api/mcp/inbox/summary").json()
    for key in ("pending_count", "by_risk", "high_risk_pending", "oldest_pending_seconds", "top_items", "note"):
        assert key in summary
    assert summary["pending_count"] >= 1


def test_inbox_approve_moves_request_to_approved():
    connector_id = _enabled_connector("github")
    request_id = _pending_request(connector_id, "draft_pr_comment")
    approved = client.post(f"/api/mcp/inbox/{request_id}/approve").json()
    assert approved["status"] == "approved"
    # It should then be runnable via the execution service.
    ran = client.post(f"/api/mcp/executions/{request_id}/run").json()
    assert ran["status"] == "executed"
    # And it should no longer appear in the inbox.
    inbox = client.get("/api/mcp/inbox").json()
    assert all(i["item_id"] != request_id for i in inbox["items"])


def test_inbox_reject_moves_request_to_rejected():
    connector_id = _enabled_connector("linear")
    request_id = _pending_request(connector_id, "update_status_with_approval")
    rejected = client.post(f"/api/mcp/inbox/{request_id}/reject").json()
    assert rejected["status"] == "rejected"
    assert client.post(f"/api/mcp/inbox/missing/approve").status_code == 404


def test_inbox_approve_missing_returns_404():
    assert client.post("/api/mcp/inbox/does-not-exist/approve").status_code == 404
    assert client.post("/api/mcp/inbox/does-not-exist/reject").status_code == 404


def test_governance_logged_on_inbox_approve():
    connector_id = _enabled_connector("github")
    request_id = _pending_request(connector_id, "draft_pr_comment")
    before = client.get("/api/governance").json()["total_events"]
    client.post(f"/api/mcp/inbox/{request_id}/approve")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "mcp_execution_approved" in actions


def test_analytics_includes_inbox_fields():
    analytics = client.get("/api/analytics").json()
    for key in ("mcp_inbox_pending", "mcp_inbox_high_risk_pending", "mcp_inbox_oldest_pending_seconds"):
        assert key in analytics


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/mcp/summary").status_code == 200
    assert client.get("/api/mcp/executions/summary").status_code == 200
    assert client.get("/api/operating-layer/dashboard").status_code == 200
