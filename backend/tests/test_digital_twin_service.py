from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.agents.master_agent import MasterOrchestratorAgent
from app.agents.memory_agent import MemoryAgent
from app.main import app
from app.models.request_models import RunRequest
from app.services.digital_twin_service import DigitalTwinService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

client = TestClient(app)


def test_digital_twin_profile_derives_work_style(tmp_path):
    storage = StorageService(data_dir=str(tmp_path))
    workspace = MagicMock()
    workspace.resolve_workspace_id.return_value = "workspace-1"
    service = DigitalTwinService(storage, workspace, GovernanceService(storage))

    storage.write_list(
        "user_preferences.json",
        [
            {
                "workspace_id": "workspace-1",
                "preference": "concise",
                "score": 3,
                "evidence": ["Helpful feedback on a short answer."],
            },
            {
                "workspace_id": "workspace-1",
                "preference": "prefers_step_by_step",
                "score": 2,
                "evidence": ["Positive feedback on numbered steps."],
            },
            {
                "workspace_id": "workspace-1",
                "preference": "technical",
                "score": 2,
                "evidence": ["Positive feedback on a coding response."],
            },
        ],
    )
    storage.write_list(
        "agent_analytics.json",
        [
            {"workspace_id": "workspace-1", "task_type": "coding", "overall_judge_score": 84},
            {"workspace_id": "workspace-1", "task_type": "coding", "overall_judge_score": 88},
        ],
    )
    storage.write_list("feedback.json", [{"workspace_id": "workspace-1", "rating": "helpful"}])

    profile = service.refresh_profile("workspace-1")

    assert profile["workspace_id"] == "workspace-1"
    assert profile["style_profile"]["detail_level"] == "concise"
    assert profile["style_profile"]["technical_level"] == "technical"
    assert profile["style_profile"]["format"] == "step_by_step"
    assert profile["quality_summary"]["average_judge_score"] == 86
    assert profile["feedback_summary"]["helpful"] == 1
    assert profile["recommendations"]
    assert "does not train" in profile["safety_note"]


def test_digital_twin_manual_override_is_persisted(tmp_path):
    storage = StorageService(data_dir=str(tmp_path))
    workspace = MagicMock()
    workspace.resolve_workspace_id.return_value = "workspace-1"
    service = DigitalTwinService(storage, workspace, GovernanceService(storage))

    updated = service.update_profile(
        "workspace-1",
        {"detail_level": "detailed", "tone": "direct", "notes": "Prefer implementation steps."},
    )
    loaded = service.get_profile("workspace-1")

    assert updated["style_profile"]["detail_level"] == "detailed"
    assert loaded["manual_overrides"]["notes"] == "Prefer implementation steps."


