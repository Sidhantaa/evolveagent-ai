from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_structure_and_score():
    body = client.get("/api/health-monitor/dashboard").json()
    for key in ("health_score", "status", "checks", "recommendations", "snapshot_count", "note"):
        assert key in body
    assert 0 <= body["health_score"] <= 100
    assert body["status"] in ("healthy", "degraded", "unhealthy")
    names = {c["name"] for c in body["checks"]}
    for expected in ("governance", "approvals_backlog", "secret_readiness", "mcp_connectors", "policies"):
        assert expected in names
    assert "no actions are taken" in body["note"].lower()


def test_checks_have_status_and_detail():
    body = client.get("/api/health-monitor/dashboard").json()
    for check in body["checks"]:
        assert check["status"] in ("ok", "warn", "critical", "info")
        assert check["detail"]


def test_backlog_reflects_pending_approvals():
    # Create a pending business-operator approval → backlog check should count it.
    client.post("/api/business-operator/approvals", json={"title": "pending item", "kind": "payment"})
    body = client.get("/api/health-monitor/dashboard").json()
    backlog = next(c for c in body["checks"] if c["name"] == "approvals_backlog")
    assert backlog["value"] >= 1


def test_snapshot_create_and_list():
    snapshot = client.post("/api/health-monitor/snapshots").json()
    assert snapshot["snapshot_id"]
    assert 0 <= snapshot["health_score"] <= 100
    assert "checks" in snapshot
    listed = client.get("/api/health-monitor/snapshots").json()
    assert any(s["snapshot_id"] == snapshot["snapshot_id"] for s in listed["snapshots"])


def test_recommendations_present():
    body = client.get("/api/health-monitor/dashboard").json()
    assert isinstance(body["recommendations"], list)
    assert len(body["recommendations"]) >= 1


def test_governance_logged_on_snapshot():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/health-monitor/snapshots")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "health_snapshot_created" in actions


def test_analytics_includes_health_fields():
    analytics = client.get("/api/analytics").json()
    for key in ("health_score", "health_warn_checks", "health_critical_checks"):
        assert key in analytics


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/approvals-center/summary").status_code == 200
    assert client.get("/api/operating-layer/dashboard").status_code == 200
