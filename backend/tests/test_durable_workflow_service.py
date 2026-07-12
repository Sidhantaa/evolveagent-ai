from fastapi.testclient import TestClient

from app.main import app
from app.services.durable_workflow_service import DurableWorkflowService
from app.services.eval_harness_service import EvalHarnessService
from app.services.governance_service import GovernanceService
from app.services.safe_command_runner import SafeCommandRunner
from app.services.self_healing_service import SelfHealingService
from app.services.storage_service import StorageService

client = TestClient(app)


class _StubTestQuality:
    """A controlled stand-in for TestQualityService -- real pytest/npm-build runs
    take up to 60s+ each and would recursively invoke this very test suite, so
    engine-level wiring tests use a fast, deterministic stub instead."""

    def __init__(self, blocked: bool, command_results: list[dict] | None = None):
        self.blocked = blocked
        self.command_results = command_results or []
        self.calls: list[dict] = []

    def run_quality_checks(self, commands=None, issue_id=None):
        self.calls.append({"commands": commands, "issue_id": issue_id})
        if self.blocked:
            return {"quality_gate": {"passed": False, "blocked": True, "reason": "1 command(s) failed."},
                    "command_results": self.command_results}
        return {"quality_gate": {"passed": True, "blocked": False, "reason": "All commands passed."},
                "command_results": self.command_results}


def _isolated_workflow_service(tmp_path, test_quality=None, self_healing=None, eval_harness=None) -> DurableWorkflowService:
    storage = StorageService(data_dir=str(tmp_path / "data"))
    return DurableWorkflowService(storage, GovernanceService(storage), test_quality=test_quality, self_healing=self_healing, eval_harness=eval_harness)


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


