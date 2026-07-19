"""Verification layer: master_agent's consensus candidates (real parallel calls
to multiple providers, gated behind deep_mode) had NO content comparison before
this -- summarize_consensus picked "first successful non-fallback candidate"
regardless of what any candidate actually said, and the disagreement notes were
always the same two fallback-count sentences. These tests cover the real
pairwise content-agreement comparison that replaced that."""

import threading
import time

from app.agents.master_agent import MasterOrchestratorAgent
from app.config import settings
from app.models.response_models import AgentOutput
from app.services.llm_router import LLMRouter, RouteChoice, llm_router
from app.services.storage_service import StorageService


def _candidate(name: str, output: str, success: bool = True, fallback_used: bool = False) -> AgentOutput:
    return AgentOutput(agent_name=name, provider="mock", model="mock-agent-model",
                        success=success, fallback_used=fallback_used, output=output)


def test_no_candidates_returns_empty():
    winner, reason, notes = MasterOrchestratorAgent.summarize_consensus([])
    assert winner is None and reason is None and notes == []


def test_single_candidate_is_winner_without_comparison():
    candidates = [_candidate("Solo Candidate", "The answer is 42.")]
    winner, reason, notes = MasterOrchestratorAgent.summarize_consensus(candidates)
    assert winner == "Solo Candidate"
    assert any("only one real candidate" in note.lower() for note in notes)


def test_agreeing_candidates_flagged_as_reasonable_agreement():
    shared_text = "The project roadmap includes authentication database deployment testing monitoring rollback"
    candidates = [
        _candidate("Candidate A", shared_text),
        _candidate("Candidate B", shared_text),
    ]
    winner, reason, notes = MasterOrchestratorAgent.summarize_consensus(candidates)
    assert winner in {"Candidate A", "Candidate B"}
    assert any("reasonable content agreement" in note.lower() for note in notes)


def test_disagreeing_candidates_flagged_as_low_agreement():
    candidates = [
        _candidate("Candidate A", "The project roadmap includes authentication database deployment"),
        _candidate("Candidate B", "Weather forecasts predict rainfall temperature humidity wind"),
    ]
    winner, reason, notes = MasterOrchestratorAgent.summarize_consensus(candidates)
    assert any("low agreement" in note.lower() for note in notes)
    assert any("review before trusting" in note.lower() for note in notes)


def test_winner_is_most_representative_not_just_first():
    # Candidate A is an outlier; B and C agree closely -- the winner should be
    # whichever of B/C has the higher average agreement, never simply "first".
    outlier = _candidate("Outlier", "Completely unrelated content about gardening tomatoes soil")
    agree_text = "The migration plan covers schema changes rollback verification monitoring alerts"
    agreeing_1 = _candidate("Agreeing One", agree_text)
    agreeing_2 = _candidate("Agreeing Two", agree_text + " additional detail here")
    winner, _, _ = MasterOrchestratorAgent.summarize_consensus([outlier, agreeing_1, agreeing_2])
    assert winner in {"Agreeing One", "Agreeing Two"}


def test_fallback_candidates_excluded_from_primary_pool():
    real = _candidate("Real Candidate", "A genuine successful answer with real content here")
    fallback = _candidate("Fallback Candidate", "mock output", fallback_used=True)
    winner, reason, notes = MasterOrchestratorAgent.summarize_consensus([real, fallback])
    assert winner == "Real Candidate"
    assert any("fallback" in note.lower() for note in notes)


def test_content_agreement_is_symmetric_and_bounded():
    score_ab = MasterOrchestratorAgent._content_agreement("shared words here database", "shared words here migration")
    score_ba = MasterOrchestratorAgent._content_agreement("shared words here migration", "shared words here database")
    assert score_ab == score_ba
    assert 0.0 <= score_ab <= 1.0
    assert MasterOrchestratorAgent._content_agreement("", "anything") == 0.0


# ------------------------------------------------------------------
# v280 target 1: run_consensus_candidates() now calls each provider
# concurrently (a thread pool) instead of one at a time -- each call is
# genuinely independent (same system_prompt/user_prompt built once, before
# any call runs; no candidate reads another's output, unlike the main
# specialist loop), so this must be a pure latency win with byte-identical
# output versus the old sequential version.
# ------------------------------------------------------------------
class _TimedProvider:
    """A stub provider with a controllable delay, so the fastest candidate
    finishes first in wall-clock time -- proves the returned list order still
    matches route submission order, not completion order."""

    def __init__(self, output: str, delay: float = 0.0):
        self.output = output
        self.delay = delay

    def generate(self, system_prompt: str, user_prompt: str, model: str | None = None) -> str:
        time.sleep(self.delay)
        return self.output


