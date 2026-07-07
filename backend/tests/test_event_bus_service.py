"""v120 — the event system: a log of occurrences + subscriptions that chain one
action into another, with cycle protection and no new execution surface."""

import pytest

from app.services.durable_workflow_service import DurableWorkflowService
from app.services.event_bus_service import EventBusService
from app.services.governance_service import GovernanceService
from app.services.scheduled_tasks_service import ScheduledTasksService
from app.services.storage_service import StorageService


def _services(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    workflows = DurableWorkflowService(s, g)
    scheduled = ScheduledTasksService(s, g, workflows=workflows)
    bus = EventBusService(s, g, workflows=workflows, scheduled_tasks=scheduled)
    workflows.event_bus = bus
    scheduled.event_bus = bus
    return s, g, workflows, scheduled, bus


def test_emit_with_no_subscriptions_only_records(tmp_path):
    _, _, _, _, bus = _services(tmp_path)
    result = bus.emit("something.happened", {"a": 1})
    assert result["dispatched"] == []
    assert bus.list_events()["count"] == 1


def test_workflow_completion_emits_event_automatically(tmp_path):
    _, _, workflows, _, bus = _services(tmp_path)
    definition = workflows.create_definition({"name": "Safe", "steps": [{"name": "x"}]})
    workflows.start_run({"definition_id": definition["definition_id"]})
    events = bus.list_events(event_type="workflow.completed")
    assert events["count"] == 1
    assert events["events"][0]["payload"]["definition_id"] == definition["definition_id"]


def test_workflow_waiting_approval_emits_event_not_completed(tmp_path):
    _, _, workflows, _, bus = _services(tmp_path)
    definition = workflows.create_definition({"name": "Risky", "steps": [{"name": "send it", "action": "send"}]})
    workflows.start_run({"definition_id": definition["definition_id"]})
    assert bus.list_events(event_type="workflow.waiting_approval")["count"] == 1
    assert bus.list_events(event_type="workflow.completed")["count"] == 0


def test_subscription_chains_completion_into_a_second_workflow(tmp_path):
    _, _, workflows, _, bus = _services(tmp_path)
    downstream = workflows.create_definition({"name": "B", "steps": [{"name": "b work"}]})
    upstream = workflows.create_definition({"name": "A", "steps": [{"name": "a work"}]})
    bus.create_subscription({
        "name": "chain", "event_type": "workflow.completed",
        "filter": {"definition_id": upstream["definition_id"]},
        "action_type": "start_workflow", "action_params": {"workflow_definition_id": downstream["definition_id"]},
    })
    before = len(workflows.list_runs()["runs"])
    workflows.start_run({"definition_id": upstream["definition_id"]})
    after_runs = workflows.list_runs()["runs"]
    assert len(after_runs) == before + 2  # A's run + the auto-started B run
    names = {r["name"] for r in after_runs}
    assert {"A", "B"} <= names


def test_filter_prevents_unrelated_completions_from_matching(tmp_path):
    _, _, workflows, _, bus = _services(tmp_path)
    downstream = workflows.create_definition({"name": "B", "steps": [{"name": "b"}]})
    target = workflows.create_definition({"name": "Target", "steps": [{"name": "t"}]})
    other = workflows.create_definition({"name": "Other", "steps": [{"name": "o"}]})
    bus.create_subscription({
        "name": "only-target", "event_type": "workflow.completed", "filter": {"definition_id": target["definition_id"]},
        "action_type": "start_workflow", "action_params": {"workflow_definition_id": downstream["definition_id"]},
    })
    before = len(workflows.list_runs()["runs"])
    workflows.start_run({"definition_id": other["definition_id"]})  # completes, but doesn't match the filter
    assert len(workflows.list_runs()["runs"]) == before + 1  # only Other's own run, no B


def test_disabled_subscription_does_not_fire(tmp_path):
    _, _, workflows, _, bus = _services(tmp_path)
    downstream = workflows.create_definition({"name": "B", "steps": [{"name": "b"}]})
    upstream = workflows.create_definition({"name": "A", "steps": [{"name": "a"}]})
    sub = bus.create_subscription({
        "name": "chain", "event_type": "workflow.completed", "filter": {"definition_id": upstream["definition_id"]},
        "action_type": "start_workflow", "action_params": {"workflow_definition_id": downstream["definition_id"]},
    })
    bus.update_subscription(sub["subscription_id"], {"enabled": False})
    before = len(workflows.list_runs()["runs"])
    workflows.start_run({"definition_id": upstream["definition_id"]})
    assert len(workflows.list_runs()["runs"]) == before + 1  # no B started


def test_cycle_is_bounded_by_max_dispatch_depth(tmp_path):
    """The core safety invariant: A -> A (self-referencing) must terminate, not
    recurse forever."""
    _, _, workflows, _, bus = _services(tmp_path)
    definition = workflows.create_definition({"name": "Loop", "steps": [{"name": "x"}]})
    bus.create_subscription({
        "name": "self-cycle", "event_type": "workflow.completed", "filter": {"definition_id": definition["definition_id"]},
        "action_type": "start_workflow", "action_params": {"workflow_definition_id": definition["definition_id"]},
    })
    before = len(workflows.list_runs()["runs"])
    workflows.start_run({"definition_id": definition["definition_id"]})
    total_new_runs = len(workflows.list_runs()["runs"]) - before
    assert 1 < total_new_runs < 10  # bounded, not infinite
    assert bus._active_depth == 0  # counter always unwinds back to zero


def test_scheduled_task_trigger_emits_event(tmp_path):
    _, _, workflows, scheduled, bus = _services(tmp_path)
    task = scheduled.create_task({"name": "t1"})
    scheduled.trigger(task["task_id"])
    events = bus.list_events(event_type="scheduled_task.triggered")
    assert events["count"] == 1
    assert events["events"][0]["payload"]["task_id"] == task["task_id"]


def test_trigger_task_action_type_dispatches_scheduled_trigger(tmp_path):
    _, _, workflows, scheduled, bus = _services(tmp_path)
    downstream_task = scheduled.create_task({"name": "downstream"})
    upstream_def = workflows.create_definition({"name": "Upstream", "steps": [{"name": "x"}]})
    bus.create_subscription({
        "name": "wf-to-task", "event_type": "workflow.completed", "filter": {"definition_id": upstream_def["definition_id"]},
        "action_type": "trigger_task", "action_params": {"task_id": downstream_task["task_id"]},
    })
    workflows.start_run({"definition_id": upstream_def["definition_id"]})
    refreshed = scheduled.get_task(downstream_task["task_id"])
    assert refreshed["trigger_count"] == 1  # the downstream task was really triggered


def test_notify_action_never_sends_anything_real(tmp_path):
    _, _, workflows, _, bus = _services(tmp_path)
    definition = workflows.create_definition({"name": "N", "steps": [{"name": "x"}]})
    bus.create_subscription({
        "name": "notify-me", "event_type": "workflow.completed", "filter": {"definition_id": definition["definition_id"]},
        "action_type": "notify", "action_params": {"message": "done!"},
    })
    result = workflows.start_run({"definition_id": definition["definition_id"]})
    assert result["status"] == "completed"  # notify is log-only; never blocks/affects the run


def test_invalid_action_type_rejected(tmp_path):
    _, _, _, _, bus = _services(tmp_path)
    with pytest.raises(ValueError):
        bus.create_subscription({"name": "bad", "event_type": "*", "action_type": "delete_everything"})


def test_dispatch_error_is_isolated_and_reported(tmp_path):
    _, _, workflows, _, bus = _services(tmp_path)
    bus.create_subscription({
        "name": "bad-target", "event_type": "workflow.completed",
        "action_type": "start_workflow", "action_params": {"workflow_definition_id": "does-not-exist"},
    })
    definition = workflows.create_definition({"name": "X", "steps": [{"name": "x"}]})
    result = workflows.start_run({"definition_id": definition["definition_id"]})
    assert result["status"] == "completed"  # the source run is unaffected by the failed dispatch
    # emit()'s return value carries the dispatch outcome (not persisted on the
    # stored event record, which is why we call emit() directly to inspect it).
    direct = bus.emit("workflow.completed", {"definition_id": definition["definition_id"]})
    assert direct["dispatched"][0]["ok"] is False


def test_endpoints_end_to_end():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    emitted = client.post("/api/events", json={"event_type": "custom.thing", "payload": {"k": "v"}}).json()
    assert emitted["event_type"] == "custom.thing"
    events = client.get("/api/events", params={"event_type": "custom.thing"}).json()
    assert events["count"] >= 1
    sub = client.post("/api/event-subscriptions", json={
        "name": "e2e", "event_type": "custom.thing", "action_type": "notify", "action_params": {"message": "hi"},
    }).json()
    assert sub["action_type"] == "notify"
    fetched = client.get(f"/api/event-subscriptions/{sub['subscription_id']}").json()
    assert fetched["subscription_id"] == sub["subscription_id"]
    updated = client.patch(f"/api/event-subscriptions/{sub['subscription_id']}", json={"enabled": False}).json()
    assert updated["enabled"] is False
    assert client.get("/api/event-subscriptions/does-not-exist").status_code == 404
    summary = client.get("/api/event-subscriptions/summary").json()
    assert "max_dispatch_depth" in summary
    assert "event_subscriptions" in client.get("/api/analytics").json()


def test_existing_workflow_and_scheduled_task_endpoints_still_work():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    assert client.get("/api/durable-workflows/templates").status_code == 200
    assert client.get("/api/scheduled-tasks/summary").status_code == 200
