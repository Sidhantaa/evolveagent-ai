from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_route_returns_confidence_and_explanation():
    result = client.post("/api/master-agent/route", json={"text": "Review this Python function and refactor the bug."}).json()
    assert result["intent"]["primary_domain"] == "Coding & Review"
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["fallback_used"] is False
    assert "Coding & Review" in result["route_explanation"]
    assert result["suggested_workflow"]  # a workflow suggestion is offered before execution


def test_uncertain_request_uses_fallback_route():
    result = client.post("/api/master-agent/route", json={"text": "zxqw"}).json()
    assert result["fallback_used"] is True
    assert result["intent"]["primary_domain"] == "Research & Retrieval"
    assert "fell back" in result["route_explanation"].lower()


def test_route_feedback_updates_accuracy():
    routed = client.post("/api/master-agent/route", json={"text": "Summarize the compliance policy."}).json()
    run_id = routed["run_id"]
    fb = client.post(f"/api/master-agent/route/{run_id}/feedback", json={"correct": True}).json()
    assert fb["feedback"]["correct"] is True
    assert fb["route_accuracy"]["rated_routes"] >= 1
    assert fb["route_accuracy"]["accuracy_pct"] is not None


def test_feedback_unknown_run_404():
    resp = client.post("/api/master-agent/route/does-not-exist/feedback", json={"correct": False})
    assert resp.status_code == 404


def test_summary_exposes_confidence_and_accuracy():
    client.post("/api/master-agent/route", json={"text": "Plan a GitHub pull request workflow."})
    summary = client.get("/api/master-agent/summary").json()
    for key in ("fallback_routes", "avg_confidence", "route_accuracy"):
        assert key in summary
    assert "accuracy_pct" in summary["route_accuracy"]


def test_analytics_includes_router_metrics():
    analytics = client.get("/api/analytics").json()
    for key in ("master_agent_fallback_routes", "master_agent_route_accuracy_pct"):
        assert key in analytics


def test_feedback_is_governance_logged():
    routed = client.post("/api/master-agent/route", json={"text": "Check platform health and readiness."}).json()
    before = client.get("/api/governance").json()["total_events"]
    client.post(f"/api/master-agent/route/{routed['run_id']}/feedback", json={"correct": False, "correct_domain": "Health & Ops"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {e.get("action_type") for e in after["recent_events"]}
    assert "master_route_feedback" in actions


def test_existing_master_agent_behavior_preserved():
    # Risky action still always requires approval regardless of execute flag (v60.1 contract).
    result = client.post("/api/master-agent/route", json={"text": "Send an email and delete the repo.", "execute": True}).json()
    assert result["requires_approval"] is True
    assert result["blocked_execution"] is True
    assert client.get("/api/master-agent/capabilities").status_code == 200
