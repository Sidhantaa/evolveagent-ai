from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from statistics import mean
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.custom_agent_service import CustomAgentService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService
from app.services.workspace_service import WorkspaceService


class AgentMarketplaceService:
    teams_file = "agent_marketplace_teams.json"
    ratings_file = "agent_marketplace_ratings.json"
    installs_file = "agent_marketplace_installs.json"

    def __init__(
        self,
        storage: StorageService,
        custom_agents: CustomAgentService,
        workspace_service: WorkspaceService,
        governance_service: GovernanceService,
    ):
        self.storage = storage
        self.custom_agents = custom_agents
        self.workspace_service = workspace_service
        self.governance = governance_service

    @staticmethod
    def skill_packs() -> list[dict]:
        return [
            {
                "pack_id": "startup-builder-pack",
                "name": "Startup Builder Pack",
                "description": "Plans MVPs, validates markets, drafts launch assets, and reviews risks.",
                "category": "business",
                "version": "1.0.0",
                "permission_profile": "plan_only",
                "recommended_workflows": ["saas_planning", "market_validation", "launch_readiness"],
                "agents": ["Startup Strategy Agent", "Business Analyst Agent", "Code Review Agent"],
            },
            {
                "pack_id": "pharmacy-prior-auth-pack",
                "name": "Pharmacy Prior Auth Pack",
                "description": "Structures PA criteria, document gaps, and compliance review checklists.",
                "category": "healthcare_admin",
                "version": "1.0.0",
                "permission_profile": "read_only",
                "recommended_workflows": ["pa_review", "missing_information", "document_summary"],
                "agents": ["Pharmacy PA Agent", "File Summary Agent", "Compliance Review Agent"],
            },
            {
                "pack_id": "resume-ats-pack",
                "name": "Resume ATS Pack",
                "description": "Improves resumes, cover letters, ATS keywords, and interview positioning.",
                "category": "career",
                "version": "1.0.0",
                "permission_profile": "read_only",
                "recommended_workflows": ["resume_review", "cover_letter", "ats_keyword_match"],
                "agents": ["Resume Agent", "Writing Agent", "Business Analyst Agent"],
            },
            {
                "pack_id": "software-engineering-pack",
                "name": "Software Engineering Pack",
                "description": "Reviews architecture, plans implementation, finds bugs, and proposes tests.",
                "category": "engineering",
                "version": "1.0.0",
                "permission_profile": "plan_only",
                "recommended_workflows": ["code_review", "bug_triage", "test_planning"],
                "agents": ["Code Review Agent", "Bug Fix Agent", "Test Generation Agent"],
            },
            {
                "pack_id": "research-paper-pack",
                "name": "Research Paper Pack",
                "description": "Runs source scoring, citation tracking, evidence tables, and report drafting.",
                "category": "research",
                "version": "1.0.0",
                "permission_profile": "read_only",
                "recommended_workflows": ["controlled_research", "citation_review", "report_generation"],
                "agents": ["Research Agent", "File Summary Agent", "Study Notes Agent"],
            },
            {
                "pack_id": "construction-bid-pack",
                "name": "Construction Bid Pack",
                "description": "Extracts bid scope, exclusions, deadlines, risks, and clarification questions.",
                "category": "construction",
                "version": "1.0.0",
                "permission_profile": "read_only",
                "recommended_workflows": ["bid_review", "scope_extraction", "risk_checklist"],
                "agents": ["Construction Bid Agent", "File Summary Agent", "Business Analyst Agent"],
            },
            {
                "pack_id": "college-study-pack",
                "name": "College Study Pack",
                "description": "Turns lectures, notes, and recordings into study plans and practice questions.",
                "category": "education",
                "version": "1.0.0",
                "permission_profile": "read_only",
                "recommended_workflows": ["study_notes", "recording_summary", "quiz_generation"],
                "agents": ["Study Notes Agent", "Meeting Notes Agent", "File Summary Agent"],
            },
            {
                "pack_id": "insurance-claim-pack",
                "name": "Insurance Claim Pack",
                "description": "Organizes claim documents, missing evidence, status summaries, and escalation notes.",
                "category": "insurance",
                "version": "1.0.0",
                "permission_profile": "read_only",
                "recommended_workflows": ["claim_document_review", "evidence_gap_check", "status_report"],
                "agents": ["File Summary Agent", "Business Analyst Agent", "Compliance Review Agent"],
            },
        ]

    @staticmethod
    def permission_profiles() -> list[dict]:
        return [
            {
                "profile": "read_only",
                "description": "Agents can summarize, classify, and recommend but cannot plan edits or runs.",
                "allowed_tools": ["file_read", "recording_read", "knowledge_search"],
                "requires_approval": False,
            },
            {
                "profile": "plan_only",
                "description": "Agents can create plans and proposed changes but cannot apply them.",
                "allowed_tools": ["file_read", "recording_read", "knowledge_search", "project_scan"],
                "requires_approval": True,
            },
            {
                "profile": "approve_to_edit",
                "description": "Agents may propose file edits that require explicit approval before apply.",
                "allowed_tools": ["file_read", "project_scan", "safe_file_editor"],
                "requires_approval": True,
            },
            {
                "profile": "approve_to_run",
                "description": "Agents may request allowlisted commands that require explicit approval.",
                "allowed_tools": ["project_scan", "safe_command_runner"],
                "requires_approval": True,
            },
            {
                "profile": "blocked",
                "description": "Agent team is disabled and cannot run workflows.",
                "allowed_tools": [],
                "requires_approval": True,
            },
        ]

    def list_packs(self) -> list[dict]:
        ratings = self._ratings_by_pack()
        installs = self._installs_by_pack()
        packs = []
        for pack in self.skill_packs():
            enriched = deepcopy(pack)
            pack_ratings = ratings.get(pack["pack_id"], [])
            enriched["rating_count"] = len(pack_ratings)
            enriched["average_rating"] = round(mean(pack_ratings), 2) if pack_ratings else 0
            enriched["install_count"] = installs.get(pack["pack_id"], 0)
            packs.append(enriched)
        return packs

    def get_pack(self, pack_id: str) -> dict | None:
        return next((pack for pack in self.list_packs() if pack["pack_id"] == pack_id), None)

    def list_teams(self, workspace_id: str | None = None) -> list[dict]:
        items = self.storage.read_list(self.teams_file)
        if workspace_id:
            items = [item for item in items if item.get("workspace_id") == workspace_id]
        ratings = self._ratings_by_team()
        for item in items:
            scores = ratings.get(item.get("team_id"), [])
            item["rating_count"] = len(scores)
            item["average_rating"] = round(mean(scores), 2) if scores else 0
        return sorted(items, key=lambda item: item.get("updated_at", ""), reverse=True)

    def create_team(self, data: dict) -> dict:
        now = datetime.now(UTC).isoformat()
        workspace_id = self.workspace_service.resolve_workspace_id(data.get("workspace_id"))
        team = {
            "team_id": str(uuid4()),
            "workspace_id": workspace_id,
            "name": data.get("name") or "Agent Team",
            "description": data.get("description") or "",
            "category": data.get("category") or "custom",
            "agents": data.get("agents") or [],
            "workflow_packs": data.get("workflow_packs") or [],
            "permission_profile": data.get("permission_profile") or "read_only",
            "version": data.get("version") or "1.0.0",
            "version_history": [
                {
                    "version": data.get("version") or "1.0.0",
                    "notes": "Initial team version.",
                    "created_at": now,
                }
            ],
            "enabled": data.get("enabled", True),
            "created_at": now,
            "updated_at": now,
            "source_pack_id": data.get("source_pack_id"),
            "benchmark_score": data.get("benchmark_score", 0),
            "usage_count": 0,
        }
        items = self.storage.read_list(self.teams_file)
        items.append(team)
        self.storage.write_list(self.teams_file, items)
        self._log("agent_team_created", workspace_id, f"Agent team {team['name']} was created.")
        return team

    def install_pack(self, pack_id: str, workspace_id: str | None = None) -> dict:
        pack = next((item for item in self.skill_packs() if item["pack_id"] == pack_id), None)
        if pack is None:
            raise ValueError("Skill pack not found")
        workspace_id = self.workspace_service.resolve_workspace_id(workspace_id)
        created_agents = []
        for agent_name in pack["agents"]:
            template = self.custom_agents.template_by_name(agent_name)
            if template:
                agent = self.custom_agents.create({"workspace_id": workspace_id, "template_name": template["name"]})
                created_agents.append(agent.model_dump())
            else:
                agent = self.custom_agents.create(
                    {
                        "workspace_id": workspace_id,
                        "name": agent_name,
                        "description": f"{agent_name} installed from {pack['name']}.",
                        "role": f"Specialist role for {pack['name']}.",
                        "prompt": f"You are {agent_name}. Follow the {pack['name']} workflow and respect all safety rules.",
                        "approval_level": pack["permission_profile"],
                        "template_name": pack["name"],
                    }
                )
                created_agents.append(agent.model_dump())
        team = self.create_team(
            {
                "workspace_id": workspace_id,
                "name": pack["name"],
                "description": pack["description"],
                "category": pack["category"],
                "agents": [{"agent_id": item["agent_id"], "name": item["name"], "role": item["role"]} for item in created_agents],
                "workflow_packs": pack["recommended_workflows"],
                "permission_profile": pack["permission_profile"],
                "version": pack["version"],
                "source_pack_id": pack["pack_id"],
            }
        )
        install = {
            "install_id": str(uuid4()),
            "pack_id": pack_id,
            "team_id": team["team_id"],
            "workspace_id": workspace_id,
            "agent_ids": [item["agent_id"] for item in created_agents],
            "created_at": datetime.now(UTC).isoformat(),
        }
        self.storage.append(self.installs_file, install)
        self._log("agent_pack_installed", workspace_id, f"Skill pack {pack['name']} was installed.")
        return {"pack": pack, "team": team, "created_agents": created_agents, "install": install}

    def update_team(self, team_id: str, updates: dict) -> dict | None:
        items = self.storage.read_list(self.teams_file)
        team = next((item for item in items if item.get("team_id") == team_id), None)
        if team is None:
            return None
        previous_version = team.get("version", "1.0.0")
        for key in ("name", "description", "category", "agents", "workflow_packs", "permission_profile", "enabled", "benchmark_score"):
            if key in updates and updates[key] is not None:
                team[key] = updates[key]
        if updates.get("version") and updates["version"] != previous_version:
            team["version"] = updates["version"]
            team.setdefault("version_history", []).append(
                {
                    "version": updates["version"],
                    "notes": updates.get("version_notes") or "Team version updated.",
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )
        team["updated_at"] = datetime.now(UTC).isoformat()
        self.storage.write_list(self.teams_file, items)
        self._log("agent_team_updated", team.get("workspace_id"), f"Agent team {team.get('name')} was updated.")
        return team

    def export_team(self, team_id: str) -> dict | None:
        team = next((item for item in self.list_teams() if item.get("team_id") == team_id), None)
        if team is None:
            return None
        exported = {
            "schema": "evolveagent.agent_team.v1",
            "exported_at": datetime.now(UTC).isoformat(),
            "team": team,
            "permission_profile": next((item for item in self.permission_profiles() if item["profile"] == team.get("permission_profile")), None),
        }
        self._log("agent_team_exported", team.get("workspace_id"), f"Agent team {team.get('name')} was exported.")
        return exported

    def import_team(self, data: dict, workspace_id: str | None = None) -> dict:
        source = data.get("team") if data.get("schema") else data
        payload = {
            "workspace_id": workspace_id or source.get("workspace_id"),
            "name": source.get("name", "Imported Agent Team"),
            "description": source.get("description", ""),
            "category": source.get("category", "imported"),
            "agents": source.get("agents", []),
            "workflow_packs": source.get("workflow_packs", []),
            "permission_profile": source.get("permission_profile", "read_only"),
            "version": source.get("version", "1.0.0"),
            "enabled": source.get("enabled", True),
            "benchmark_score": source.get("benchmark_score", 0),
        }
        team = self.create_team(payload)
        team["source_imported"] = True
        return team

    def rate_team(self, team_id: str, rating: int, review: str = "", workspace_id: str | None = None) -> dict:
        team = next((item for item in self.storage.read_list(self.teams_file) if item.get("team_id") == team_id), None)
        if team is None:
            raise ValueError("Agent team not found")
        record = {
            "rating_id": str(uuid4()),
            "team_id": team_id,
            "pack_id": team.get("source_pack_id"),
            "workspace_id": workspace_id or team.get("workspace_id"),
            "rating": max(1, min(5, rating)),
            "review": review,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self.storage.append(self.ratings_file, record)
        self._log("agent_team_rated", record["workspace_id"], f"Agent team {team.get('name')} received a rating.")
        return record

    def dashboard(self, workspace_id: str | None = None) -> dict:
        resolved = self.workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
        teams = self.list_teams(resolved)
        packs = self.list_packs()
        ratings = self.storage.read_list(self.ratings_file)
        if resolved:
            ratings = [item for item in ratings if item.get("workspace_id") == resolved]
        return {
            "total_packs": len(packs),
            "installed_teams": len(teams),
            "enabled_teams": len([team for team in teams if team.get("enabled", True)]),
            "average_rating": round(mean([item.get("rating", 0) for item in ratings]), 2) if ratings else 0,
            "top_packs": sorted(packs, key=lambda item: (item.get("install_count", 0), item.get("average_rating", 0)), reverse=True)[:5],
            "recent_teams": teams[:5],
            "permission_profiles": self.permission_profiles(),
        }

    def _ratings_by_team(self) -> dict[str, list[int]]:
        rows: dict[str, list[int]] = {}
        for item in self.storage.read_list(self.ratings_file):
            if item.get("team_id"):
                rows.setdefault(item["team_id"], []).append(item.get("rating", 0))
        return rows

    def _ratings_by_pack(self) -> dict[str, list[int]]:
        rows: dict[str, list[int]] = {}
        for item in self.storage.read_list(self.ratings_file):
            if item.get("pack_id"):
                rows.setdefault(item["pack_id"], []).append(item.get("rating", 0))
        return rows

    def _installs_by_pack(self) -> dict[str, int]:
        rows: dict[str, int] = {}
        for item in self.storage.read_list(self.installs_file):
            if item.get("pack_id"):
                rows[item["pack_id"]] = rows.get(item["pack_id"], 0) + 1
        return rows

    def _log(self, action_type: str, workspace_id: str | None, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                workspace_id=workspace_id,
                agent_name="Agent Workforce Marketplace",
                action_type=action_type,
                tool_used="AgentMarketplaceService",
                permission_level="read_only",
                approved=False,
                blocked=False,
                reason=reason,
            )
        )
