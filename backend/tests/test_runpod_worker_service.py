from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.agent_scheduler_service import AgentSchedulerService
from app.services.durable_workflow_service import DurableWorkflowService
from app.services.governance_service import GovernanceService
from app.services.runpod_worker_service import RunPodWorkerError, RunPodWorkerService
from app.services.storage_service import StorageService
from app.services.worker_registry_service import WorkerRegistryService
from app.services.workspace_service import WorkspaceService

client = TestClient(app)


class _FakeResponse:
    def __init__(self, data: dict, status_code: int = 200):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            request = httpx.Request("GET", "https://api.runpod.ai/test")
            response = httpx.Response(self.status_code, request=request, json=self._data)
            raise httpx.HTTPStatusError("boom", request=request, response=response)

    def json(self):
        return self._data


class _FakeRunPodHTTP:
    def __init__(self, post_data: dict | None = None, get_data: dict | None = None, status_code: int = 200):
        self.post_data = post_data or {"id": "rp-job-1", "status": "IN_QUEUE"}
        self.get_data = get_data or {"id": "rp-job-1", "status": "COMPLETED", "output": {"result": "ok"}}
        self.status_code = status_code
        self.calls: list[dict] = []

    def post(self, url, headers, json, timeout):
        self.calls.append({"method": "POST", "url": url, "headers": headers, "json": json, "timeout": timeout})
        return _FakeResponse(self.post_data, status_code=self.status_code)

    def get(self, url, headers, timeout):
        self.calls.append({"method": "GET", "url": url, "headers": headers, "timeout": timeout})
        return _FakeResponse(self.get_data, status_code=self.status_code)


@pytest.fixture
def runpod_env(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "runpod_worker_enabled", True)
    monkeypatch.setattr(settings, "runpod_api_key", "secret-runpod-token")
    monkeypatch.setattr(settings, "runpod_default_endpoint_id", "endpoint-1")
    monkeypatch.setattr(settings, "runpod_api_base_url", "https://api.runpod.ai")
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    return storage, governance


def test_submit_job_disabled_by_default_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "runpod_worker_enabled", False)
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    service = RunPodWorkerService(storage, governance, http_client=_FakeRunPodHTTP())

    with pytest.raises(RunPodWorkerError):
        service.submit_job(input_payload={"prompt": "hi"}, title="Disabled")


def test_submit_job_uses_authorization_header_and_sanitizes_records(runpod_env):
    storage, governance = runpod_env
    registry = WorkerRegistryService(storage, governance)
    scheduler = AgentSchedulerService(storage, governance, WorkspaceService(storage))
    http = _FakeRunPodHTTP()
    service = RunPodWorkerService(storage, governance, worker_registry=registry, agent_scheduler=scheduler, http_client=http)

    job = service.submit_job(input_payload={"prompt": "hello"}, title="RunPod smoke")

    assert job["submitted"] is True
    assert job["runpod_job_id"] == "rp-job-1"
    assert job["status"] == "queued"
    assert job["worker_id"]
    assert registry.get_worker(job["worker_id"])["provider"] == "runpod"
    assert job["agent_scheduler_job_id"]
    assert http.calls[0]["headers"]["Authorization"] == "Bearer secret-runpod-token"

    visible = str(job) + str(storage.read_list("governance_log.json")) + str(service.status())
    assert "secret-runpod-token" not in visible
    assert "Authorization" not in visible


def test_submit_job_http_error_never_leaks_api_key(runpod_env):
    storage, governance = runpod_env
    http = _FakeRunPodHTTP(post_data={"error": "bad token secret-runpod-token"}, status_code=401)
    service = RunPodWorkerService(storage, governance, http_client=http)

    job = service.submit_job(input_payload={"prompt": "hello"}, title="Error path")

    assert job["submitted"] is False
    assert job["status"] == "submit_failed"
    assert "HTTP 401" in job["error"]
    visible = str(job) + str(storage.read_list("governance_log.json"))
    assert "secret-runpod-token" not in visible
    assert "bad token" not in visible


