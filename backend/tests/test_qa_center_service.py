from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_has_readiness_and_matrix():
    dash = client.get("/api/qa-center/dashboard").json()
    for key in ("release_readiness_score", "readiness_status", "verification",
                "failed_feature_tracker", "regression_dashboard", "qa_checklist"):
        assert key in dash
    assert 0 <= dash["release_readiness_score"] <= 100
    assert len(dash["qa_checklist"]) >= 4


def test_matrix_lists_features():
    m = client.get("/api/qa-center/matrix").json()
    assert m["count"] >= 20
    row = m["matrix"][0]
    for key in ("key", "name", "route", "demo_safe", "qa_status"):
        assert key in row
    assert row["qa_status"] in ("unverified", "pass", "fail", "skip")


def test_record_updates_matrix_and_readiness():
    client.post("/api/qa-center/record", json={"feature_key": "master-agent", "status": "pass"})
    m = client.get("/api/qa-center/matrix").json()["matrix"]
    row = next(r for r in m if r["key"] == "master-agent")
    assert row["qa_status"] == "pass"


def test_fail_appears_in_tracker():
    client.post("/api/qa-center/record", json={"feature_key": "global-search", "status": "fail", "note": "broken"})
    dash = client.get("/api/qa-center/dashboard").json()
    assert any(r["key"] == "global-search" for r in dash["failed_feature_tracker"])


def test_summary_and_analytics():
    s = client.get("/api/qa-center/summary").json()
    for key in ("release_readiness_score", "verified", "failed"):
        assert key in s
    analytics = client.get("/api/analytics").json()
    for key in ("qa_results", "qa_failed"):
        assert key in analytics


def test_record_is_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/qa-center/record", json={"feature_key": "activity-timeline", "status": "pass"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "qa_recorded" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/integration-hub/summary").status_code == 200
    assert client.get("/api/plugin-marketplace/summary").status_code == 200
