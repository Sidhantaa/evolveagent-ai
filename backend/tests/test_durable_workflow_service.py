from fastapi.testclient import TestClient

from app.main import app
from app.services.durable_workflow_service import DurableWorkflowService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

client = TestClient(app)


class _StubTestQuality:
    """A controlled stand-in for TestQualityService -- real pytest/npm-build runs
    take up to 60s+ each and would recursively invoke this very test suite, so
    engine-level wiring tests use a fast, deterministic stub instead."""

    def __init__(self, blocked: bool):
        self.blocked = blocked
        self.calls: list[dict] = []

    def run_quality_checks(self, commands=None, issue_id=None):
        self.calls.append({"commands": commands, "issue_id": issue_id})
        if self.blocked:
            return {"quality_gate": {"passed": False, "blocked": True, "reason": "1 command(s) failed."}}
        return {"quality_gate": {"passed": True, "blocked": False, "reason": "All commands passed."}}


def _isolated_workflow_service(tmp_path, test_quality=None) -> DurableWorkflowService:
    storage = StorageService(data_dir=str(tmp_path / "data"))
    return DurableWorkflowService(storage, GovernanceService(storage), test_quality=test_quality)


def test_templates():
    t = client.get("/api/durable-workflows/templates").json()
    assert t["count"] >= 3
    assert "weekly_report" in {x["key"] for x in t["templates"]}


def test_action_step_is_gated_and_executes_real_effect():
    run = client.post("/api/durable-workflows/runs", json={"steps": [
        {"name": "prep"},
        {"name": "make task", "action_type": "create_task", "action_params": {"title": "Ship it"}},
    ]}).json()
    # the action step must halt for approval (never auto-run)
    assert run["status"] == "waiting_approval"
    assert run["steps"][1]["requires_approval"] is True
    assert run["steps"][1]["action_type"] == "create_task"
    done = client.post(f"/api/durable-workflows/runs/{run['run_id']}/approve", json={"approved": True}).json()
    assert done["status"] == "completed"
    assert "[executed] create_task" in done["steps"][1]["output"]
    # a real effect record now exists for this run
    eff = client.get("/api/durable-workflows/effects", params={"run_id": run["run_id"]}).json()
    assert eff["count"] == 1
    assert eff["effects"][0]["action_type"] == "create_task"
    assert eff["effects"][0]["params"]["title"] == "Ship it"


def test_rejecting_action_step_creates_no_effect():
    run = client.post("/api/durable-workflows/runs", json={"steps": [
        {"name": "notify me", "action_type": "notify", "action_params": {"message": "hi"}},
    ]}).json()
    rid = run["run_id"]
    res = client.post(f"/api/durable-workflows/runs/{rid}/approve", json={"approved": False}).json()
    assert res["steps"][0]["status"] == "skipped"
    assert client.get("/api/durable-workflows/effects", params={"run_id": rid}).json()["count"] == 0


def test_non_whitelisted_action_type_is_not_executed():
    # An unknown action_type must NOT become a real effect; it stays a normal step.
    run = client.post("/api/durable-workflows/runs", json={"steps": [
        {"name": "wipe disk", "action_type": "delete_everything"},
    ]}).json()
    assert run["steps"][0]["action_type"] == ""  # stripped — not whitelisted
    assert run["status"] == "completed"  # ran as a plain simulated step
    assert client.get("/api/durable-workflows/effects", params={"run_id": run["run_id"]}).json()["count"] == 0


def test_daily_capture_template_halts_at_action():
    d = client.post("/api/durable-workflows/definitions", json={"template": "daily_capture"}).json()
    run = client.post("/api/durable-workflows/runs", json={"definition_id": d["definition_id"]}).json()
    assert run["status"] == "waiting_approval"  # stops at the create_task step


def test_run_halts_at_approval_gate():
    # Weekly report ends with a "send" step -> should halt for approval.
    run = client.post("/api/durable-workflows/runs", json={"template": None, "steps": [
        {"name": "Collect activity"},
        {"name": "Draft report"},
        {"name": "Send to stakeholders", "action": "send"},
    ]}).json()
    assert run["status"] == "waiting_approval"
    assert run["steps"][0]["status"] == "done"
    assert run["steps"][1]["status"] == "done"
    assert run["steps"][2]["status"] == "waiting_approval"
    assert run["steps"][2]["requires_approval"] is True


def test_approval_continues_and_completes():
    run = client.post("/api/durable-workflows/runs", json={"steps": [
        {"name": "Prepare"},
        {"name": "Send email", "action": "send"},
    ]}).json()
    assert run["status"] == "waiting_approval"
    done = client.post(f"/api/durable-workflows/runs/{run['run_id']}/approve", json={"approved": True}).json()
    assert done["status"] == "completed"
    assert done["steps"][1]["status"] == "done"


def test_rejection_skips_step():
    run = client.post("/api/durable-workflows/runs", json={"steps": [
        {"name": "Deploy to prod", "action": "deploy"},
        {"name": "Log result"},
    ]}).json()
    assert run["status"] == "waiting_approval"
    res = client.post(f"/api/durable-workflows/runs/{run['run_id']}/approve", json={"approved": False, "note": "not ready"}).json()
    assert res["steps"][0]["status"] == "skipped"
    assert res["status"] == "completed"


