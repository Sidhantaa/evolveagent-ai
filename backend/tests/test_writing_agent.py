from unittest.mock import MagicMock

from app.agents.writing_agent import WritingAgent
from app.models.response_models import AgentOutput
from app.services.llm_router import LLMResult, llm_router


def test_run_final_with_metadata_forwards_workspace_id(monkeypatch):
    """Same gap as the main specialist loop (PR #236): the Writing Agent's
    final-synthesis call is a real LLM call on every request, but previously
    had no way to carry the resolved workspace_id through to LLMRouter's real
    per-call cost recording."""
    agent = WritingAgent()
    generate_spy = MagicMock(return_value=LLMResult(
        output="final answer", provider="mock", model="mock-agent-model", latency_ms=1, success=True,
    ))
    monkeypatch.setattr(llm_router, "generate", generate_spy)
    outputs = [AgentOutput(agent_name="Research Agent", provider="mock", model="m", success=True, output="finding")]
    agent.run_final_with_metadata("do a task", outputs, judge_summary="{}", workspace_id="workspace-final")
    assert generate_spy.call_args.kwargs["workspace_id"] == "workspace-final"


def test_run_final_with_metadata_defaults_workspace_id_to_none(monkeypatch):
    agent = WritingAgent()
    generate_spy = MagicMock(return_value=LLMResult(
        output="final answer", provider="mock", model="mock-agent-model", latency_ms=1, success=True,
    ))
    monkeypatch.setattr(llm_router, "generate", generate_spy)
    outputs = [AgentOutput(agent_name="Research Agent", provider="mock", model="m", success=True, output="finding")]
    agent.run_final_with_metadata("do a task", outputs, judge_summary="{}")
    assert generate_spy.call_args.kwargs["workspace_id"] is None


def test_run_final_still_works_unchanged(monkeypatch):
    agent = WritingAgent()
    monkeypatch.setattr(llm_router, "generate", lambda *a, **kw: LLMResult(
        output="plain final answer", provider="mock", model="mock-agent-model", latency_ms=1, success=True,
    ))
    outputs = [AgentOutput(agent_name="Research Agent", provider="mock", model="m", success=True, output="finding")]
    assert agent.run_final("do a task", outputs, "{}") == "plain final answer"
