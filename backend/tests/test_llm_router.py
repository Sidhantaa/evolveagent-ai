from app.config import settings
from app.services.governance_service import GovernanceService
from app.services.llm_router import LLMRouter, RouteChoice, llm_router
from app.services.provider_control_service import ProviderControlService
from app.services.storage_service import StorageService
from app.services.usage_ledger_service import UsageLedgerService


def _isolated_provider_control(tmp_path) -> ProviderControlService:
    storage = StorageService(data_dir=str(tmp_path / "data"))
    return ProviderControlService(storage, GovernanceService(storage))


def _isolated_usage_ledger(tmp_path) -> UsageLedgerService:
    storage = StorageService(data_dir=str(tmp_path / "usage-data"))
    return UsageLedgerService(storage, GovernanceService(storage))


class _StaticProvider:
    def __init__(self, output: str = "provider ok"):
        self.output = output

    def generate(self, system_prompt: str, user_prompt: str, model: str | None = None) -> str:
        return self.output


class _BrokenUsageLedger:
    def record_usage(self, data: dict) -> dict:
        raise RuntimeError("ledger unavailable")


def test_real_mode_openai_failure_falls_back_to_mock(monkeypatch):
    monkeypatch.setattr(settings, "llm_mode", "real")
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "mistral_api_key", None)

    result = llm_router.generate_for_provider(
        "openai",
        settings.openai_reasoning_model,
        "You are a test agent.",
        "Return a short test response.",
    )

    assert result.provider == "mock"
    assert result.model == "mock-agent-model"
    assert result.fallback_used is True
    assert result.success is True


def test_real_mode_provider_status_with_openai_key(monkeypatch):
    monkeypatch.setattr(settings, "llm_mode", "real")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "mistral_api_key", None)
    monkeypatch.setattr(settings, "default_provider", "openai")

    status = llm_router.status()

    assert status.llm_mode == "real"
    assert status.openai_configured is True
    assert status.default_provider == "openai"
    assert status.available_providers == ["openai", "mock"]


def test_real_mode_provider_status_lists_configured_consensus_providers(monkeypatch):
    monkeypatch.setattr(settings, "llm_mode", "real")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "anthropic_api_key", "test-anthropic-key")
    monkeypatch.setattr(settings, "gemini_api_key", "test-gemini-key")
    monkeypatch.setattr(settings, "mistral_api_key", "test-mistral-key")
    monkeypatch.setattr(settings, "default_provider", "openai")

    status = llm_router.status()

    assert status.openai_configured is True
    assert status.anthropic_configured is True
    assert status.gemini_configured is True
    assert status.mistral_configured is True
    assert status.available_providers == ["openai", "anthropic", "gemini", "mistral", "mock"]


def test_consensus_routes_use_available_real_providers(monkeypatch):
    monkeypatch.setattr(settings, "llm_mode", "real")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "anthropic_api_key", "test-anthropic-key")
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "mistral_api_key", None)
    monkeypatch.setattr(settings, "openai_text_model", "gpt-4o-mini")
    monkeypatch.setattr(settings, "anthropic_model", "claude-3-5-sonnet-latest")

    routes = llm_router.consensus_routes()

    assert [(route.provider, route.model) for route in routes] == [
        ("openai", "gpt-4o-mini"),
        ("anthropic", "claude-3-5-sonnet-latest"),
    ]


def test_consensus_routes_add_mock_comparison_when_only_one_real_provider(monkeypatch):
    monkeypatch.setattr(settings, "llm_mode", "real")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "mistral_api_key", None)

    routes = llm_router.consensus_routes()

    assert [route.provider for route in routes] == ["openai", "mock"]


def test_mock_consensus_keeps_three_demo_candidates(monkeypatch):
    monkeypatch.setattr(settings, "llm_mode", "mock")

    routes = llm_router.consensus_routes()

    assert [route.provider for route in routes] == ["openai", "anthropic", "gemini"]


