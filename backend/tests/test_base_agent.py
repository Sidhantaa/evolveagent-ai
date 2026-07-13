from unittest.mock import MagicMock

from app.agents.base_agent import BaseAgent
from app.services.llm_router import LLMResult, llm_router


def test_run_with_metadata_forwards_workspace_id_to_llm_router(monkeypatch):
    """workspace_id was resolved everywhere real callers already needed it
    (memory, digital twin, tool routing) but never reached LLMRouter's real
    per-call cost recording -- every real call recorded against "default"
    no matter which workspace actually made it."""
    agent = BaseAgent()
    generate_spy = MagicMock(return_value=LLMResult(
        output="ok", provider="mock", model="mock-agent-model", latency_ms=1, success=True,
    ))
    monkeypatch.setattr(llm_router, "generate", generate_spy)
    agent.run_with_metadata("do a task", workspace_id="workspace-123")
    generate_spy.assert_called_once()
    assert generate_spy.call_args.kwargs["workspace_id"] == "workspace-123"


def test_run_with_metadata_defaults_workspace_id_to_none(monkeypatch):
    agent = BaseAgent()
    generate_spy = MagicMock(return_value=LLMResult(
        output="ok", provider="mock", model="mock-agent-model", latency_ms=1, success=True,
    ))
    monkeypatch.setattr(llm_router, "generate", generate_spy)
    agent.run_with_metadata("do a task")
    assert generate_spy.call_args.kwargs["workspace_id"] is None


def test_run_still_works_unchanged(monkeypatch):
    """The plain run() convenience method (no workspace_id param) must keep
    working exactly as before -- backward compatible."""
    agent = BaseAgent()
    monkeypatch.setattr(llm_router, "generate", lambda *a, **kw: LLMResult(
        output="plain result", provider="mock", model="mock-agent-model", latency_ms=1, success=True,
    ))
    assert agent.run("do a task") == "plain result"