def test_digital_twin_api_profile_refresh_and_update():
    workspace_response = client.post(
        "/api/workspaces",
        json={"name": "Digital Twin Test Workspace", "description": "Profile test"},
    )
    assert workspace_response.status_code == 200
    workspace_id = workspace_response.json()["workspace_id"]

    refresh_response = client.post(f"/api/digital-twin/profile/refresh?workspace_id={workspace_id}")
    assert refresh_response.status_code == 200
    profile = refresh_response.json()
    assert profile["workspace_id"] == workspace_id
    assert profile["style_profile"]

    update_response = client.patch(
        "/api/digital-twin/profile",
        json={
            "workspace_id": workspace_id,
            "detail_level": "concise",
            "format": "bullets",
            "tone": "practical",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["style_profile"]["detail_level"] == "concise"
    assert updated["style_profile"]["format"] == "bullets"
    assert updated["style_profile"]["tone"] == "practical"

    get_response = client.get(f"/api/digital-twin/profile?workspace_id={workspace_id}")
    assert get_response.status_code == 200
    assert get_response.json()["manual_overrides"]["detail_level"] == "concise"


def test_digital_twin_export_reset_and_delete_privacy_controls():
    workspace_response = client.post(
        "/api/workspaces",
        json={"name": "Twin Privacy Workspace", "description": "Privacy controls"},
    )
    workspace_id = workspace_response.json()["workspace_id"]

    client.patch(
        "/api/digital-twin/profile",
        json={"workspace_id": workspace_id, "detail_level": "detailed", "notes": "remember me"},
    )

    # Export returns the full profile in a portable wrapper.
    export_response = client.get(f"/api/digital-twin/profile/export?workspace_id={workspace_id}")
    assert export_response.status_code == 200
    exported = export_response.json()
    assert exported["workspace_id"] == workspace_id
    assert exported["format"] == "evolveagent.digital_twin.v1"
    assert exported["profile"]["manual_overrides"]["notes"] == "remember me"

    # Reset clears manual overrides and re-derives a fresh profile.
    reset_response = client.post(f"/api/digital-twin/profile/reset?workspace_id={workspace_id}")
    assert reset_response.status_code == 200
    assert reset_response.json()["manual_overrides"] == {}

    # Re-add an override so we can confirm delete removes stored data.
    client.patch(
        "/api/digital-twin/profile",
        json={"workspace_id": workspace_id, "tone": "warm"},
    )
    delete_response = client.delete(f"/api/digital-twin/profile?workspace_id={workspace_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"workspace_id": workspace_id, "deleted": True}

    # Deleting again is a no-op (nothing left to remove).
    second_delete = client.delete(f"/api/digital-twin/profile?workspace_id={workspace_id}")
    assert second_delete.json()["deleted"] is False


# ------------------------------------------------------------------
# MasterOrchestratorAgent wiring: the real derived style profile (previously
# never consulted by any agent run) is now folded into shared_context on
# every run -- read-only, best-effort, never blocks or fails a run.
# ------------------------------------------------------------------
def test_master_agent_run_consults_and_creates_a_real_digital_twin_profile(tmp_path):
    storage = StorageService(data_dir=str(tmp_path))
    agent = MasterOrchestratorAgent(storage=storage, memory_agent=MemoryAgent(storage))
    workspace_id = agent.workspace.resolve_workspace_id(None)

    # Seed a strong, unambiguous preference signal BEFORE the run.
    storage.write_list("user_preferences.json", [
        {"workspace_id": workspace_id, "preference": "concise", "score": 5, "evidence": ["short answers preferred"]},
    ])

    # No profile exists yet -- get_profile() during run() must lazily create one.
    assert storage.read_list("digital_twin_profiles.json") == []
    response = agent.run(RunRequest(user_input="Explain how EvolveAgent AI works."))
    assert response.run_id
    assert isinstance(response.final_output, str) and response.final_output

    profiles = storage.read_list("digital_twin_profiles.json")
    assert len(profiles) == 1
    assert profiles[0]["workspace_id"] == workspace_id
    assert profiles[0]["style_profile"]["detail_level"] == "concise"


def test_master_agent_run_degrades_safely_with_no_preference_history(tmp_path):
    storage = StorageService(data_dir=str(tmp_path))
    agent = MasterOrchestratorAgent(storage=storage, memory_agent=MemoryAgent(storage))
    response = agent.run(RunRequest(user_input="Explain how EvolveAgent AI works."))
    assert response.run_id
    assert isinstance(response.final_output, str) and response.final_output
    # A default (balanced/adaptive/mixed) profile is still created -- the run
    # never fails or is left without a profile just because there's no history.
    assert len(storage.read_list("digital_twin_profiles.json")) == 1


def test_master_agent_run_survives_a_broken_digital_twin_collaborator(tmp_path, monkeypatch):
    storage = StorageService(data_dir=str(tmp_path))
    agent = MasterOrchestratorAgent(storage=storage, memory_agent=MemoryAgent(storage))

    def _boom(*args, **kwargs):
        raise RuntimeError("digital twin storage unavailable")

    monkeypatch.setattr(agent.digital_twin, "get_profile", _boom)
    response = agent.run(RunRequest(user_input="Explain how EvolveAgent AI works."))
    assert response.run_id
    assert isinstance(response.final_output, str) and response.final_output


def test_master_agent_specialist_loop_forwards_resolved_workspace_id_to_llm_router(tmp_path, monkeypatch):
    """workspace_id was already resolved and used for memory/digital-twin/tool
    routing on every real run, but never reached LLMRouter's real per-call
    cost recording (PR #234) -- the main specialist loop (4 real agents:
    Research/Logic/Risk/Strategy) is the highest-value real call site fixed
    here. Other agent-output methods elsewhere in run() (writer, judge,
    evolution, etc.) are a deliberately separate, out-of-scope follow-up --
    this test checks the specialist loop specifically, not every LLM call in
    a full run."""
    from app.services.llm_router import LLMResult, llm_router

    storage = StorageService(data_dir=str(tmp_path))
    agent = MasterOrchestratorAgent(storage=storage, memory_agent=MemoryAgent(storage))
    workspace = agent.workspace.create_workspace({"name": "Cost Tracking Test Workspace"})
    workspace_id = workspace["workspace_id"]
    specialist_names = {s.name for s in agent.specialists}

    generate_spy = MagicMock(return_value=LLMResult(
        output="ok", provider="mock", model="mock-agent-model", latency_ms=1, success=True,
    ))
    monkeypatch.setattr(llm_router, "generate", generate_spy)
    agent.run(RunRequest(user_input="Explain how EvolveAgent AI works.", workspace_id=workspace_id))

    specialist_calls = [c for c in generate_spy.call_args_list if c.args and c.args[0] in specialist_names]
    assert len(specialist_calls) == len(agent.specialists)
    assert all(c.kwargs.get("workspace_id") == workspace_id for c in specialist_calls)


def test_run_consensus_candidates_forwards_workspace_id(tmp_path, monkeypatch):
    """Round 13: the remaining real LLM call sites in master_agent.py --
    consensus candidates (Deep Mode) and the risk/writing retry path -- had
    the same gap as the main specialist loop, and workspace_id was already in
    scope at both call sites (no new parameter plumbing needed)."""
    from app.services.llm_router import LLMResult, llm_router

    storage = StorageService(data_dir=str(tmp_path))
    agent = MasterOrchestratorAgent(storage=storage, memory_agent=MemoryAgent(storage))
    generate_for_provider_spy = MagicMock(return_value=LLMResult(
        output="candidate answer", provider="mock", model="mock-agent-model", latency_ms=1, success=True,
    ))
    monkeypatch.setattr(llm_router, "generate_for_provider", generate_for_provider_spy)
    agent.run_consensus_candidates("do a task", "some context", workspace_id="workspace-consensus")
    assert generate_for_provider_spy.called
    assert all(c.kwargs.get("workspace_id") == "workspace-consensus" for c in generate_for_provider_spy.call_args_list)


def test_risk_retry_forwards_workspace_id_to_both_retried_agents(tmp_path, monkeypatch):
    from app.models.response_models import AgentOutput
    from app.services.llm_router import LLMResult, llm_router

    storage = StorageService(data_dir=str(tmp_path))
    agent = MasterOrchestratorAgent(storage=storage, memory_agent=MemoryAgent(storage))
    generate_spy = MagicMock(return_value=LLMResult(
        output="retry output", provider="mock", model="mock-agent-model", latency_ms=1, success=True,
    ))
    monkeypatch.setattr(llm_router, "generate", generate_spy)
    outputs = [AgentOutput(agent_name="Research Agent", provider="mock", model="m", success=True, output="finding")]
    agent.risk_retry(
        "do a task", "some context", outputs, previous_score=40,
        writing_provider="mock", workspace_id="workspace-retry",
    )
    assert generate_spy.called
    assert all(c.kwargs.get("workspace_id") == "workspace-retry" for c in generate_spy.call_args_list)