def test_v13_routes_text_agents_to_openai_only(monkeypatch):
    monkeypatch.setattr(settings, "llm_mode", "real")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "anthropic_api_key", "test-anthropic-key")
    monkeypatch.setattr(settings, "gemini_api_key", "test-gemini-key")
    monkeypatch.setattr(settings, "mistral_api_key", "test-mistral-key")
    monkeypatch.setattr(settings, "default_provider", "openai")
    monkeypatch.setattr(settings, "openai_text_model", "gpt-4o-mini")

    for agent_name in ["Research Agent", "Risk Agent", "Writing Agent", "Judge Agent"]:
        route = llm_router.route_for_agent(agent_name)
        assert route.provider == "openai"
        assert route.model == "gpt-4o-mini"


# ------------------------------------------------------------------
# Task-based routing: ProviderControlService.model_by_task previously had a
# real UI + real validation but ZERO effect on which provider/model any agent
# actually used. These tests wire it into route_for_agent for the first time.
# ------------------------------------------------------------------
def test_task_type_preference_routes_to_configured_provider_model(tmp_path, monkeypatch):
    pcs = _isolated_provider_control(tmp_path)
    pcs.update({"coding": "claude-opus-4-8"}, None, None)
    monkeypatch.setattr(llm_router, "provider_control", pcs)
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")

    route = llm_router.route_for_agent("Coding Agent", task_type="coding")

    assert route.provider == "anthropic"
    assert route.model == "claude-opus-4-8"
    assert route.label == "task:coding"


def test_task_type_preference_skipped_when_provider_not_configured(tmp_path, monkeypatch):
    pcs = _isolated_provider_control(tmp_path)
    pcs.update({"coding": "claude-opus-4-8"}, None, None)
    monkeypatch.setattr(llm_router, "provider_control", pcs)
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    monkeypatch.setattr(settings, "default_provider", "openai")

    route = llm_router.route_for_agent("Coding Agent", task_type="coding")

    assert route.provider == "openai"


def test_task_type_preference_with_unrecognized_model_string_falls_back(tmp_path, monkeypatch):
    pcs = _isolated_provider_control(tmp_path)
    pcs.update({"coding": "some-unknown-model-xyz"}, None, None)
    monkeypatch.setattr(llm_router, "provider_control", pcs)
    monkeypatch.setattr(settings, "default_provider", "openai")

    route = llm_router.route_for_agent("Coding Agent", task_type="coding")

    assert route.provider == "openai"


def test_no_task_type_keeps_default_behavior_even_when_provider_control_wired(tmp_path, monkeypatch):
    pcs = _isolated_provider_control(tmp_path)
    pcs.update({"coding": "claude-opus-4-8"}, None, None)
    monkeypatch.setattr(llm_router, "provider_control", pcs)
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")
    monkeypatch.setattr(settings, "default_provider", "openai")
    monkeypatch.setattr(settings, "openai_text_model", "gpt-4o-mini")

    route = llm_router.route_for_agent("Coding Agent")  # no task_type passed

    assert route.provider == "openai"
    assert route.model == "gpt-4o-mini"


# ------------------------------------------------------------------
# Quality tiers: openai_master_model / openai_cheap_model / anthropic_strong_model
# etc. were already declared in Settings but had zero real callers before this.
# ------------------------------------------------------------------
def test_quality_tier_resolves_previously_unused_settings_fields(monkeypatch):
    monkeypatch.setattr(settings, "default_provider", "openai")
    monkeypatch.setattr(settings, "openai_cheap_model", "gpt-5.4-mini")
    monkeypatch.setattr(settings, "openai_master_model", "gpt-5.5")
    monkeypatch.setattr(settings, "openai_text_model", "gpt-4o-mini")

    assert llm_router.route_for_agent("Any Agent", quality="fast").model == "gpt-5.4-mini"
    assert llm_router.route_for_agent("Any Agent", quality="quality").model == "gpt-5.5"
    assert llm_router.route_for_agent("Any Agent").model == "gpt-4o-mini"  # default "balanced" unchanged


