"""v120 — real triggers: scheduled tasks -> durable workflow runs, and the
opt-in background tick worker."""

import pytest

from app.services.durable_workflow_service import DurableWorkflowService
from app.services.governance_service import GovernanceService
from app.services.scheduled_tasks_service import ScheduledTasksService
from app.services.scheduler_tick_worker import SchedulerTickWorker
from app.services.storage_service import StorageService


def _services(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    workflows = DurableWorkflowService(s, g)
    scheduled = ScheduledTasksService(s, g, workflows=workflows)
    return s, g, workflows, scheduled


def test_task_without_linked_workflow_behaves_as_before(tmp_path):
    _, _, _, scheduled = _services(tmp_path)
    task = scheduled.create_task({"name": "plain", "action_type": "plan"})
    run = scheduled.trigger(task["task_id"])
    assert run["status"] == "planned"
    assert run["executed"] is False
    assert run["workflow_run_id"] is None  # unchanged, backward-compatible shape


def test_linked_workflow_with_only_safe_steps_completes_for_real(tmp_path):
    _, _, workflows, scheduled = _services(tmp_path)
    definition = workflows.create_definition({"name": "Greet", "steps": [{"name": "say hi"}]})
    task = scheduled.create_task({"name": "greeter", "workflow_definition_id": definition["definition_id"]})
    run = scheduled.trigger(task["task_id"])
    assert run["status"] == "completed"
    assert run["executed"] is True
    assert run["workflow_run_id"]
    wf_run = workflows.get_run(run["workflow_run_id"])
    assert wf_run["status"] == "completed"
    assert wf_run["steps"][0]["status"] == "done"


def test_linked_workflow_with_risky_step_halts_for_approval_not_auto_run(tmp_path):
    """The core safety invariant: firing a schedule must NEVER bypass approval."""
    _, _, workflows, scheduled = _services(tmp_path)
    definition = workflows.create_definition({
        "name": "Risky", "steps": [{"name": "send the email", "action": "send"}],
    })
    task = scheduled.create_task({"name": "risky-task", "workflow_definition_id": definition["definition_id"]})
    run = scheduled.trigger(task["task_id"])
    assert run["status"] == "waiting_approval"
    assert run["executed"] is False
    wf_run = workflows.get_run(run["workflow_run_id"])
    assert wf_run["status"] == "waiting_approval"
    assert wf_run["steps"][0]["status"] == "waiting_approval"  # NOT auto-approved


def test_missing_workflow_definition_fails_gracefully(tmp_path):
    _, _, _, scheduled = _services(tmp_path)
    task = scheduled.create_task({"name": "broken-link", "workflow_definition_id": "does-not-exist"})
    run = scheduled.trigger(task["task_id"])
    assert run["status"] == "failed"
    assert run["workflow_run_id"] is None
    # the task itself is not corrupted; can still be listed/disabled normally
    assert scheduled.get_task(task["task_id"]) is not None


def test_tick_worker_start_is_noop_when_disabled(tmp_path, monkeypatch):
    import app.services.scheduler_tick_worker as mod
    monkeypatch.setattr(mod.settings, "scheduler_tick_enabled", False)
    _, _, _, scheduled = _services(tmp_path)
    worker = SchedulerTickWorker(scheduled)
    import asyncio
    asyncio.run(worker.start())
    assert worker.running is False
    assert worker._task is None


def test_tick_once_fires_only_due_enabled_tasks(tmp_path):
    _, _, workflows, scheduled = _services(tmp_path)
    due_task = scheduled.create_task({"name": "due", "schedule": "hourly"})
    manual_task = scheduled.create_task({"name": "manual-only", "schedule": "manual"})
    disabled_task = scheduled.create_task({"name": "off", "schedule": "hourly"})
    scheduled.set_enabled(disabled_task["task_id"], False)

    worker = SchedulerTickWorker(scheduled)
    fired = worker.tick_once()
    fired_ids = {f["task_id"] for f in fired}
    assert due_task["task_id"] in fired_ids       # hourly, never triggered -> due
    assert manual_task["task_id"] not in fired_ids  # manual is never "due"
    assert disabled_task["task_id"] not in fired_ids  # disabled is never "due"


def test_tick_once_isolates_one_bad_task_from_the_rest(tmp_path, monkeypatch):
    _, _, workflows, scheduled = _services(tmp_path)
    a = scheduled.create_task({"name": "a", "schedule": "hourly"})
    b = scheduled.create_task({"name": "b", "schedule": "hourly"})

    real_trigger = scheduled.trigger

    def flaky_trigger(task_id):
        if task_id == a["task_id"]:
            raise RuntimeError("boom")
        return real_trigger(task_id)

    monkeypatch.setattr(scheduled, "trigger", flaky_trigger)
    worker = SchedulerTickWorker(scheduled)
    fired = worker.tick_once()
    by_id = {f["task_id"]: f for f in fired}
    assert by_id[a["task_id"]]["status"] == "error"
    assert by_id[b["task_id"]]["status"] in ("planned", "noted", "approval_required")  # b still ran fine


def test_tick_once_is_not_gated_by_enabled_flag_itself(tmp_path, monkeypatch):
    """Manual/direct calls to tick_once() are an explicit action and must work
    even when the autonomous loop is disabled -- only start()/the loop are gated."""
    import app.services.scheduler_tick_worker as mod
    monkeypatch.setattr(mod.settings, "scheduler_tick_enabled", False)
    _, _, _, scheduled = _services(tmp_path)
    scheduled.create_task({"name": "due-now", "schedule": "hourly"})
    worker = SchedulerTickWorker(scheduled)
    fired = worker.tick_once()
    assert len(fired) == 1  # fired despite the flag being off


def test_status_reports_shape(tmp_path):
    _, _, _, scheduled = _services(tmp_path)
    worker = SchedulerTickWorker(scheduled)
    status = worker.status()
    assert set(["enabled", "running", "interval_seconds", "last_tick_at", "last_error", "last_fired"]) <= set(status)


def test_endpoints_end_to_end():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    d = client.post("/api/durable-workflows/definitions", json={"name": "e2e", "steps": [{"name": "x"}]}).json()
    t = client.post("/api/scheduled-tasks", json={"name": "e2e-task", "workflow_definition_id": d["definition_id"]}).json()
    assert t["workflow_definition_id"] == d["definition_id"]
    run = client.post(f"/api/scheduled-tasks/{t['task_id']}/trigger").json()
    assert run["status"] == "completed" and run["workflow_run_id"]
    status = client.get("/api/scheduled-tasks/tick-status").json()
    assert "enabled" in status and status["enabled"] is False  # off by default
    tick = client.post("/api/scheduled-tasks/tick-now").json()
    assert "fired" in tick and "count" in tick


def test_existing_endpoints_still_work():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    assert client.get("/api/scheduled-tasks/summary").status_code == 200
    assert client.get("/api/durable-workflows/templates").status_code == 200