def test_consensus_candidates_preserve_route_order_despite_different_completion_times(monkeypatch):
    monkeypatch.setattr(settings, "llm_mode", "real")
    monkeypatch.setattr(llm_router, "storage", None)
    # Slowest candidate is submitted FIRST -- if the result were ordered by
    # completion time instead of submission order, this candidate would land
    # last instead of first.
    monkeypatch.setitem(llm_router.providers, "openai", _TimedProvider("OPENAI-OUTPUT", delay=0.3))
    monkeypatch.setitem(llm_router.providers, "anthropic", _TimedProvider("ANTHROPIC-OUTPUT", delay=0.05))
    monkeypatch.setitem(llm_router.providers, "gemini", _TimedProvider("GEMINI-OUTPUT", delay=0.15))
    monkeypatch.setattr(llm_router, "consensus_routes", lambda: [
        RouteChoice("openai", "gpt-test", "OpenAI"),
        RouteChoice("anthropic", "claude-test", "Claude"),
        RouteChoice("gemini", "gemini-test", "Gemini"),
    ])

    outputs = MasterOrchestratorAgent.run_consensus_candidates("do the task", "some context")

    assert [o.output for o in outputs] == ["OPENAI-OUTPUT", "ANTHROPIC-OUTPUT", "GEMINI-OUTPUT"]
    assert [o.provider for o in outputs] == ["openai", "anthropic", "gemini"]
    assert all(o.success for o in outputs)


def test_consensus_candidates_run_concurrently_not_sequentially(monkeypatch):
    """Deterministic, non-timing-based proof the 3 calls genuinely overlap:
    each provider blocks on a shared 3-party barrier before returning. If
    execution were secretly sequential (e.g. a bug that submits to the
    executor but immediately awaits each future one at a time instead of
    submitting all first), only one thread would ever reach the barrier and
    this test would hang until the barrier's timeout and raise
    BrokenBarrierError instead of passing. A wall-clock threshold would work
    too but is flaky under real machine load; this isn't."""
    barrier = threading.Barrier(3, timeout=5)

    class _BarrierProvider:
        def __init__(self, output: str):
            self.output = output

        def generate(self, system_prompt: str, user_prompt: str, model: str | None = None) -> str:
            barrier.wait()  # only returns once all 3 threads have reached this point
            return self.output

    monkeypatch.setattr(settings, "llm_mode", "real")
    monkeypatch.setattr(llm_router, "storage", None)
    monkeypatch.setitem(llm_router.providers, "openai", _BarrierProvider("A"))
    monkeypatch.setitem(llm_router.providers, "anthropic", _BarrierProvider("B"))
    monkeypatch.setitem(llm_router.providers, "gemini", _BarrierProvider("C"))
    monkeypatch.setattr(llm_router, "consensus_routes", lambda: [
        RouteChoice("openai", "gpt-test", "OpenAI"),
        RouteChoice("anthropic", "claude-test", "Claude"),
        RouteChoice("gemini", "gemini-test", "Gemini"),
    ])

    outputs = MasterOrchestratorAgent.run_consensus_candidates("do the task", "some context")

    assert [o.output for o in outputs] == ["A", "B", "C"]


class _RaisingProvider:
    def generate(self, system_prompt: str, user_prompt: str, model: str | None = None) -> str:
        raise RuntimeError("simulated provider outage")


def test_consensus_candidates_isolate_a_single_provider_failure(monkeypatch):
    """One candidate's provider raising must not lose the others' real
    results -- generate_with_route already catches provider exceptions
    internally and falls back to a mock LLMResult (success=True,
    fallback_used=True), so this must hold true when run concurrently too."""
    monkeypatch.setattr(settings, "llm_mode", "real")
    monkeypatch.setattr(llm_router, "storage", None)
    monkeypatch.setitem(llm_router.providers, "openai", _TimedProvider("OPENAI-OK"))
    monkeypatch.setitem(llm_router.providers, "anthropic", _RaisingProvider())
    monkeypatch.setitem(llm_router.providers, "gemini", _TimedProvider("GEMINI-OK"))
    monkeypatch.setattr(llm_router, "fallback_routes", lambda original_provider: [])  # isolate the failure, no fallback chain
    monkeypatch.setattr(llm_router, "consensus_routes", lambda: [
        RouteChoice("openai", "gpt-test", "OpenAI"),
        RouteChoice("anthropic", "claude-test", "Claude"),
        RouteChoice("gemini", "gemini-test", "Gemini"),
    ])

    outputs = MasterOrchestratorAgent.run_consensus_candidates("do the task", "some context")

    assert len(outputs) == 3  # the failing candidate must not lose the other two
    assert outputs[0].output == "OPENAI-OK"
    assert outputs[2].output == "GEMINI-OK"
    assert outputs[1].success is True  # generate_with_route degrades to mock, not a raised exception
    assert outputs[1].fallback_used is True


def test_record_call_does_not_lose_a_concurrent_sibling_call(tmp_path):
    """The concurrency lens this session's core finding, applied here: v280
    made multiple generate_with_route() calls happen concurrently, each
    internally calling _record_call(). The OLD read_list() + write_list()
    pair (two separate lock acquisitions) would lose a sibling call's record
    landing in the gap between them -- proven directly with real concurrent
    threads against real storage."""
    storage = StorageService(data_dir=str(tmp_path / "data"))
    router = LLMRouter()
    router.storage = storage

    threads = [
        threading.Thread(target=router._record_call, args=("openai", f"model-{i}", True, 10, None))
        for i in range(20)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    rows = storage.read_list(router._calls_file)
    assert len(rows) == 20  # every concurrent call's record must survive


def test_record_call_still_caps_at_max_records_under_concurrency(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    router = LLMRouter()
    router.storage = storage
    router._MAX_CALL_RECORDS = 10

    threads = [
        threading.Thread(target=router._record_call, args=("openai", f"model-{i}", True, 10, None))
        for i in range(25)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    rows = storage.read_list(router._calls_file)
    assert len(rows) == 10  # still capped, not unbounded, even under concurrency