# ------------------------------------------------------------------
# Real provider health/observability -- previously no call outcome was ever
# recorded anywhere.
# ------------------------------------------------------------------
def test_provider_health_aggregates_recorded_calls(tmp_path, monkeypatch):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    monkeypatch.setattr(llm_router, "storage", storage)
    monkeypatch.setattr(settings, "llm_mode", "mock")

    llm_router.generate("Agent A", "sys", "hi")
    llm_router.generate("Agent B", "sys", "hi")

    health = llm_router.provider_health()

    assert health["available"] is True
    assert health["total_calls"] == 2
    mock_stats = next(p for p in health["providers"] if p["provider"] == "mock")
    assert mock_stats["calls"] == 2
    assert mock_stats["success_rate"] == 100


def test_provider_health_unavailable_when_storage_not_wired(monkeypatch):
    monkeypatch.setattr(llm_router, "storage", None)

    health = llm_router.provider_health()

    assert health["available"] is False
    assert health["providers"] == []


# ------------------------------------------------------------------
# Real per-call cost tracking: UsageLedgerService existed, but no real LLM
# execution path recorded estimated usage until LLMRouter wired it here.
# ------------------------------------------------------------------
def test_llm_router_records_real_usage_for_successful_call(tmp_path, monkeypatch):
    ledger = _isolated_usage_ledger(tmp_path)
    router = LLMRouter(usage_ledger=ledger)
    router.providers["openai"] = _StaticProvider("real response")
    monkeypatch.setattr(settings, "llm_mode", "real")

    result = router.generate_with_route(
        RouteChoice("openai", "gpt-test"),
        "system",
        "user",
        workspace_id="workspace-cost-a",
    )

    entries = ledger.list_entries("workspace-cost-a")
    assert result.output == "real response"
    assert result.provider == "openai"
    assert len(entries) == 1
    assert entries[0]["workspace_id"] == "workspace-cost-a"
    assert entries[0]["capability"] == "text"
    assert entries[0]["units"] == 1
    assert entries[0]["mode"] == "real"
    assert entries[0]["estimated_cost"] > 0


def test_llm_router_records_mock_usage_for_default_workspace(tmp_path, monkeypatch):
    ledger = _isolated_usage_ledger(tmp_path)
    router = LLMRouter(usage_ledger=ledger)
    monkeypatch.setattr(settings, "llm_mode", "mock")

    result = router.generate("Any Agent", "system", "user")

    entries = ledger.list_entries("default")
    assert result.provider == "mock"
    assert len(entries) == 1
    assert entries[0]["workspace_id"] == "default"
    assert entries[0]["mode"] == "mock"


def test_llm_router_ledger_failure_never_breaks_generation(monkeypatch):
    router = LLMRouter(usage_ledger=_BrokenUsageLedger())
    router.providers["openai"] = _StaticProvider("still works")
    monkeypatch.setattr(settings, "llm_mode", "real")

    result = router.generate_with_route(RouteChoice("openai", "gpt-test"), "system", "user")

    assert result.success is True
    assert result.output == "still works"
    assert result.provider == "openai"


def test_llm_router_without_usage_ledger_keeps_existing_behavior(monkeypatch):
    router = LLMRouter()
    router.providers["openai"] = _StaticProvider("unchanged")
    monkeypatch.setattr(settings, "llm_mode", "real")

    result = router.generate_with_route(RouteChoice("openai", "gpt-test"), "system", "user")

    assert result.success is True
    assert result.output == "unchanged"
    assert result.provider == "openai"


def test_usage_ledger_analytics_moves_after_router_call(tmp_path, monkeypatch):
    ledger = _isolated_usage_ledger(tmp_path)
    router = LLMRouter(usage_ledger=ledger)
    router.providers["openai"] = _StaticProvider("tracked")
    monkeypatch.setattr(settings, "llm_mode", "real")

    before = ledger.analytics_summary()
    router.generate_with_route(RouteChoice("openai", "gpt-test"), "system", "user", workspace_id="analytics-workspace")
    after = ledger.analytics_summary()

    assert after["usage_entries"] == before["usage_entries"] + 1
    assert after["usage_total_estimated_cost"] > before["usage_total_estimated_cost"]
