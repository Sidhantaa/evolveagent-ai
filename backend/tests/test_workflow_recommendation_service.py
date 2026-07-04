from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_recommend_coding_workflow():
    r = client.post("/api/workflow-recommend", json={"goal": "Refactor the python api and add tests"}).json()
    assert r["task_type"] == "coding"
    assert r["expected_step_count"] >= 3
    assert isinstance(r["recommended_workflow"], list)
    assert "estimated_minutes" in r and "complexity" in r


def test_risky_goal_requires_approval():
    r = client.post("/api/workflow-recommend", json={"goal": "Send the invoice email and deploy to prod"}).json()
    assert r["requires_approval"] is True
    assert r["risk_level"] == "high"
    assert r["approval_reason"]


def test_explicit_task_type_honored():
    r = client.post("/api/workflow-recommend", json={"goal": "anything", "task_type": "research"}).json()
    assert r["task_type"] == "research"


def test_similar_runs_included():
    client.post("/api/master-agent/route", json={"text": "Analyze the sales dataset and report trends"})
    r = client.post("/api/workflow-recommend", json={"goal": "Analyze the sales dataset"}).json()
    assert isinstance(r["similar_past_runs"], list)


def test_summary_and_analytics():
    summary = client.get("/api/workflow-recommend/summary").json()
    assert "task_types" in summary and summary["template_count"] >= 4
    assert "workflow_templates" in client.get("/api/analytics").json()


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/workflow-recommend", json={"goal": "plan something"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "workflow_recommended" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/agent-quality/summary").status_code == 200
    assert client.get("/api/context/summary").status_code == 200
