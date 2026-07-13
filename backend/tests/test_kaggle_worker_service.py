from __future__ import annotations

import subprocess

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.agent_scheduler_service import AgentSchedulerService
from app.services.durable_workflow_service import DurableWorkflowService
from app.services.governance_service import GovernanceService
from app.services.kaggle_worker_service import KaggleWorkerError, KaggleWorkerService
from app.services.storage_service import StorageService
from app.services.worker_registry_service import WorkerRegistryService
from app.services.workspace_service import WorkspaceService

client = TestClient(app)


class _StubKaggleRunner:
    """Never invokes the real `kaggle` CLI -- returns canned CompletedProcess
    objects so tests can never create a real (quota-consuming) Kaggle kernel."""

    def __init__(self, responses: dict[str, subprocess.CompletedProcess]):
        self.responses = responses
        self.calls: list[list[str]] = []

    def __call__(self, argv, cwd, timeout=120):
        self.calls.append(argv)
        # argv looks like ["kaggle", "kernels", "push", ...] or ["kaggle", "config", "view"]
        # -- the verb (push/status/output/view) is always argv[2].
        key = argv[2] if len(argv) > 2 else (argv[1] if len(argv) > 1 else argv[0])
        return self.responses.get(key, subprocess.CompletedProcess(argv, 0, stdout="", stderr=""))


def _ok(stdout: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], 0, stdout=stdout, stderr="")


def _fail(stderr: str = "error") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], 1, stdout="", stderr=stderr)


@pytest.fixture
def kaggle_env(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "kaggle_worker_enabled", True)
    monkeypatch.setattr(settings, "kaggle_worker_private", True)
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    return storage, governance


