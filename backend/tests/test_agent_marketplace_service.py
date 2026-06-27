from app.services.agent_marketplace_service import AgentMarketplaceService
from app.services.custom_agent_service import CustomAgentService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService
from app.services.workspace_service import WorkspaceService


def build_service(tmp_path):
    storage = StorageService(data_dir=str(tmp_path))
    workspace = WorkspaceService(storage)
    governance = GovernanceService(storage)
    custom_agents = CustomAgentService(storage)
    service = AgentMarketplaceService(storage, custom_agents, workspace, governance)
    return service, storage, workspace


def test_marketplace_lists_skill_packs_and_permission_profiles(tmp_path):
    service, _, _ = build_service(tmp_path)

    packs = service.list_packs()
    profiles = service.permission_profiles()

    assert any(pack["pack_id"] == "software-engineering-pack" for pack in packs)
    assert any(pack["name"] == "Pharmacy Prior Auth Pack" for pack in packs)
    assert any(profile["profile"] == "plan_only" for profile in profiles)
    assert all("average_rating" in pack for pack in packs)


def test_install_pack_creates_agent_team_and_custom_agents(tmp_path):
    service, storage, workspace = build_service(tmp_path)

    result = service.install_pack("software-engineering-pack", workspace.default_workspace_id())

    assert result["team"]["name"] == "Software Engineering Pack"
    assert result["team"]["permission_profile"] == "plan_only"
    assert len(result["created_agents"]) == 3
    assert storage.read_list("agent_marketplace_installs.json")
    assert len(storage.read_list("custom_agents.json")) == 3
    assert any(event["action_type"] == "agent_pack_installed" for event in storage.read_list("governance_log.json"))


def test_create_update_export_import_and_rate_team(tmp_path):
    service, storage, workspace = build_service(tmp_path)

    team = service.create_team(
        {
            "workspace_id": workspace.default_workspace_id(),
            "name": "Research Team",
            "description": "Research workflow specialists",
            "agents": [{"name": "Research Agent"}],
            "workflow_packs": ["controlled_research"],
            "permission_profile": "read_only",
        }
    )
    updated = service.update_team(
        team["team_id"],
        {"version": "1.1.0", "version_notes": "Added citation review.", "benchmark_score": 88},
    )
    rating = service.rate_team(team["team_id"], 5, "Strong research pack")
    exported = service.export_team(team["team_id"])
    imported = service.import_team(exported, workspace_id=workspace.default_workspace_id())
    dashboard = service.dashboard(workspace_id=workspace.default_workspace_id())

    assert updated["version"] == "1.1.0"
    assert updated["version_history"][-1]["notes"] == "Added citation review."
    assert rating["rating"] == 5
    assert exported["schema"] == "evolveagent.agent_team.v1"
    assert imported["name"] == "Research Team"
    assert dashboard["installed_teams"] == 2
    assert dashboard["average_rating"] == 5
    assert any(event["action_type"] == "agent_team_exported" for event in storage.read_list("governance_log.json"))
