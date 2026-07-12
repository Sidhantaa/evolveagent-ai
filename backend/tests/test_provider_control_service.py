from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_lists_providers():
    data = client.get("/api/provider-control/dashboard").json()
    ids = {p["id"] for p in data["providers"]}
    for expected in ("openai", "anthropic", "gemini", "mistral", "local"):
        assert expected in ids
    # local is always ready
    assert next(p for p in data["providers"] if p["id"] == "local")["ready"] is True
    assert "fallback_policy" in data and "cost_estimate_usd" in data


def test_key_check_is_boolean_only():
    data = client.get("/api/provider-control/key-check").json()
    for check in data["checks"]:
        for key in check["keys"]:
            assert set(key.keys()) == {"key_name", "is_set"}
            assert isinstance(key["is_set"], bool)  # never a value
    assert "booleans only" in data["note"].lower()


def test_update_model_and_capability_prefs():
    result = client.patch("/api/provider-control", json={
        "model_by_task": {"coding": "claude-opus-4-8"},
        "capability_modes": {"chat": "real"},
    }).json()
    assert result["config"]["model_by_task"]["coding"] == "claude-opus-4-8"
    assert result["config"]["capability_modes"]["chat"] == "real"
    assert result["rejected"] == []


def test_bad_capability_mode_rejected():
    result = client.patch("/api/provider-control", json={"capability_modes": {"chat": "turbo"}}).json()
    assert any("capability_modes.chat" in r for r in result["rejected"])


def test_unknown_task_rejected():
    result = client.patch("/api/provider-control", json={"model_by_task": {"nonsense": "x"}}).json()
    assert any("model_by_task.nonsense" in r for r in result["rejected"])


def test_summary_and_analytics():
    summary = client.get("/api/provider-control/summary").json()
    for key in ("total_providers", "ready_providers", "capability_modes"):
        assert key in summary
    analytics = client.get("/api/analytics").json()
    for key in ("provider_control_ready_providers", "provider_control_total_providers"):
        assert key in analytics


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/provider-control/dashboard")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "provider_control_viewed" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/settings").status_code == 200
    assert client.get("/api/demo/summary").status_code == 200


def test_preferred_model_for_task_reads_stored_preference():
    client.patch("/api/provider-control", json={"model_by_task": {"research": "gemini-1.5-pro"}})
    from app.api.routes import provider_control_service
    assert provider_control_service.preferred_model_for_task("research") == "gemini-1.5-pro"


def test_preferred_model_for_task_none_when_unset():
    from app.api.routes import provider_control_service
    assert provider_control_service.preferred_model_for_task("nonexistent-task-xyz") is None


def test_health_endpoint_available_when_wired_to_router():
    data = client.get("/api/provider-control/health").json()
    assert data["available"] is True
    assert "providers" in data


def test_dashboard_includes_provider_health():
    data = client.get("/api/provider-control/dashboard").json()
    assert "provider_health" in data
    assert "available" in data["provider_health"]


def test_smoke_test_task_type_resolves_via_real_task_routing():
    client.patch("/api/provider-control", json={"model_by_task": {"business": "gpt-5.5"}})
    resp = client.post("/api/providers/smoke-test", json={"task_type": "business", "live": False}).json()
    assert resp["task_type"] == "business"
    assert resp["provider"] in {"openai", "anthropic", "gemini", "mistral", "mock"}


# ------------------------------------------------------------------
# Learned model preference: LearningAgent already computes a real per-task
# "best model" from judge-scored Deep Mode consensus tournaments
# (model_performance.json consensus_candidate records), but that data
# previously dead-ended at a dashboard (GET /learning/report) and never
# reached an actual routing decision. preferred_model_for_task() now falls
# back to it when no manual preference is set.
# ------------------------------------------------------------------
def _isolated_provider_control(tmp_path):
    from app.services.governance_service import GovernanceService
    from app.services.provider_control_service import ProviderControlService
    from app.services.storage_service import StorageService

    storage = StorageService(data_dir=str(tmp_path / "data"))
    return storage, ProviderControlService(storage, GovernanceService(storage))


def _seed_tournament(storage, task_type: str, winners: list[str], losers: list[str]) -> None:
    records = storage.read_list("model_performance.json")
    for model in winners:
        records.append({"record_type": "consensus_candidate", "task_type": task_type, "provider": "anthropic",
                         "model": model, "selected_as_winner": True})
    for model in losers:
        records.append({"record_type": "consensus_candidate", "task_type": task_type, "provider": "openai",
                         "model": model, "selected_as_winner": False})
    storage.write_list("model_performance.json", records)


def test_learned_preference_used_when_no_manual_preference_and_enough_samples(tmp_path):
    storage, pcs = _isolated_provider_control(tmp_path)
    _seed_tournament(storage, "coding", winners=["claude-opus-4-8"] * 3, losers=["gpt-5.5"] * 3)
    assert pcs.preferred_model_for_task("coding") == "claude-opus-4-8"


def test_learned_preference_skipped_below_sample_threshold(tmp_path):
    storage, pcs = _isolated_provider_control(tmp_path)
    _seed_tournament(storage, "coding", winners=["claude-opus-4-8"] * 2, losers=["gpt-5.5"] * 2)
    assert pcs.preferred_model_for_task("coding") is None


def test_manual_preference_always_wins_over_learned_preference(tmp_path):
    storage, pcs = _isolated_provider_control(tmp_path)
    _seed_tournament(storage, "coding", winners=["claude-opus-4-8"] * 5, losers=["gpt-5.5"] * 5)
    pcs.storage.write_list("provider_control.json", [{"config": {"model_by_task": {"coding": "gemini-1.5-pro"}}}])
    assert pcs.preferred_model_for_task("coding") == "gemini-1.5-pro"


def test_learned_preference_scoped_to_its_own_task_type(tmp_path):
    storage, pcs = _isolated_provider_control(tmp_path)
    _seed_tournament(storage, "coding", winners=["claude-opus-4-8"] * 5, losers=[])
    _seed_tournament(storage, "research", winners=["gemini-1.5-pro"] * 5, losers=[])
    assert pcs.preferred_model_for_task("coding") == "claude-opus-4-8"
    assert pcs.preferred_model_for_task("research") == "gemini-1.5-pro"


def test_learned_preference_none_with_no_tournament_data(tmp_path):
    _, pcs = _isolated_provider_control(tmp_path)
    assert pcs.preferred_model_for_task("coding") is None


def test_learned_preference_flows_into_real_router_routing(tmp_path, monkeypatch):
    from app.config import settings
    from app.services.llm_router import llm_router

    storage, pcs = _isolated_provider_control(tmp_path)
    _seed_tournament(storage, "coding", winners=["claude-opus-4-8"] * 5, losers=["gpt-5.5"] * 5)
    monkeypatch.setattr(llm_router, "provider_control", pcs)
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    choice = llm_router.route_for_agent("Coder Agent", task_type="coding")
    assert choice.provider == "anthropic"
    assert choice.model == "claude-opus-4-8"
    assert choice.label == "task:coding"
