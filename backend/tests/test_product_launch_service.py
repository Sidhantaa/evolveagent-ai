from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_has_all_sections():
    dash = client.get("/api/launch-console/dashboard").json()
    for key in ("version", "positioning", "feature_matrix", "milestones", "demo_mode",
                "exports", "qa", "final_readiness", "disclaimer"):
        assert key in dash
    assert dash["version"] == "v90.0"
    assert dash["milestones"]["implementation_versions"] == 90
    assert "not AGI" in dash["disclaimer"]


def test_positioning_and_pillars():
    dash = client.get("/api/launch-console/dashboard").json()
    pos = dash["positioning"]
    assert pos["name"] == "EvolveAgent AI"
    assert len(pos["pillars"]) >= 4


def test_feature_matrix_and_readiness():
    dash = client.get("/api/launch-console/dashboard").json()
    matrix = dash["feature_matrix"]
    assert matrix["total_features"] >= 20
    assert "by_category" in matrix and "by_status" in matrix
    assert 0 <= dash["final_readiness"]["score"] <= 100
    assert dash["final_readiness"]["status"] in ("launch-ready", "polishing", "in progress")


def test_export_links_present():
    dash = client.get("/api/launch-console/dashboard").json()
    for key in ("portfolio_case_study", "resume_bullets", "package"):
        assert key in dash["exports"]


def test_launch_report_markdown():
    r = client.get("/api/launch-console/report").json()
    assert r["format"] == "markdown"
    assert "Launch Report" in r["content"]
    assert "Final readiness" in r["content"]


def test_summary_and_analytics():
    s = client.get("/api/launch-console/summary").json()
    assert s["version"] == "v90.0" and "final_readiness" in s
    analytics = client.get("/api/analytics").json()
    for key in ("launch_final_readiness", "launch_implementation_versions"):
        assert key in analytics


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/launch-console/dashboard")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "launch_console_viewed" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/release-manager/summary").status_code == 200
    assert client.get("/api/qa-center/summary").status_code == 200
    assert client.post("/api/run", json={"user_input": "Explain EvolveAgent."}).status_code == 200