# ------------------------------------------------------------------
# WorkerRegistryService -- pure local, no external calls at all.
# ------------------------------------------------------------------
def test_register_heartbeat_deregister_worker(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    registry = WorkerRegistryService(storage, GovernanceService(storage))
    worker = registry.register_worker("kaggle_gpu", capabilities=["gpu"], metadata={"note": "test"})
    assert worker["status"] == "online"
    updated = registry.heartbeat(worker["worker_id"], status="busy")
    assert updated["status"] == "busy"
    deregistered = registry.deregister_worker(worker["worker_id"])
    assert deregistered["status"] == "offline"
    assert registry.list_workers(status="offline")[0]["worker_id"] == worker["worker_id"]


def test_heartbeat_unknown_worker_raises(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    registry = WorkerRegistryService(storage, GovernanceService(storage))
    with pytest.raises(ValueError):
        registry.heartbeat("does-not-exist")


def test_worker_registry_dashboard(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    registry = WorkerRegistryService(storage, GovernanceService(storage))
    registry.register_worker("kaggle_gpu")
    registry.register_worker("kaggle_gpu")
    dashboard = registry.dashboard()
    assert dashboard["total_workers"] == 2
    assert dashboard["online"] == 2
    assert dashboard["by_type"]["kaggle_gpu"] == 2


# ------------------------------------------------------------------
# KaggleWorkerService -- real command construction, stubbed subprocess
# (NEVER invokes the real `kaggle` CLI in tests).
# ------------------------------------------------------------------
def test_submit_job_disabled_by_default_raises(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    service = KaggleWorkerService(storage, governance, kaggle_runner=_StubKaggleRunner({}))
    with pytest.raises(KaggleWorkerError):
        service.submit_job(code="print('hi')", title="Test job")


def test_submit_job_requires_code(kaggle_env):
    storage, governance = kaggle_env
    service = KaggleWorkerService(storage, governance, kaggle_runner=_StubKaggleRunner({}))
    with pytest.raises(KaggleWorkerError):
        service.submit_job(code="", title="Empty job")


def test_submit_job_success_creates_real_kernel_metadata_and_job_record(kaggle_env):
    storage, governance = kaggle_env
    runner = _StubKaggleRunner({"view": _ok("- username: testuser\n"), "push": _ok("Kernel version pushed.")})
    service = KaggleWorkerService(storage, governance, kaggle_runner=runner)
    job = service.submit_job(code="print('hello gpu')", title="My Job")
    assert job["submitted"] is True
    assert job["status"] == "submitted"
    assert job["kernel_ref"] == f"testuser/{job['kernel_slug']}"
    assert job in service.list_jobs()
    # real argv construction: push subcommand + -p <dir>, no shell=True involved
    push_call = next(c for c in runner.calls if "push" in c)
    assert push_call[0] == "kaggle"
    assert "-p" in push_call


def test_submit_job_failure_records_submit_failed(kaggle_env):
    storage, governance = kaggle_env
    runner = _StubKaggleRunner({"view": _ok("- username: testuser\n"), "push": _fail("quota exceeded")})
    service = KaggleWorkerService(storage, governance, kaggle_runner=runner)
    job = service.submit_job(code="print('x')", title="Failing job")
    assert job["submitted"] is False
    assert job["status"] == "submit_failed"
    assert "quota exceeded" in job["stderr_tail"]


def test_submit_job_registers_with_worker_registry_and_scheduler(kaggle_env):
    storage, governance = kaggle_env
    registry = WorkerRegistryService(storage, governance)
    scheduler = AgentSchedulerService(storage, governance, WorkspaceService(storage))
    runner = _StubKaggleRunner({"view": _ok("- username: testuser\n"), "push": _ok("pushed")})
    service = KaggleWorkerService(storage, governance, worker_registry=registry, agent_scheduler=scheduler, kaggle_runner=runner)
    job = service.submit_job(code="print(1)", title="Registered job")
    assert job["worker_id"] is not None
    assert registry.get_worker(job["worker_id"]) is not None
    assert job["agent_scheduler_job_id"] is not None
    assert scheduler.list_jobs()


def test_poll_job_updates_status_to_complete(kaggle_env):
    storage, governance = kaggle_env
    runner = _StubKaggleRunner({"view": _ok("- username: testuser\n"), "push": _ok("pushed")})
    service = KaggleWorkerService(storage, governance, kaggle_runner=runner)
    job = service.submit_job(code="print(1)", title="Poll job")
    runner.responses["status"] = _ok("Kernel has status \"complete\"")
    polled = service.poll_job(job["job_id"])
    assert polled["status"] == "complete"


def test_poll_job_updates_status_to_error(kaggle_env):
    storage, governance = kaggle_env
    runner = _StubKaggleRunner({"view": _ok("- username: testuser\n"), "push": _ok("pushed")})
    service = KaggleWorkerService(storage, governance, kaggle_runner=runner)
    job = service.submit_job(code="print(1)", title="Poll error job")
    runner.responses["status"] = _ok("Kernel has status \"error\"")
    polled = service.poll_job(job["job_id"])
    assert polled["status"] == "error"


def test_poll_job_not_found_raises(kaggle_env):
    storage, governance = kaggle_env
    service = KaggleWorkerService(storage, governance, kaggle_runner=_StubKaggleRunner({}))
    with pytest.raises(ValueError):
        service.poll_job("does-not-exist")


# ------------------------------------------------------------------
# worker_registry lifecycle closure: register_worker() at submit time was
# never balanced by a deregister on completion, so every job leaked a
# permanent "online" phantom worker (inflating WorkerRegistryService's
# dashboard/analytics_summary indefinitely).
# ------------------------------------------------------------------
def test_poll_job_complete_deregisters_worker(kaggle_env):
    storage, governance = kaggle_env
    registry = WorkerRegistryService(storage, governance)
    runner = _StubKaggleRunner({"view": _ok("- username: testuser\n"), "push": _ok("pushed")})
    service = KaggleWorkerService(storage, governance, worker_registry=registry, kaggle_runner=runner)
    job = service.submit_job(code="print(1)", title="Poll complete job")
    assert registry.get_worker(job["worker_id"])["status"] == "online"

    runner.responses["status"] = _ok("Kernel has status \"complete\"")
    service.poll_job(job["job_id"])
    assert registry.get_worker(job["worker_id"])["status"] == "offline"


def test_poll_job_error_deregisters_worker(kaggle_env):
    storage, governance = kaggle_env
    registry = WorkerRegistryService(storage, governance)
    runner = _StubKaggleRunner({"view": _ok("- username: testuser\n"), "push": _ok("pushed")})
    service = KaggleWorkerService(storage, governance, worker_registry=registry, kaggle_runner=runner)
    job = service.submit_job(code="print(1)", title="Poll error job")

    runner.responses["status"] = _ok("Kernel has status \"error\"")
    service.poll_job(job["job_id"])
    assert registry.get_worker(job["worker_id"])["status"] == "offline"


def test_poll_job_still_running_does_not_deregister_worker(kaggle_env):
    storage, governance = kaggle_env
    registry = WorkerRegistryService(storage, governance)
    runner = _StubKaggleRunner({"view": _ok("- username: testuser\n"), "push": _ok("pushed")})
    service = KaggleWorkerService(storage, governance, worker_registry=registry, kaggle_runner=runner)
    job = service.submit_job(code="print(1)", title="Poll running job")

    runner.responses["status"] = _ok("Kernel has status \"running\"")
    service.poll_job(job["job_id"])
    assert registry.get_worker(job["worker_id"])["status"] == "online"


def test_get_job_output_not_found_raises(kaggle_env):
    storage, governance = kaggle_env
    service = KaggleWorkerService(storage, governance, kaggle_runner=_StubKaggleRunner({}))
    with pytest.raises(ValueError):
        service.get_job_output("does-not-exist")


def test_username_resolution_is_cached(kaggle_env):
    storage, governance = kaggle_env
    runner = _StubKaggleRunner({"view": _ok("- username: cacheduser\n"), "push": _ok("pushed")})
    service = KaggleWorkerService(storage, governance, kaggle_runner=runner)
    service.submit_job(code="print(1)", title="First")
    service.submit_job(code="print(2)", title="Second")
    view_calls = [c for c in runner.calls if "view" in c]
    assert len(view_calls) == 1  # resolved once, cached after


def test_analytics_summary_counts_jobs(kaggle_env):
    storage, governance = kaggle_env
    runner = _StubKaggleRunner({"view": _ok("- username: testuser\n"), "push": _ok("pushed")})
    service = KaggleWorkerService(storage, governance, kaggle_runner=runner)
    service.submit_job(code="print(1)", title="A")
    summary = service.analytics_summary()
    assert summary["kaggle_jobs_total"] == 1
    assert summary["kaggle_jobs_submitted"] == 1


# ------------------------------------------------------------------
# status() -- consumed by CapabilityDirectoryService to classify this real
# capability as real/mock without inventing a fake always-on status.
# ------------------------------------------------------------------
def test_status_reports_enabled_and_disabled(kaggle_env, monkeypatch):
    storage, governance = kaggle_env
    service = KaggleWorkerService(storage, governance)
    assert service.status()["enabled"] is True  # kaggle_env fixture sets it True

    monkeypatch.setattr(settings, "kaggle_worker_enabled", False)
    assert service.status()["enabled"] is False


def test_status_counts_real_jobs(kaggle_env):
    storage, governance = kaggle_env
    runner = _StubKaggleRunner({"view": _ok("- username: testuser\n"), "push": _ok("pushed")})
    service = KaggleWorkerService(storage, governance, kaggle_runner=runner)
    assert service.status()["total_jobs"] == 0
    service.submit_job(code="print(1)", title="A")
    assert service.status()["total_jobs"] == 1


# ------------------------------------------------------------------
# Platform-wide /api/analytics aggregation: worker_registry_service and
# kaggle_worker_service were both built in #221 but never folded into the
# hand-maintained rollup, silently under-reporting compute/GPU-job activity.
# ------------------------------------------------------------------
def test_analytics_endpoint_includes_worker_services():
    analytics = client.get("/api/analytics").json()
    for key in ("compute_workers_total", "compute_workers_online",
                "kaggle_jobs_total", "kaggle_jobs_submitted", "kaggle_jobs_complete"):
        assert key in analytics


def test_capability_directory_lists_kaggle_gpu_worker():
    data = client.get("/api/capability-directory").json()
    names = {c["name"] for c in data["capabilities"]}
    assert "Kaggle GPU Worker (real kernel submission)" in names
    entry = next(c for c in data["capabilities"] if c["name"] == "Kaggle GPU Worker (real kernel submission)")
    assert entry["status"] in ("real", "mock")  # off by default in test settings -> mock
    assert entry["route"] == "/api/worker-registry"


# ------------------------------------------------------------------
# DurableWorkflowService: run_kaggle_job whitelisted action wiring.
# ------------------------------------------------------------------
def test_run_kaggle_job_disabled_declines_safely(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    kaggle_worker = KaggleWorkerService(storage, governance, kaggle_runner=_StubKaggleRunner({}))
    service = DurableWorkflowService(storage, governance, kaggle_worker=kaggle_worker)
    run = service.start_run({"steps": [{
        "name": "gpu job", "action_type": "run_kaggle_job",
        "action_params": {"code": "print(1)", "title": "Test"},
    }]})
    assert run["steps"][0]["requires_approval"] is True
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "completed"  # disabled degrades to a safe decline, never fails the run
    assert "[declined] run_kaggle_job" in done["steps"][0]["output"]


def test_run_kaggle_job_without_collaborator_declines_safely(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    service = DurableWorkflowService(storage, governance, kaggle_worker=None)
    run = service.start_run({"steps": [{
        "name": "gpu job", "action_type": "run_kaggle_job",
        "action_params": {"code": "print(1)", "title": "Test"},
    }]})
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "completed"
    assert "[declined] run_kaggle_job" in done["steps"][0]["output"]


def test_run_kaggle_job_missing_code_declines_safely(kaggle_env):
    storage, governance = kaggle_env
    kaggle_worker = KaggleWorkerService(storage, governance, kaggle_runner=_StubKaggleRunner({}))
    service = DurableWorkflowService(storage, governance, kaggle_worker=kaggle_worker)
    run = service.start_run({"steps": [{"name": "gpu job", "action_type": "run_kaggle_job"}]})
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "completed"
    assert "[declined] run_kaggle_job" in done["steps"][0]["output"]


def test_run_kaggle_job_enabled_submits_real_job(kaggle_env):
    storage, governance = kaggle_env
    runner = _StubKaggleRunner({"view": _ok("- username: testuser\n"), "push": _ok("pushed")})
    kaggle_worker = KaggleWorkerService(storage, governance, kaggle_runner=runner)
    service = DurableWorkflowService(storage, governance, kaggle_worker=kaggle_worker)
    run = service.start_run({"steps": [{
        "name": "gpu job", "action_type": "run_kaggle_job",
        "action_params": {"code": "print('hi')", "title": "Real submit"},
    }]})
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "completed"
    assert "[executed] run_kaggle_job" in done["steps"][0]["output"]
    assert kaggle_worker.list_jobs()


# ------------------------------------------------------------------
# App wiring: worker-registry + Kaggle worker routes are registered and
# degrade safely with KAGGLE_WORKER_ENABLED off (the default in this app).
# ------------------------------------------------------------------
def test_worker_registry_endpoints_registered():
    assert client.get("/api/worker-registry/dashboard").status_code == 200
    assert client.get("/api/worker-registry/workers").status_code == 200
    created = client.post("/api/worker-registry/workers", json={"worker_type": "kaggle_gpu"}).json()
    assert created["worker_id"]
    assert client.post(f"/api/worker-registry/workers/{created['worker_id']}/heartbeat").status_code == 200
    assert client.delete(f"/api/worker-registry/workers/{created['worker_id']}").status_code == 200


def test_kaggle_job_endpoint_declines_when_disabled_by_default():
    assert client.get("/api/worker-registry/kaggle/jobs").status_code == 200
    response = client.post("/api/worker-registry/kaggle/jobs", json={"code": "print(1)", "title": "x"})
    assert response.status_code == 400  # KAGGLE_WORKER_ENABLED is off by default in this app
    assert "disabled" in response.json()["detail"].lower()


def test_kaggle_job_not_found_endpoints():
    assert client.get("/api/worker-registry/kaggle/jobs/does-not-exist").status_code == 404
    assert client.post("/api/worker-registry/kaggle/jobs/does-not-exist/poll").status_code == 404
    assert client.get("/api/worker-registry/kaggle/jobs/does-not-exist/output").status_code == 404
