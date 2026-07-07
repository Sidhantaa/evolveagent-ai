"""v120 task 3 — job-queue observability: every real durable-workflow run becomes
an observable AgentSchedulerService job, reflecting the run's actual status."""

from app.services.agent_scheduler_service import AgentSchedulerService
from app.services.durable_workflow_service import DurableWorkflowService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService
from app.services.workspace_service import WorkspaceService


def _services(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    ws = WorkspaceService(s)
    scheduler = AgentSchedulerService(s, g, ws)
    workflows = DurableWorkflowService(s, g, agent_scheduler=scheduler)
    return s, g, workflows, scheduler


def test_starting_a_run_creates_a_real_job(tmp_path):
    _, _, workflows, scheduler = _services(tmp_path)
    definition = workflows.create_definition({"name": "Safe", "steps": [{"name": "x"}]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run.get("job_id")
    job = scheduler.get_job(run["job_id"])
    assert job is not None
    assert job["job_type"] == "workflow"
    assert job["payload"]["run_id"] == run["run_id"]
    assert job["payload"]["definition_id"] == definition["definition_id"]


def test_completed_run_completes_its_job(tmp_path):
    _, _, workflows, scheduler = _services(tmp_path)
    definition = workflows.create_definition({"name": "Safe", "steps": [{"name": "x"}]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run["status"] == "completed"
    job = scheduler.get_job(run["job_id"])
    assert job["status"] == "completed"


def test_risky_run_pauses_its_job_until_approved(tmp_path):
    _, _, workflows, scheduler = _services(tmp_path)
    definition = workflows.create_definition({"name": "Risky", "steps": [{"name": "send it", "action": "send"}]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run["status"] == "waiting_approval"
    job = scheduler.get_job(run["job_id"])
    assert job["status"] == "paused"  # blocked on a human, same as the run itself

    approved = workflows.approve_step(run["run_id"], approved=True)
    assert approved["status"] == "completed"
    job_after = scheduler.get_job(run["job_id"])
    assert job_after["status"] == "completed"


def test_rejected_step_still_completes_the_run_and_job(tmp_path):
    _, _, workflows, scheduler = _services(tmp_path)
    definition = workflows.create_definition({"name": "Risky2", "steps": [{"name": "send it", "action": "send"}]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    rejected = workflows.approve_step(run["run_id"], approved=False)
    assert rejected["status"] == "completed"  # only step is skipped, run still finishes
    job = scheduler.get_job(run["job_id"])
    assert job["status"] == "completed"


def test_cancelled_run_cancels_its_job(tmp_path):
    _, _, workflows, scheduler = _services(tmp_path)
    definition = workflows.create_definition({"name": "ToCancel", "steps": [{"name": "send it", "action": "send"}]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    cancelled = workflows.cancel_run(run["run_id"])
    assert cancelled["status"] == "cancelled"
    job = scheduler.get_job(run["job_id"])
    assert job["status"] == "canceled"


def test_ad_hoc_run_without_definition_still_gets_a_job(tmp_path):
    _, _, workflows, scheduler = _services(tmp_path)
    run = workflows.start_run({"name": "Ad hoc", "steps": [{"name": "just do it"}]})
    job = scheduler.get_job(run["job_id"])
    assert job is not None and job["payload"]["definition_id"] == ""


def test_without_agent_scheduler_wired_behavior_is_unchanged(tmp_path):
    """Backward compatibility: DurableWorkflowService with no scheduler collaborator
    behaves exactly as before v120 task 3 -- no job_id, no crash."""
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    workflows = DurableWorkflowService(s, g)  # no agent_scheduler
    definition = workflows.create_definition({"name": "Plain", "steps": [{"name": "x"}]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run["status"] == "completed"
    assert "job_id" not in run


def test_multi_gate_workflow_re_pauses_job_at_each_gate(tmp_path):
    _, _, workflows, scheduler = _services(tmp_path)
    definition = workflows.create_definition({"name": "TwoGates", "steps": [
        {"name": "send first", "action": "send"},
        {"name": "send second", "action": "send"},
    ]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run["status"] == "waiting_approval"
    job = scheduler.get_job(run["job_id"])
    assert job["status"] == "paused"

    still_gated = workflows.approve_step(run["run_id"], approved=True)
    assert still_gated["status"] == "waiting_approval"  # second gate
    job_mid = scheduler.get_job(run["job_id"])
    assert job_mid["status"] == "paused"  # same job, re-paused at the new gate

    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"
    job_final = scheduler.get_job(run["job_id"])
    assert job_final["status"] == "completed"


def test_endpoints_end_to_end():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    d = client.post("/api/durable-workflows/definitions", json={"name": "E2E-JQ", "steps": [{"name": "x"}]}).json()
    run = client.post("/api/durable-workflows/runs", json={"definition_id": d["definition_id"]}).json()
    assert run.get("job_id")
    job = client.get(f"/api/agent-jobs/{run['job_id']}").json()
    assert job["status"] == "completed"
    assert job["payload"]["run_id"] == run["run_id"]
    health = client.get("/api/agent-jobs/health").json()
    assert health["total_jobs"] >= 1


def test_existing_agent_jobs_manual_flow_still_works():
    """The pre-existing manual job API (create/pause/resume/cancel/heartbeat) is
    untouched -- this feature only ADDS automatic creation from real runs."""
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    job = client.post("/api/agent-jobs", json={"job_type": "tool", "title": "manual job"}).json()
    assert job["status"] == "queued"
    paused = client.post(f"/api/agent-jobs/{job['job_id']}/pause", json={"reason": "test"}).json()
    assert paused["status"] == "paused"