def test_poll_job_complete_deregisters_worker_and_stores_output(runpod_env):
    storage, governance = runpod_env
    registry = WorkerRegistryService(storage, governance)
    http = _FakeRunPodHTTP(get_data={"id": "rp-job-1", "status": "COMPLETED", "output": {"answer": 42}})
    service = RunPodWorkerService(storage, governance, worker_registry=registry, http_client=http)
    job = service.submit_job(input_payload={"prompt": "hello"}, title="Poll")
    assert registry.get_worker(job["worker_id"])["status"] == "online"

    polled = service.poll_job(job["job_id"])

    assert polled["status"] == "complete"
    assert polled["output"] == {"answer": 42}
    assert registry.get_worker(job["worker_id"])["status"] == "offline"
    output = service.get_job_output(job["job_id"])
    assert output["available"] is True
    assert output["output"] == {"answer": 42}


def test_poll_job_error_deregisters_worker(runpod_env):
    storage, governance = runpod_env
    registry = WorkerRegistryService(storage, governance)
    http = _FakeRunPodHTTP(get_data={"id": "rp-job-1", "status": "FAILED", "error": "runtime failed"})
    service = RunPodWorkerService(storage, governance, worker_registry=registry, http_client=http)
    job = service.submit_job(input_payload={"prompt": "hello"}, title="Poll error")

    polled = service.poll_job(job["job_id"])

    assert polled["status"] == "error"
    assert registry.get_worker(job["worker_id"])["status"] == "offline"


def test_runpod_status_reports_booleans_only(runpod_env):
    storage, governance = runpod_env
    service = RunPodWorkerService(storage, governance, http_client=_FakeRunPodHTTP())

    status = service.status()

    assert status["enabled"] is True
    assert status["configured"] is True
    assert status["default_endpoint_set"] is True
    assert "secret-runpod-token" not in str(status)


def test_run_runpod_job_disabled_declines_safely(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "runpod_worker_enabled", False)
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    runpod_worker = RunPodWorkerService(storage, governance, http_client=_FakeRunPodHTTP())
    service = DurableWorkflowService(storage, governance, runpod_worker=runpod_worker)
    run = service.start_run({"steps": [{
        "name": "gpu job", "action_type": "run_runpod_job",
        "action_params": {"input": "{\"prompt\":\"hello\"}", "title": "Test"},
    }]})

    assert run["steps"][0]["requires_approval"] is True
    done = service.approve_step(run["run_id"], approved=True)
    assert done["status"] == "completed"
    assert "[declined] run_runpod_job" in done["steps"][0]["output"]


def test_run_runpod_job_enabled_submits_after_approval(runpod_env):
    storage, governance = runpod_env
    http = _FakeRunPodHTTP()
    runpod_worker = RunPodWorkerService(storage, governance, http_client=http)
    service = DurableWorkflowService(storage, governance, runpod_worker=runpod_worker)
    run = service.start_run({"steps": [{
        "name": "gpu job", "action_type": "run_runpod_job",
        "action_params": {"input": "{\"prompt\":\"hello\"}", "title": "Real submit"},
    }]})

    done = service.approve_step(run["run_id"], approved=True)

    assert done["status"] == "completed"
    assert "[executed] run_runpod_job" in done["steps"][0]["output"]
    assert runpod_worker.list_jobs()


def test_runpod_api_routes_registered_and_secret_safe(monkeypatch):
    monkeypatch.setattr(settings, "runpod_api_key", "secret-runpod-token")

    assert client.get("/api/worker-registry/runpod/jobs").status_code == 200
    direct = client.post("/api/worker-registry/runpod/jobs", json={"input": {"prompt": "x"}, "title": "x"})
    assert direct.status_code == 400
    assert "durable workflow" in direct.json()["detail"].lower()
    assert "secret-runpod-token" not in str(direct.json())
    assert client.get("/api/worker-registry/runpod/jobs/does-not-exist").status_code == 404
    assert client.post("/api/worker-registry/runpod/jobs/does-not-exist/poll").status_code == 404
    assert client.get("/api/worker-registry/runpod/jobs/does-not-exist/output").status_code == 404
