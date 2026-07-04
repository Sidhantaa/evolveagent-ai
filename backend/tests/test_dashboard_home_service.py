from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home_has_all_sections():
    home = client.get("/api/home").json()
    for key in ("today", "active_workspace", "pending_approvals", "recent_runs",
                "system_health", "upcoming_tasks", "suggested_actions", "quick_launch"):
        assert key in home
    assert len(home["quick_launch"]) >= 6
    assert "score" in home["system_health"]


def test_today_counts_are_numbers():
    home = client.get("/api/home").json()
    today = home["today"]
    for key in ("events_today", "pending_approvals", "upcoming_tasks"):
        assert isinstance(today[key], int)


def test_recent_runs_reflect_master_agent_activity():
    client.post("/api/master-agent/route", json={"text": "Review this Python function."})
    home = client.get("/api/home").json()
    assert isinstance(home["recent_runs"], list)
    if home["recent_runs"]:
        assert "domain" in home["recent_runs"][0]


def test_suggested_actions_present():
    home = client.get("/api/home").json()
    assert len(home["suggested_actions"]) >= 1
    assert all(isinstance(a, str) for a in home["suggested_actions"])


def test_home_is_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/home")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {e.get("action_type") for e in after["recent_events"]}
    assert "dashboard_home_viewed" in actions


def test_analytics_includes_dashboard():
    analytics = client.get("/api/analytics").json()
    assert "dashboard_quick_launch_cards" in analytics


def test_existing_endpoints_still_work():
    assert client.get("/api/activity/summary").status_code == 200
    assert client.get("/api/search/sources").status_code == 200
