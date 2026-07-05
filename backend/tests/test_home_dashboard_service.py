from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_today_shape():
    d = client.get("/api/today/summary").json()
    assert "generated_at" in d
    assert isinstance(d["metrics"], dict)
    assert "agents" in d["metrics"] and "workflow_runs" in d["metrics"]
    assert isinstance(d["recent_activity"], list)
    assert isinstance(d["highlights"], list) and d["highlights"]
    assert isinstance(d["quick_actions"], list)


def test_today_reflects_activity():
    client.post("/api/agent-studio/agents", json={"name": "Dash Agent", "role": "x"})
    d = client.get("/api/today/summary").json()
    assert d["metrics"]["agents"] >= 1
    # recent activity items are sanitized to a compact shape
    if d["recent_activity"]:
        ev = d["recent_activity"][0]
        assert set(ev.keys()) == {"action_type", "agent", "reason", "risk_score"}


def test_existing_endpoints_still_work():
    assert client.get("/api/adaptive-learning/status").status_code == 200
    assert client.get("/api/analytics").status_code == 200
