from fastapi.testclient import TestClient

from app.main import app
from app.services.governance_service import GovernanceService
from app.services.scheduled_tasks_service import ScheduledTasksService
from app.services.storage_service import StorageService

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


# ------------------------------------------------------------------
# Round 29: set_enabled()/trigger() had the same lost-update shape rounds
# 25-28 fixed elsewhere. Independently confirmed against the true pre-fix
# code (patching read_list to widen the window) that a concurrent
# set_enabled(B, disabled) landing during trigger(A)'s wide window
# (which may start a real durable workflow) got silently reverted -- a task
# the user just disabled would fire again anyway. Background scheduler
# ticks + foreground trigger/patch requests are the real concurrent writers.
# ------------------------------------------------------------------
def test_trigger_does_not_lose_a_concurrent_set_enabled(tmp_path):
    import threading
    import time

    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    service = ScheduledTasksService(storage, governance)
    a = service.create_task({"name": "A", "schedule": "manual", "action_type": "note"})
    b = service.create_task({"name": "B", "schedule": "manual", "action_type": "note"})

    entered = threading.Event()
    original_update_list = storage.update_list

    def _slow_update_list(filename, mutator):
        def _slow_mutator(items):
            entered.set()
            time.sleep(0.2)
            return mutator(items)
        return original_update_list(filename, _slow_mutator)

    storage.update_list = _slow_update_list

    def _trigger_a():
        service.trigger(a["task_id"])

    t = threading.Thread(target=_trigger_a)
    t.start()
    entered.wait(timeout=2)
    service.set_enabled(b["task_id"], False)  # concurrent disable of a DIFFERENT task
    t.join(timeout=2)

    assert service.get_task(b["task_id"])["enabled"] is False  # must not be lost -- failed before the fix
    assert service.get_task(a["task_id"])["trigger_count"] == 1  # trigger's own count must also survive


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/workspace-templates/summary").status_code == 200
    assert client.get("/api/operating-layer-2/dashboard").status_code == 200
