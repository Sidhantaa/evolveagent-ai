from pathlib import Path

from app.services.debate_simulation_service import DebateSimulationService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


def make_service(tmp_path: Path) -> DebateSimulationService:
    storage = StorageService(str(tmp_path / "data"))
    return DebateSimulationService(storage=storage, governance_service=GovernanceService(storage))


def test_create_debate_returns_agent_turns_and_consensus(tmp_path: Path):
    service = make_service(tmp_path)
    debate = service.create_debate("Should we add simulation mode before autopilot?")

    assert debate["debate_id"]
    assert len(debate["turns"]) >= 4
    assert debate["consensus"]["selected_agent"]
    assert debate["audit_log"]


def test_debate_redacts_secret_like_input(tmp_path: Path):
    service = make_service(tmp_path)
    debate = service.create_debate("Compare plans using OPENAI_API_KEY=sk-secretvalue")

    assert "[REDACTED_SECRET]" in debate["prompt"]
    assert debate["secret_scan"]["secrets_detected"] is True


def test_consensus_updates_existing_debate(tmp_path: Path):
    service = make_service(tmp_path)
    debate = service.create_debate("Pick the best implementation plan")
    result = service.consensus_for(debate["debate_id"])

    assert result["success"] is True
    assert result["consensus"]["confidence"] >= 80


def test_create_simulation_has_no_side_effects(tmp_path: Path):
    service = make_service(tmp_path)
    simulation = service.create_simulation("What if we run this workflow automatically?")

    assert simulation["simulation_id"]
    assert simulation["side_effects"] == []
    assert len(simulation["outcomes"]) == 3
    assert simulation["recommendation"]["decision"] == "proceed_with_controls"


def test_summary_counts_debates_and_simulations(tmp_path: Path):
    service = make_service(tmp_path)
    service.create_debate("Debate this")
    service.create_simulation("Simulate this")

    summary = service.summary()

    assert summary["total_debates"] == 1
    assert summary["total_simulations"] == 1
