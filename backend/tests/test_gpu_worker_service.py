from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.services.governance_service import GovernanceService
from app.services.gpu_worker_service import GPUWorkerService
from app.services.kaggle_worker_service import KaggleWorkerService
from app.services.runpod_worker_service import RunPodWorkerService
from app.services.storage_service import StorageService
from app.services.worker_registry_service import WorkerRegistryService

client = TestClient(app)


def _service(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    registry = WorkerRegistryService(storage, governance)
    kaggle = KaggleWorkerService(storage, governance, worker_registry=registry, kaggle_runner=lambda *_: None)
    runpod = RunPodWorkerService(storage, governance, worker_registry=registry)
    return GPUWorkerService(registry, kaggle, governance, runpod_worker=runpod), registry, storage


def test_dashboard_normalizes_legacy_and_gpu_workers(tmp_path):
    service, registry, _ = _service(tmp_path)
    registry.register_worker("legacy_worker", capabilities=["cpu"], metadata={"note": "old shape"})
    service.register_local_worker({
        "name": "Studio 4090",
        "gpu_model": "RTX 4090",
        "gpu_memory_gb": 24,
        "region": "desk",
        "runtime": "python",
    })

    dashboard = service.dashboard()

    assert dashboard["total_gpu_workers"] == 2
    assert dashboard["by_provider"]["local"] == 1
    assert any(worker["gpu_model"] == "RTX 4090" for worker in dashboard["workers"])
    assert any(worker["provider"] == "other" for worker in dashboard["workers"])


def test_provider_readiness_reports_booleans_and_env_names_only(tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "runpod_worker_enabled", True)
    monkeypatch.setattr(settings, "runpod_api_key", "secret-runpod-token")
    monkeypatch.setattr(settings, "runpod_default_endpoint_id", "rp-endpoint")
    service, _, _ = _service(tmp_path)

    runpod = next(provider for provider in service.providers()["providers"] if provider["provider"] == "runpod")

    assert runpod["enabled"] is True
    assert runpod["configured"] is True
    assert runpod["execution_enabled"] is True
    assert runpod["required_env_vars"] == ["RUNPOD_WORKER_ENABLED", "RUNPOD_API_KEY", "RUNPOD_DEFAULT_ENDPOINT_ID"]
    assert "secret-runpod-token" not in str(runpod)


def test_dry_run_accepts_runpod_only_when_configured_for_approval(tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "runpod_worker_enabled", True)
    monkeypatch.setattr(settings, "runpod_api_key", "secret-runpod-token")
    monkeypatch.setattr(settings, "runpod_default_endpoint_id", "rp-endpoint")
    service, _, storage = _service(tmp_path)

    result = service.dry_run({"provider": "runpod", "title": "paid gpu job"})

    assert result["accepted"] is True
    assert result["requires_approval"] is True
    assert result["execution_path"] == "durable_workflow.run_runpod_job"
    assert "secret-runpod-token" not in str(result)
    events = storage.read_list("governance_log.json")
    assert any(event.get("action_type") == "gpu_worker_dry_run" and event.get("blocked") is False for event in events)


def test_dry_run_declines_runpod_when_disabled(tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "runpod_worker_enabled", False)
    monkeypatch.setattr(settings, "runpod_api_key", "secret-runpod-token")
    monkeypatch.setattr(settings, "runpod_default_endpoint_id", "rp-endpoint")
    service, _, _ = _service(tmp_path)

    result = service.dry_run({"provider": "runpod", "title": "paid gpu job"})

    assert result["accepted"] is False
    assert result["requires_approval"] is False
    assert "RUNPOD_WORKER_ENABLED" in result["declined_reason"]
    assert "secret-runpod-token" not in str(result)


def test_dry_run_declines_kaggle_when_disabled(tmp_path):
    service, _, _ = _service(tmp_path)

    result = service.dry_run({"provider": "kaggle", "title": "kernel"})

    assert result["accepted"] is False
    assert result["requires_approval"] is False
    assert "KAGGLE_WORKER_ENABLED" in result["declined_reason"]


def test_register_local_worker_uses_existing_registry_and_logs(tmp_path):
    service, registry, storage = _service(tmp_path)

    worker = service.register_local_worker({"name": "Local A100", "gpu_model": "A100", "gpu_memory_gb": 80})

    assert worker["worker_type"] == "local_gpu"
    assert worker["provider"] == "local"
    assert worker["gpu_model"] == "A100"
    assert registry.get_worker(worker["worker_id"])["worker_id"] == worker["worker_id"]
    events = storage.read_list("governance_log.json")
    assert any(event.get("action_type") == "gpu_local_worker_registered" for event in events)


def test_gpu_worker_api_endpoints_registered_and_safe(monkeypatch):
    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    monkeypatch.delenv("RUNPOD_WORKER_ENABLED", raising=False)
    monkeypatch.delenv("RUNPOD_EXECUTION_ENABLED", raising=False)

    assert client.get("/api/worker-registry/gpu/dashboard").status_code == 200
    providers = client.get("/api/worker-registry/gpu/providers")
    assert providers.status_code == 200
    assert "providers" in providers.json()

    dry_run = client.post("/api/worker-registry/gpu/dry-run", json={"provider": "runpod", "title": "smoke"})
    assert dry_run.status_code == 200
    assert dry_run.json()["accepted"] is False

    assert client.get("/api/worker-registry/runpod/jobs").status_code == 200
    direct_submit = client.post("/api/worker-registry/runpod/jobs", json={"input": {"prompt": "x"}, "title": "x"})
    assert direct_submit.status_code == 400
    assert "durable workflow" in direct_submit.json()["detail"].lower()

    created = client.post(
        "/api/worker-registry/gpu/local-workers",
        json={"name": "Smoke GPU", "gpu_model": "M-series", "gpu_memory_gb": 16},
    )
    assert created.status_code == 200
    assert created.json()["provider"] == "local"
