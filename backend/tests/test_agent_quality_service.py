from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_has_sections():
    dash = client.get("/api/agent-quality/dashboard").json()
    for key in ("score_trends", "weak_agents", "regressions", "best_by_task", "feedback_correlation", "agents_tracked"):
        assert key in dash
    for trend in dash["score_trends"]:
        for key in ("agent", "runs", "avg_score", "recent_avg", "trend"):
            assert key in trend
        assert 0 <= trend["avg_score"] <= 100


def test_best_by_task_structure():
    data = client.get("/api/agent-quality/best-by-task").json()
    assert "best_by_task" in data
    for row in data["best_by_task"]:
        for key in ("task_type", "best_agent", "avg_score"):
            assert key in row


def test_feedback_correlation_shape():
    dash = client.get("/api/agent-quality/dashboard").json()
    corr = dash["feedback_correlation"]
    for key in ("positive_feedback", "negative_feedback", "aligned"):
        assert key in corr


def test_summary_and_analytics():
    summary = client.get("/api/agent-quality/summary").json()
    for key in ("agents_tracked", "weak_agent_count", "regression_count"):
        assert key in summary
    assert "agent_quality_agents_tracked" in client.get("/api/analytics").json()


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/agent-quality/summary")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "agent_quality_analyzed" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/context/summary").status_code == 200
    assert client.get("/api/workspace-os/summary").status_code == 200
