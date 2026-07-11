"""Verification layer: master_agent's consensus candidates (real parallel calls
to multiple providers, gated behind deep_mode) had NO content comparison before
this -- summarize_consensus picked "first successful non-fallback candidate"
regardless of what any candidate actually said, and the disagreement notes were
always the same two fallback-count sentences. These tests cover the real
pairwise content-agreement comparison that replaced that."""

from app.agents.master_agent import MasterOrchestratorAgent
from app.models.response_models import AgentOutput


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
