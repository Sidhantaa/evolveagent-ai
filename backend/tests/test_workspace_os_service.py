from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_workspace():
    resp = client.post("/api/workspaces", json={"name": "v70 WS OS test"})
    data = resp.json()
    return data.get("workspace_id") or data.get("id") or (data.get("workspace") or {}).get("workspace_id")


def test_dashboard_has_all_sections():
    wid = _make_workspace()
    dash = client.get(f"/api/workspace-os/{wid}/dashboard").json()
    for key in ("workspace_id", "feature_usage", "memory_graph", "agents", "reports", "timeline", "health"):
        assert key in dash
    assert "score" in dash["health"] and "status" in dash["health"]
    assert "node_count" in dash["memory_graph"] and "edge_count" in dash["memory_graph"]


def test_feature_usage_reflects_scoped_goal():
    wid = _make_workspace()
    client.post("/api/goals", json={"title": "WS-scoped goal", "description": "x", "workspace_id": wid})
    dash = client.get(f"/api/workspace-os/{wid}/dashboard").json()
    assert dash["feature_usage"]["goals"] >= 1
    assert dash["health"]["score"] >= 0


def test_unknown_workspace_is_handled():
    dash = client.get("/api/workspace-os/does-not-exist/dashboard").json()
    assert dash["exists"] is False
    assert dash["health"]["status"] in ("sparse", "developing", "healthy")


def test_summary_lists_workspaces():
    _make_workspace()
    summary = client.get("/api/workspace-os/summary").json()
    assert summary["total_workspaces"] >= 1
    assert isinstance(summary["workspaces"], list)
    if summary["workspaces"]:
        assert "health" in summary["workspaces"][0]


def test_governance_logged_and_analytics():
    wid = _make_workspace()
    before = client.get("/api/governance").json()["total_events"]
    client.get(f"/api/workspace-os/{wid}/dashboard")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "workspace_os_viewed" in {e.get("action_type") for e in after["recent_events"]}
    assert "workspace_os_total_workspaces" in client.get("/api/analytics").json()


def test_existing_endpoints_still_work():
    assert client.get("/api/notifications-inbox/summary").status_code == 200
    assert client.get("/api/provider-control/summary").status_code == 200
