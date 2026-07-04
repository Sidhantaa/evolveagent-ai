from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_task(**overrides) -> dict:
    payload = {
        "name": overrides.get("name", "Daily digest"),
        "schedule": overrides.get("schedule", "daily"),
        "action_type": overrides.get("action_type", "plan"),
        "detail": overrides.get("detail", "Summarize the day."),
    }
    response = client.post("/api/scheduled-tasks", json=payload)
    assert response.status_code == 200
    return response.json()


def test_create_and_list_task():
    task = _create_task()
    assert task["task_id"]
    assert task["schedule"] == "daily"
    listed = client.get("/api/scheduled-tasks").json()
    assert any(t["task_id"] == task["task_id"] for t in listed["tasks"])


def test_trigger_is_planning_first():
    task = _create_task(action_type="plan")
    run = client.post(f"/api/scheduled-tasks/{task['task_id']}/trigger").json()
    assert run["run_id"]
    assert run["executed"] is False
    assert run["status"] == "planned"
    assert "no real action" in run["note"].lower()
    assert client.post("/api/scheduled-tasks/missing/trigger").status_code in (404, 409)


def test_trigger_risky_holds_for_approval():
    task = _create_task(action_type="approval_required")
    run = client.post(f"/api/scheduled-tasks/{task['task_id']}/trigger").json()
    assert run["status"] == "approval_required"
    assert run["executed"] is False


def test_disable_blocks_trigger():
    task = _create_task()
    client.patch(f"/api/scheduled-tasks/{task['task_id']}", json={"enabled": False})
    resp = client.post(f"/api/scheduled-tasks/{task['task_id']}/trigger")
    assert resp.status_code == 409


def test_trigger_increments_count():
    task = _create_task()
    client.post(f"/api/scheduled-tasks/{task['task_id']}/trigger")
    fetched = next(t for t in client.get("/api/scheduled-tasks").json()["tasks"] if t["task_id"] == task["task_id"])
    assert fetched["trigger_count"] >= 1
    assert fetched["last_triggered_at"] is not None


def test_due_is_informational():
    # A never-triggered daily task is "due"; a manual one never is.
    daily = _create_task(name="due one", schedule="daily")
    _create_task(name="manual one", schedule="manual")
    summary = client.get("/api/scheduled-tasks/summary").json()
    assert "due_count" in summary
    assert "no real background" in summary["note"].lower()


def test_runs_listed_and_filtered():
    task = _create_task()
    client.post(f"/api/scheduled-tasks/{task['task_id']}/trigger")
    runs = client.get(f"/api/scheduled-tasks/runs?task_id={task['task_id']}").json()
    assert all(r["task_id"] == task["task_id"] for r in runs["runs"])
    assert runs["count"] >= 1


def test_analytics_includes_scheduled_fields():
    analytics = client.get("/api/analytics").json()
    for key in ("scheduled_tasks", "scheduled_task_runs", "scheduled_tasks_due"):
        assert key in analytics


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    task = _create_task()
    client.post(f"/api/scheduled-tasks/{task['task_id']}/trigger")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "scheduled_task_created" in actions or "scheduled_task_triggered" in actions


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/workspace-templates/summary").status_code == 200
    assert client.get("/api/operating-layer-2/dashboard").status_code == 200
