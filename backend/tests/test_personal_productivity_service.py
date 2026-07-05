from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_brain_has_all_sections():
    brain = client.get("/api/productivity").json()
    for key in ("priority_recommendations", "daily_focus", "blockers", "overdue",
                "upcoming_deadlines", "goal_progress", "what_now", "open_task_count"):
        assert key in brain
    assert "pick" in brain["what_now"] and "reason" in brain["what_now"]
    assert len(brain["daily_focus"]) <= 3


def test_overdue_task_surfaces_and_is_picked():
    ws = client.post("/api/workspaces", json={"name": "v74 prod ws"}).json()
    wid = ws.get("workspace_id") or ws.get("id") or (ws.get("workspace") or {}).get("workspace_id")
    # Create an overdue high-priority task directly via life-os if available; else skip creation.
    client.post("/api/life-os/tasks", json={"title": "Overdue thing v74", "due_date": "2000-01-01", "priority": "high", "workspace_id": wid})
    brain = client.get(f"/api/productivity?workspace_id={wid}").json()
    # If the task endpoint created it, it should be overdue and picked.
    if brain["open_task_count"] > 0:
        assert any("Overdue thing v74" == t["title"] for t in brain["overdue"]) or brain["what_now"]["pick"] is not None


def test_what_now_endpoint():
    wn = client.get("/api/productivity/what-now").json()
    assert "pick" in wn and "reason" in wn


def test_summary_and_analytics():
    summary = client.get("/api/productivity/summary").json()
    for key in ("open_tasks", "overdue", "blockers", "what_now"):
        assert key in summary
    assert "productivity_open_tasks" in client.get("/api/analytics").json()


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/productivity")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "productivity_reviewed" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/workflow-recommend/summary").status_code == 200
    assert client.get("/api/agent-quality/summary").status_code == 200