def test_all_safe_steps_complete_immediately():
    run = client.post("/api/durable-workflows/runs", json={"steps": [
        {"name": "Gather"}, {"name": "Summarize"}, {"name": "Write"},
    ]}).json()
    assert run["status"] == "completed"
    assert all(s["status"] == "done" for s in run["steps"])


def test_durable_checkpoint_and_resume():
    run = client.post("/api/durable-workflows/runs", json={"steps": [{"name": "Step A"}, {"name": "Send", "action": "send"}]}).json()
    rid = run["run_id"]
    # checkpoints recorded (durability)
    assert len(run.get("checkpoints", [])) >= 1
    paused = client.post(f"/api/durable-workflows/runs/{rid}/pause").json()
    assert paused["status"] == "paused"
    # fetching a fresh copy proves state persisted
    fetched = client.get(f"/api/durable-workflows/runs/{rid}").json()
    assert fetched["status"] == "paused" and fetched["cursor"] == 1
    resumed = client.post(f"/api/durable-workflows/runs/{rid}/resume").json()
    assert resumed["status"] == "waiting_approval"  # resumes and hits the send gate


def test_definition_from_template_then_start():
    d = client.post("/api/durable-workflows/definitions", json={"template": "research_brief"}).json()
    assert d["definition_id"] and len(d["steps"]) >= 2
    run = client.post("/api/durable-workflows/runs", json={"definition_id": d["definition_id"]}).json()
    assert run["status"] == "completed"  # research_brief has no risky steps


def test_cancel_run():
    run = client.post("/api/durable-workflows/runs", json={"steps": [{"name": "X"}, {"name": "Pay invoice", "action": "pay"}]}).json()
    cancelled = client.post(f"/api/durable-workflows/runs/{run['run_id']}/cancel").json()
    assert cancelled["status"] == "cancelled"


def test_empty_run_rejected():
    assert client.post("/api/durable-workflows/runs", json={"steps": []}).status_code == 400


def test_summary_analytics_governance():
    client.post("/api/durable-workflows/runs", json={"steps": [{"name": "note"}]})
    assert "durable_workflow_runs" in client.get("/api/durable-workflows/summary").json()
    assert "durable_workflow_runs" in client.get("/api/analytics").json()
    actions = {e.get("action_type") for e in client.get("/api/governance").json()["recent_events"]}
    assert "workflow_started" in actions or "workflow_completed" in actions


def test_existing_endpoints_still_work():
    assert client.get("/api/voice-console/status").status_code == 200
    assert client.get("/api/agent-studio/summary").status_code == 200


# ------------------------------------------------------------------
# Verification layer: run_quality_checks wires TestQualityService (real pytest/
# npm-build execution, previously an orphaned service with no caller) into the
# workflow engine as a genuine pre-approval gate. A real block now fails the
# run for the first time this engine's dead "failed" terminal status is reached.
# ------------------------------------------------------------------
def test_run_quality_checks_gated_and_passes(tmp_path):
    stub = _StubTestQuality(blocked=False)
    service = _isolated_workflow_service(tmp_path, test_quality=stub)
    run = service.start_run({"steps": [{"name": "verify", "action_type": "run_quality_checks"}]})
    assert run["status"] == "waiting_approval"
    assert run["steps"][0]["requires_approval"] is True
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "completed"
    assert "[executed] run_quality_checks" in done["steps"][0]["output"]
    assert stub.calls  # the real (stubbed) check was actually invoked


def test_run_quality_checks_blocked_fails_the_run(tmp_path):
    stub = _StubTestQuality(blocked=True)
    service = _isolated_workflow_service(tmp_path, test_quality=stub)
    run = service.start_run({"steps": [{"name": "verify", "action_type": "run_quality_checks"}]})
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "failed"
    assert done["steps"][0]["status"] == "blocked"
    assert "[blocked] run_quality_checks" in done["steps"][0]["output"]


def test_run_quality_checks_without_collaborator_declines_safely(tmp_path):
    service = _isolated_workflow_service(tmp_path, test_quality=None)
    run = service.start_run({"steps": [{"name": "verify", "action_type": "run_quality_checks"}]})
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "completed"  # missing collaborator declines, never fails the run
    assert "[declined] run_quality_checks" in done["steps"][0]["output"]


def test_failed_run_is_terminal(tmp_path):
    stub = _StubTestQuality(blocked=True)
    service = _isolated_workflow_service(tmp_path, test_quality=stub)
    run = service.start_run({"steps": [{"name": "verify", "action_type": "run_quality_checks"}]})
    done = service.approve_step(run["run_id"], approved=True)
    again = service.advance_run(done["run_id"])
    assert again["status"] == "failed"


def test_quality_check_commands_can_be_overridden_via_action_params(tmp_path):
    stub = _StubTestQuality(blocked=False)
    service = _isolated_workflow_service(tmp_path, test_quality=stub)
    run = service.start_run({"steps": [{
        "name": "verify", "action_type": "run_quality_checks",
        "action_params": {"commands": '["pytest"]'},
    }]})
    service.approve_step(run["run_id"], approved=True)
    assert stub.calls[0]["commands"] == ["pytest"]
