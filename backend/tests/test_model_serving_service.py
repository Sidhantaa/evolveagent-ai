from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.governance_service import GovernanceService
from app.services.model_serving_service import ModelServingService
from app.services.storage_service import StorageService

client = TestClient(app)


class _FakeResponse:
    def __init__(self, data, status_code: int = 200):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            request = httpx.Request("GET", "http://127.0.0.1:1/test")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("boom", request=request, response=response)

    def json(self):
        return self._data


class _FakeModelServingHTTP:
    def __init__(self, data=None, status_code: int = 200, raise_exc: Exception | None = None):
        self.data = data if data is not None else {"models": [{"name": "llama3"}]}
        self.status_code = status_code
        self.raise_exc = raise_exc
        self.calls: list[dict] = []

    def get(self, url, timeout):
        self.calls.append({"url": url, "timeout": timeout})
        if self.raise_exc is not None:
            raise self.raise_exc
        return _FakeResponse(self.data, status_code=self.status_code)


def test_unconfigured_backend_is_reported_without_any_http_call(monkeypatch, tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    http = _FakeModelServingHTTP()
    monkeypatch.setattr(settings, "ollama_base_url", None)
    service = ModelServingService(governance, http_client=http)

    result = service.detect("ollama")

    assert result == {
        "backend": "ollama",
        "name": "Ollama",
        "configured": False,
        "reachable": False,
        "models": [],
        "checked_at": result["checked_at"],
        "note": "Set OLLAMA_BASE_URL to an already-running local endpoint to enable detection.",
    }
    assert http.calls == []  # never attempted a request for an unconfigured backend


def test_configured_and_reachable_backend_reports_its_models(monkeypatch, tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    http = _FakeModelServingHTTP(data={"models": [{"name": "llama3"}, {"name": "mistral"}]})
    monkeypatch.setattr(settings, "ollama_base_url", "http://127.0.0.1:11434")
    service = ModelServingService(governance, http_client=http)

    result = service.detect("ollama")

    assert result["configured"] is True
    assert result["reachable"] is True
    assert result["models"] == ["llama3", "mistral"]
    assert http.calls[0]["url"] == "http://127.0.0.1:11434/api/tags"


def test_configured_but_unreachable_backend_degrades_safely(monkeypatch, tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    http = _FakeModelServingHTTP(raise_exc=ConnectionError("refused"))
    monkeypatch.setattr(settings, "ollama_base_url", "http://127.0.0.1:11434")
    service = ModelServingService(governance, http_client=http)

    result = service.detect("ollama")

    assert result["configured"] is True
    assert result["reachable"] is False
    assert result["models"] == []


def test_unknown_backend_never_attempts_a_request(monkeypatch, tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    http = _FakeModelServingHTTP()
    service = ModelServingService(governance, http_client=http)

    result = service.detect("some-made-up-backend")

    assert result["configured"] is False
    assert result["reachable"] is False
    assert http.calls == []


def test_dashboard_never_starts_a_server_and_reports_all_known_backends(monkeypatch, tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    monkeypatch.setattr(settings, "ollama_base_url", None)
    monkeypatch.setattr(settings, "vllm_base_url", None)
    monkeypatch.setattr(settings, "local_openai_compatible_base_url", None)
    service = ModelServingService(governance, http_client=_FakeModelServingHTTP())

    dashboard = service.dashboard()

    assert dashboard["count"] == 3
    assert dashboard["reachable_count"] == 0  # nothing configured -> nothing reachable
    assert dashboard["real_execution_default"] == "disabled"
    assert {row["backend"] for row in dashboard["backends"]} == {"ollama", "vllm", "openai_compatible_endpoint"}


def test_dry_run_declines_for_unconfigured_backend(monkeypatch, tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    monkeypatch.setattr(settings, "ollama_base_url", None)
    service = ModelServingService(governance, http_client=_FakeModelServingHTTP())

    result = service.dry_run({"backend": "ollama", "model": "llama3"})

    assert result["accepted"] is False
    assert "OLLAMA_BASE_URL" in result["declined_reason"]


def test_dry_run_accepts_when_the_requested_model_is_loaded(monkeypatch, tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    http = _FakeModelServingHTTP(data={"models": [{"name": "llama3"}]})
    monkeypatch.setattr(settings, "ollama_base_url", "http://127.0.0.1:11434")
    service = ModelServingService(governance, http_client=http)

    result = service.dry_run({"backend": "ollama", "model": "llama3"})

    assert result["accepted"] is True
    assert result["declined_reason"] == ""


def test_dry_run_declines_when_the_requested_model_is_not_loaded(monkeypatch, tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    http = _FakeModelServingHTTP(data={"models": [{"name": "llama3"}]})
    monkeypatch.setattr(settings, "ollama_base_url", "http://127.0.0.1:11434")
    service = ModelServingService(governance, http_client=http)

    result = service.dry_run({"backend": "ollama", "model": "codellama"})

    assert result["accepted"] is False
    assert "codellama" in result["declined_reason"]


def test_analytics_summary_never_makes_a_network_call(monkeypatch, tmp_path):
    """/api/analytics is a hot path polled by the frontend -- analytics_summary()
    must stay a local, non-blocking read like every other service's, never a
    live detect() over the network."""
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    http = _FakeModelServingHTTP()
    monkeypatch.setattr(settings, "ollama_base_url", "http://127.0.0.1:11434")
    monkeypatch.setattr(settings, "vllm_base_url", None)
    monkeypatch.setattr(settings, "local_openai_compatible_base_url", None)
    service = ModelServingService(governance, http_client=http)

    summary = service.analytics_summary()

    assert summary == {"model_serving_backends_total": 3, "model_serving_backends_configured": 1}
    assert http.calls == []  # no live request triggered by analytics


def test_dashboard_endpoint_is_wired_and_never_starts_a_server():
    r = client.get("/api/model-serving/dashboard").json()
    assert r["count"] == 3
    assert r["real_execution_default"] == "disabled"


def test_dry_run_endpoint_declines_safely_with_no_backend_configured():
    r = client.post("/api/model-serving/dry-run", json={"backend": "ollama", "model": "llama3"}).json()
    assert r["accepted"] is False


def test_model_serving_analytics_are_exposed_in_the_global_analytics_endpoint():
    r = client.get("/api/analytics").json()
    assert "model_serving_backends_total" in r
    assert "model_serving_backends_configured" in r
