from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _mcp_pending() -> str:
    connector = client.post("/api/mcp/connectors", json={"slug": "github"}).json()
    client.post(f"/api/mcp/connectors/{connector['connector_id']}/enable")
    return client.post(
        f"/api/mcp/connectors/{connector['connector_id']}/execute",
        json={"action_name": "draft_pr_comment"},
    ).json()["request_id"]


def _business_pending() -> str:
    return client.post(
        "/api/business-operator/approvals",
        json={"title": "Send external report", "kind": "external_send"},
    ).json()["approval_id"]


def test_center_aggregates_both_sources():
    mcp_id = _mcp_pending()
    biz_id = _business_pending()
    body = client.get("/api/approvals-center").json()
    ids = {i["item_id"] for i in body["items"]}
    assert mcp_id in ids
    assert biz_id in ids
    sources = {i["source"] for i in body["items"]}
    assert "mcp_execution" in sources
    assert "business_operator" in sources


def test_source_filter():
    _mcp_pending()
    _business_pending()
    mcp_only = client.get("/api/approvals-center?source=mcp_execution").json()
    assert all(i["source"] == "mcp_execution" for i in mcp_only["items"])
    biz_only = client.get("/api/approvals-center?source=business_operator").json()
    assert all(i["source"] == "business_operator" for i in biz_only["items"])


def test_summary():
    _mcp_pending()
    summary = client.get("/api/approvals-center/summary").json()
    for key in ("pending_count", "by_source", "by_risk", "high_risk_pending", "sources", "top_items", "note"):
        assert key in summary
    assert summary["pending_count"] >= 1


def test_approve_mcp_delegates():
    mcp_id = _mcp_pending()
    approved = client.post("/api/approvals-center/approve", json={"source": "mcp_execution", "item_id": mcp_id}).json()
    assert approved["status"] == "approved"
    # No longer pending in the center.
    ids = {i["item_id"] for i in client.get("/api/approvals-center").json()["items"]}
    assert mcp_id not in ids


def test_reject_business_delegates():
    biz_id = _business_pending()
    rejected = client.post("/api/approvals-center/reject", json={"source": "business_operator", "item_id": biz_id}).json()
    assert rejected["status"] == "rejected"


def test_prioritizes_high_risk_first():
    # payment (high) should outrank external_send (medium).
    client.post("/api/business-operator/approvals", json={"title": "low-ish", "kind": "external_send"})
    client.post("/api/business-operator/approvals", json={"title": "pay", "kind": "payment"})
    items = client.get("/api/approvals-center").json()["items"]
    priorities = [i["priority"] for i in items]
    assert priorities == sorted(priorities, reverse=True)
    assert items[0]["risk_level"] == "high"


def test_approve_missing_and_unknown_source():
    assert client.post("/api/approvals-center/approve", json={"source": "mcp_execution", "item_id": "nope"}).status_code == 404
    # Unknown source is rejected by the request model (422).
    assert client.post("/api/approvals-center/approve", json={"source": "bogus", "item_id": "x"}).status_code == 422


def test_governance_logged_on_decision():
    mcp_id = _mcp_pending()
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/approvals-center/approve", json={"source": "mcp_execution", "item_id": mcp_id})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before  # delegated service logs the decision


def test_analytics_includes_center_fields():
    analytics = client.get("/api/analytics").json()
    for key in ("approvals_center_pending", "approvals_center_high_risk_pending", "approvals_center_sources"):
        assert key in analytics


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/mcp/inbox").status_code == 200
    assert client.get("/api/business-operator/dashboard").status_code == 200
    assert client.get("/api/operating-layer/dashboard").status_code == 200
