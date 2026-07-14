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


# ------------------------------------------------------------------
# concurrency_limit visibility: it's only actually enforced by start_next()
# (the manual dequeue flow) -- real automated producers (DurableWorkflowService,
# KaggleWorkerService) create+heartbeat jobs directly, bypassing that gate by
# design (their own engines are the real throttle). health() now surfaces
# real running-vs-limit status as pure observability -- it must never block
# a real run or job.
# ------------------------------------------------------------------
def test_health_reports_concurrency_limit_status(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    ws = WorkspaceService(s)
    scheduler = AgentSchedulerService(s, g, ws, concurrency_limit=2)
    health = scheduler.health()
    assert health["concurrency_limit"] == 2
    assert health["running"] == 0
    assert health["over_concurrency_limit"] is False


def test_health_flags_over_concurrency_limit_without_blocking_anything(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    ws = WorkspaceService(s)
    scheduler = AgentSchedulerService(s, g, ws, concurrency_limit=1)
    workflows = DurableWorkflowService(s, g, agent_scheduler=scheduler)
    # Two real workflow runs, both must actually execute -- concurrency_limit
    # must never block a real run, only be visible after the fact.
    d1 = workflows.create_definition({"name": "A", "steps": [{"name": "x", "action": "send"}]})
    d2 = workflows.create_definition({"name": "B", "steps": [{"name": "y", "action": "send"}]})
    run1 = workflows.start_run({"definition_id": d1["definition_id"]})
    run2 = workflows.start_run({"definition_id": d2["definition_id"]})
    assert run1["status"] == "waiting_approval"  # both real runs proceeded, unthrottled
    assert run2["status"] == "waiting_approval"

    health = scheduler.health()
    assert health["running"] == 0  # waiting_approval maps to "paused", not "running"
    assert health["concurrency_limit"] == 1
    assert health["over_concurrency_limit"] is False


def test_agent_jobs_health_endpoint_includes_concurrency_fields():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    health = client.get("/api/agent-jobs/health").json()
    assert "concurrency_limit" in health
    assert "over_concurrency_limit" in health
    assert isinstance(health["over_concurrency_limit"], bool)


# ------------------------------------------------------------------
# Round 27: create_job()/start_next()/_transition() had the same lost-update
# shape rounds 25/26 fixed elsewhere -- a hand-rolled read_list() -> mutate ->
# write_list() on the shared agent_jobs.json. Independently reproduced against
# the real unmodified code (patching read_list to widen the window) before
# writing the fix: one job's transition (e.g. complete()) silently vanished
# when it raced a different job's transition (e.g. heartbeat()). These tests
# prove the fix (update_list()/atomic append()) survives genuine concurrent
# contention against the actual code path (patching storage.update_list,
# which the fixed code genuinely calls, not read_list which it bypasses).
# ------------------------------------------------------------------
def test_transition_does_not_lose_a_concurrent_transition_of_a_different_job(tmp_path):
    import threading
    import time

    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    ws = WorkspaceService(storage)
    scheduler = AgentSchedulerService(storage, governance, ws)

    j1 = scheduler.create_job({"title": "J1"})
    j2 = scheduler.create_job({"title": "J2"})
    scheduler._transition(j1["job_id"], "running", "start")
    scheduler._transition(j2["job_id"], "running", "start")

    entered = threading.Event()
    original_update_list = storage.update_list

    def _slow_update_list(filename, mutator):
        def _slow_mutator(items):
            entered.set()
            time.sleep(0.2)
            return mutator(items)
        return original_update_list(filename, _slow_mutator)

    storage.update_list = _slow_update_list

    def _heartbeat_j2():
        scheduler.heartbeat(j2["job_id"])

    t = threading.Thread(target=_heartbeat_j2)
    t.start()
    entered.wait(timeout=2)
    scheduler.complete(j1["job_id"], "done")  # concurrent transition of a DIFFERENT job
    t.join(timeout=2)

    assert scheduler.get_job(j2["job_id"])["status"] == "running"  # heartbeat must not be lost
    assert scheduler.get_job(j1["job_id"])["status"] == "completed"  # completion must not be lost


def test_create_job_does_not_lose_jobs_under_real_concurrency(tmp_path):
    """create_job() previously hand-rolled read_list() + append in memory +
    write_list() -- the same lost-update shape as _transition(), just for job
    creation instead of job transitions (real concurrent writers: a Kaggle
    submit_job() and a durable workflow start can both create a job at once).
    Now delegates to the already-atomic storage.append(); stress with many
    genuinely concurrent threads to catch any regression back to a hand-rolled
    read-modify-write."""
    import threading

    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    ws = WorkspaceService(storage)
    scheduler = AgentSchedulerService(storage, governance, ws)

    def _create(i):
        scheduler.create_job({"title": f"job-{i}"})

    threads = [threading.Thread(target=_create, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    titles = {job["title"] for job in scheduler.list_jobs()}
    assert titles == {f"job-{i}" for i in range(20)}  # none lost