# ------------------------------------------------------------------
# Self-healing: a genuinely blocked quality gate turns the first failing
# command's real output into a structured finding + drafted repair task via
# SelfHealingService's own failure parser (previously an orphaned service with
# no caller besides its own routes/tests) instead of just a text reason.
# ------------------------------------------------------------------
def test_blocked_quality_gate_drafts_a_self_healing_repair_task(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    self_healing = SelfHealingService(storage, governance, SafeCommandRunner())
    stub = _StubTestQuality(blocked=True, command_results=[
        {"command": "pytest", "exit_code": 1, "stdout": "", "stderr": "1 failed, AssertionError", "success": False},
    ])
    service = DurableWorkflowService(storage, governance, test_quality=stub, self_healing=self_healing)
    run = service.start_run({"steps": [{"name": "verify", "action_type": "run_quality_checks"}]})
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "failed"
    assert "repair drafted" in done["steps"][0]["output"]
    repairs = self_healing.list_repairs()
    assert len(repairs) == 1
    assert repairs[0]["status"] == "draft"
    assert repairs[0]["requires_approval"] is True
    assert repairs[0]["auto_apply"] is False  # never auto-applied, human must act on the draft
    findings = self_healing.list_findings()
    assert findings[0]["status"] == "repair_drafted"


def test_blocked_quality_gate_without_self_healing_collaborator_unchanged(tmp_path):
    stub = _StubTestQuality(blocked=True, command_results=[
        {"command": "pytest", "exit_code": 1, "stdout": "", "stderr": "failed", "success": False},
    ])
    service = _isolated_workflow_service(tmp_path, test_quality=stub, self_healing=None)
    run = service.start_run({"steps": [{"name": "verify", "action_type": "run_quality_checks"}]})
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "failed"
    assert "repair drafted" not in done["steps"][0]["output"]


def test_blocked_quality_gate_with_no_failing_command_skips_repair(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    self_healing = SelfHealingService(storage, governance, SafeCommandRunner())
    stub = _StubTestQuality(blocked=True)  # blocked but no command_results at all
    service = DurableWorkflowService(storage, governance, test_quality=stub, self_healing=self_healing)
    run = service.start_run({"steps": [{"name": "verify", "action_type": "run_quality_checks"}]})
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "failed"
    assert "repair drafted" not in done["steps"][0]["output"]
    assert self_healing.list_repairs() == []


def test_passing_quality_gate_never_drafts_a_repair(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    self_healing = SelfHealingService(storage, governance, SafeCommandRunner())
    stub = _StubTestQuality(blocked=False)
    service = DurableWorkflowService(storage, governance, test_quality=stub, self_healing=self_healing)
    run = service.start_run({"steps": [{"name": "verify", "action_type": "run_quality_checks"}]})
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "completed"
    assert self_healing.list_repairs() == []


# ------------------------------------------------------------------
# v250 Self-Evaluating System: run_eval_suite wires EvalHarnessService's real
# deterministic regression check (previously an orphaned service, reachable
# only via its own routes) into the workflow engine, mirroring run_quality_checks.
# ------------------------------------------------------------------
def test_run_eval_suite_executes_and_records_a_run(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    eval_harness = EvalHarnessService(storage, governance)
    suite = eval_harness.create_suite({
        "name": "Basic suite",
        "cases": [{"prompt": "p", "reference_answer": "apple banana", "expected_keywords": ["apple", "banana"]}],
    })
    service = DurableWorkflowService(storage, governance, eval_harness=eval_harness)
    run = service.start_run({"steps": [{
        "name": "evaluate", "action_type": "run_eval_suite",
        "action_params": {"suite_id": suite["suite_id"]},
    }]})
    assert run["steps"][0]["requires_approval"] is True
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "completed"
    assert "[executed] run_eval_suite" in done["steps"][0]["output"]
    assert len(eval_harness.list_runs(suite["suite_id"])) == 1


def test_run_eval_suite_regression_fails_the_run(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    eval_harness = EvalHarnessService(storage, governance)
    suite = eval_harness.create_suite({
        "name": "Regressing suite",
        "cases": [{"prompt": "p", "reference_answer": "apple banana", "expected_keywords": ["apple", "banana"]}],
    })
    suite_id = suite["suite_id"]
    eval_harness.run_suite(suite_id)  # baseline run, score 1.0

    # Mutate the suite's own reference answer so the next run scores lower --
    # a genuine regression signal, not a stub.
    suites = storage.read_list(eval_harness.suites_file)
    for s in suites:
        if s.get("suite_id") == suite_id:
            s["cases"][0]["reference_answer"] = "nothing matches"
    storage.write_list(eval_harness.suites_file, suites)

    service = DurableWorkflowService(storage, governance, eval_harness=eval_harness)
    run = service.start_run({"steps": [{
        "name": "evaluate", "action_type": "run_eval_suite",
        "action_params": {"suite_id": suite_id},
    }]})
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "failed"
    assert done["steps"][0]["status"] == "blocked"
    assert "[blocked] run_eval_suite" in done["steps"][0]["output"]
    assert "regressed" in done["steps"][0]["output"]


def test_run_eval_suite_without_collaborator_declines_safely(tmp_path):
    service = _isolated_workflow_service(tmp_path, eval_harness=None)
    run = service.start_run({"steps": [{
        "name": "evaluate", "action_type": "run_eval_suite",
        "action_params": {"suite_id": "does-not-matter"},
    }]})
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "completed"  # missing collaborator declines, never fails the run
    assert "[declined] run_eval_suite" in done["steps"][0]["output"]


def test_run_eval_suite_missing_suite_id_declines_safely(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    eval_harness = EvalHarnessService(storage, governance)
    service = DurableWorkflowService(storage, governance, eval_harness=eval_harness)
    run = service.start_run({"steps": [{"name": "evaluate", "action_type": "run_eval_suite"}]})
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "completed"
    assert "[declined] run_eval_suite" in done["steps"][0]["output"]


def test_run_eval_suite_unknown_suite_declines_safely(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    eval_harness = EvalHarnessService(storage, governance)
    service = DurableWorkflowService(storage, governance, eval_harness=eval_harness)
    run = service.start_run({"steps": [{
        "name": "evaluate", "action_type": "run_eval_suite",
        "action_params": {"suite_id": "nonexistent-suite-id"},
    }]})
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "completed"
    assert "[declined] run_eval_suite" in done["steps"][0]["output"]
