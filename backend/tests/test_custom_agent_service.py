from unittest.mock import MagicMock

from app.services.custom_agent_service import CustomAgentService, RuntimeCustomAgent
from app.services.llm_router import LLMResult, llm_router
from app.services.storage_service import StorageService


def _create_agent(storage: StorageService, **overrides) -> dict:
    service = CustomAgentService(storage)
    result = service.create({
        "name": overrides.get("name", "Pref Test Agent"),
        "role": "test",
        "prompt": overrides.get("prompt", "You are a test agent."),
        "model_preference": overrides.get("model_preference", "default"),
        "workspace_id": overrides.get("workspace_id"),
    })
    return service.get(result.agent_id)


# ------------------------------------------------------------------
# model_preference was validated, persisted, and API-exposed but never
# consumed at execution time -- RuntimeCustomAgent now honors it as a
# forced provider route.
# ------------------------------------------------------------------
def test_model_preference_default_resolves_to_none():
    agent = RuntimeCustomAgent({"name": "x", "prompt": "p", "model_preference": "default"})
    assert agent.model_preference is None


def test_model_preference_unset_resolves_to_none():
    agent = RuntimeCustomAgent({"name": "x", "prompt": "p"})
    assert agent.model_preference is None


def test_model_preference_unrecognized_value_resolves_to_none():
    agent = RuntimeCustomAgent({"name": "x", "prompt": "p", "model_preference": "not-a-real-provider"})
    assert agent.model_preference is None


def test_model_preference_claude_resolves_to_anthropic_provider():
    agent = RuntimeCustomAgent({"name": "x", "prompt": "p", "model_preference": "claude"})
    assert agent.model_preference == "anthropic"


def test_model_preference_openai_and_gemini_and_mock_resolve_directly():
    assert RuntimeCustomAgent({"name": "x", "prompt": "p", "model_preference": "openai"}).model_preference == "openai"
    assert RuntimeCustomAgent({"name": "x", "prompt": "p", "model_preference": "gemini"}).model_preference == "gemini"
    assert RuntimeCustomAgent({"name": "x", "prompt": "p", "model_preference": "mock"}).model_preference == "mock"


def test_default_preference_uses_normal_agent_name_routing(monkeypatch):
    agent = RuntimeCustomAgent({"name": "Default Pref Agent", "prompt": "p", "model_preference": "default"})
    generate_spy = MagicMock(return_value=LLMResult(
        output="ok", provider="mock", model="mock-agent-model", latency_ms=1, success=True,
    ))
    generate_for_provider_spy = MagicMock()
    monkeypatch.setattr(llm_router, "generate", generate_spy)
    monkeypatch.setattr(llm_router, "generate_for_provider", generate_for_provider_spy)
    agent.run_with_metadata("do a task")
    generate_spy.assert_called_once()
    generate_for_provider_spy.assert_not_called()


def test_pinned_preference_forces_the_requested_provider(monkeypatch):
    agent = RuntimeCustomAgent({"name": "Gemini Pinned Agent", "prompt": "p", "model_preference": "gemini"})
    generate_spy = MagicMock()
    generate_for_provider_spy = MagicMock(return_value=LLMResult(
        output="ok", provider="gemini", model="gemini-1.5-pro", latency_ms=1, success=True,
    ))
    monkeypatch.setattr(llm_router, "generate", generate_spy)
    monkeypatch.setattr(llm_router, "generate_for_provider", generate_for_provider_spy)
    output = agent.run_with_metadata("do a task")
    generate_spy.assert_not_called()
    generate_for_provider_spy.assert_called_once()
    called_provider = generate_for_provider_spy.call_args[0][0]
    assert called_provider == "gemini"
    assert output.provider == "gemini"


def test_custom_agent_service_run_honors_model_preference_end_to_end(tmp_path, monkeypatch):
    storage = StorageService(data_dir=str(tmp_path))
    agent_record = _create_agent(storage, name="E2E Pref Agent", model_preference="claude")
    generate_for_provider_spy = MagicMock(return_value=LLMResult(
        output="ok", provider="anthropic", model="claude-opus-4-8", latency_ms=1, success=True,
    ))
    monkeypatch.setattr(llm_router, "generate_for_provider", generate_for_provider_spy)
    service = CustomAgentService(storage)
    output, config = service.run(agent_record["agent_id"], "Explain the deployment plan.")
    assert config["model_preference"] == "claude"
    generate_for_provider_spy.assert_called_once()
    assert generate_for_provider_spy.call_args[0][0] == "anthropic"
    assert output.provider == "anthropic"


def test_custom_agent_service_run_with_default_preference_unaffected(tmp_path, monkeypatch):
    storage = StorageService(data_dir=str(tmp_path))
    agent_record = _create_agent(storage, name="E2E Default Agent", model_preference="default")
    generate_spy = MagicMock(return_value=LLMResult(
        output="ok", provider="mock", model="mock-agent-model", latency_ms=1, success=True,
    ))
    monkeypatch.setattr(llm_router, "generate", generate_spy)
    service = CustomAgentService(storage)
    output, config = service.run(agent_record["agent_id"], "Explain the deployment plan.")
    assert config["model_preference"] == "default"
    generate_spy.assert_called_once()
    assert output.success is True


# ------------------------------------------------------------------
# A custom agent already carries its own real workspace_id (set at creation)
# but it never reached LLMRouter's real per-call cost recording (PR #234) --
# every custom-agent run recorded cost against "default" regardless of which
# workspace actually owned the agent.
# ------------------------------------------------------------------
def test_custom_agent_forwards_its_own_workspace_id_with_default_preference(tmp_path, monkeypatch):
    storage = StorageService(data_dir=str(tmp_path))
    agent_record = _create_agent(storage, name="WS Default Agent", model_preference="default", workspace_id="ws-abc")
    generate_spy = MagicMock(return_value=LLMResult(
        output="ok", provider="mock", model="mock-agent-model", latency_ms=1, success=True,
    ))
    monkeypatch.setattr(llm_router, "generate", generate_spy)
    service = CustomAgentService(storage)
    service.run(agent_record["agent_id"], "Explain the deployment plan.")
    assert generate_spy.call_args.kwargs["workspace_id"] == "ws-abc"


def test_custom_agent_forwards_its_own_workspace_id_with_pinned_preference(tmp_path, monkeypatch):
    storage = StorageService(data_dir=str(tmp_path))
    agent_record = _create_agent(storage, name="WS Pinned Agent", model_preference="claude", workspace_id="ws-xyz")
    generate_for_provider_spy = MagicMock(return_value=LLMResult(
        output="ok", provider="anthropic", model="claude-opus-4-8", latency_ms=1, success=True,
    ))
    monkeypatch.setattr(llm_router, "generate_for_provider", generate_for_provider_spy)
    service = CustomAgentService(storage)
    service.run(agent_record["agent_id"], "Explain the deployment plan.")
    assert generate_for_provider_spy.call_args.kwargs["workspace_id"] == "ws-xyz"


def test_custom_agent_without_workspace_id_forwards_none(tmp_path, monkeypatch):
    storage = StorageService(data_dir=str(tmp_path))
    agent_record = _create_agent(storage, name="No WS Agent", model_preference="default")
    generate_spy = MagicMock(return_value=LLMResult(
        output="ok", provider="mock", model="mock-agent-model", latency_ms=1, success=True,
    ))
    monkeypatch.setattr(llm_router, "generate", generate_spy)
    service = CustomAgentService(storage)
    service.run(agent_record["agent_id"], "Explain the deployment plan.")
    assert generate_spy.call_args.kwargs["workspace_id"] is None
