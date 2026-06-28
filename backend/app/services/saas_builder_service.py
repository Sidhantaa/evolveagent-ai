from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

FEEDBACK_TYPES = ["feature", "bug", "improvement", "question"]
FEEDBACK_STATUSES = ["open", "planned", "resolved", "wont_do"]


class SaaSBuilderService:
    """v32.0 Autonomous SaaS Builder (planning/drafting studio).

    Plans and drafts SaaS products from an idea: validation, roadmap,
    architecture plan, launch assets (landing/pricing/docs), and a feedback/bug
    loop. It only PLANS and DRAFTS — it does not deploy, charge money, create
    accounts, or modify files. Every stateful action is governance-logged.
    """

    projects_file = "saas_projects.json"
    validations_file = "saas_validations.json"
    roadmaps_file = "saas_roadmaps.json"
    architecture_file = "saas_architecture_plans.json"
    launch_file = "saas_launch_assets.json"
    feedback_file = "saas_feedback_items.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _enum(self, value, allowed: list[str], default: str) -> str:
        candidate = str(value or "").strip().lower()
        return candidate if candidate in allowed else default

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="saas_builder",
                agent_name="SaaS Builder",
                action_type=action_type,
                tool_used="SaaSBuilderService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------
    def list_projects(self) -> list[dict]:
        return self.storage.read_list(self.projects_file)

    def get_project(self, project_id: str) -> dict | None:
        return next((p for p in self.storage.read_list(self.projects_file) if p.get("project_id") == project_id), None)

    def create_project(self, data: dict) -> dict:
        project = {
            "project_id": str(uuid4()),
            "name": self._clean(data.get("name"), 160) or "SaaS project",
            "idea": self._clean(data.get("idea"), 4000),
            "status": "drafting",
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.projects_file, project)
        self._log("saas_project_created", f"Created SaaS project: {project['name']}.")
        return project

    def _require_project(self, project_id: str) -> dict:
        project = self.get_project(project_id)
        if project is None:
            raise ValueError("Project not found")
        return project

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate(self, project_id: str) -> dict:
        project = self._require_project(project_id)
        idea = project.get("idea", "")
        confidence = max(20, min(85, 40 + min(40, len(idea) // 20)))
        validation = {
            "validation_id": str(uuid4()),
            "project_id": project_id,
            "target_user": "Define the primary user segment most affected by the problem.",
            "pain": f"Core pain inferred from idea: {idea[:160]}" if idea else "Describe the pain point the product removes.",
            "value_prop": "A focused value proposition that solves one painful job better than alternatives.",
            "market_risk": "Validate willingness-to-pay and differentiation before building broadly.",
            "mvp_scope": ["One core workflow end to end", "Minimal onboarding", "A single integration if essential"],
            "monetization_hypothesis": "Start with a simple tiered subscription; validate pricing with early users.",
            "confidence": confidence,
            "note": "Planning/drafting only — no accounts, payments, or deployment.",
            "created_at": self._now(),
        }
        self.storage.append(self.validations_file, validation)
        self._log("saas_validation_created", f"Validated SaaS project {project_id}.")
        return validation

    # ------------------------------------------------------------------
    # Roadmap
    # ------------------------------------------------------------------
    def roadmap(self, project_id: str) -> dict:
        self._require_project(project_id)
        roadmap = {
            "roadmap_id": str(uuid4()),
            "project_id": project_id,
            "phases": [
                {"phase": "MVP", "features": ["Core workflow", "Auth-less local demo", "Basic dashboard"], "milestone": "Working demo"},
                {"phase": "Beta", "features": ["Onboarding", "Feedback loop", "Key integration"], "milestone": "First users"},
                {"phase": "Launch", "features": ["Pricing", "Docs", "Landing page"], "milestone": "Public launch (manual)"},
            ],
            "dependencies": ["Core workflow before dashboard", "Feedback loop before pricing"],
            "note": "A draft roadmap — sequence and scope should be confirmed with real users.",
            "created_at": self._now(),
        }
        self.storage.append(self.roadmaps_file, roadmap)
        self._log("saas_roadmap_created", f"Generated roadmap for project {project_id}.")
        return roadmap

    # ------------------------------------------------------------------
    # Architecture
    # ------------------------------------------------------------------
    def architecture(self, project_id: str) -> dict:
        self._require_project(project_id)
        plan = {
            "architecture_id": str(uuid4()),
            "project_id": project_id,
            "database_entities": [
                {"entity": "User", "fields": ["id", "email", "created_at"]},
                {"entity": "Project", "fields": ["id", "user_id", "name", "status"]},
                {"entity": "Item", "fields": ["id", "project_id", "data", "created_at"]},
            ],
            "api_routes": [
                "GET /api/projects",
                "POST /api/projects",
                "GET /api/projects/{id}",
                "POST /api/projects/{id}/items",
            ],
            "frontend_pages": ["Landing", "Dashboard", "Project detail", "Settings"],
            "integrations": ["Email (draft-only)", "Storage", "Analytics"],
            "risks": ["Scope creep", "Auth/security must be designed carefully before real launch", "Data migration"],
            "note": "Architecture draft only — not generated code; build behind the existing approval workflow.",
            "created_at": self._now(),
        }
        self.storage.append(self.architecture_file, plan)
        self._log("saas_architecture_created", f"Generated architecture plan for project {project_id}.")
        return plan

    # ------------------------------------------------------------------
    # Launch assets
    # ------------------------------------------------------------------
    def launch_assets(self, project_id: str) -> dict:
        project = self._require_project(project_id)
        name = project.get("name", "Your SaaS")
        assets = {
            "launch_id": str(uuid4()),
            "project_id": project_id,
            "landing_copy": {
                "headline": f"{name}: do your core workflow in minutes, not hours.",
                "subhead": "A focused tool that removes one painful job — without the bloat.",
                "cta": "Start free (demo)",
            },
            "pricing_tiers": [
                {"tier": "Free", "price": "$0", "features": ["Core workflow", "Local demo"]},
                {"tier": "Pro", "price": "$—/mo", "features": ["Everything in Free", "Integrations", "Priority support"]},
                {"tier": "Team", "price": "$—/mo", "features": ["Everything in Pro", "Shared workspace", "Admin controls"]},
            ],
            "docs_outline": ["Quickstart", "Core concepts", "Integrations", "FAQ", "Troubleshooting"],
            "note": "Draft marketing/pricing/docs — placeholder pricing; no real payment or sending.",
            "created_at": self._now(),
        }
        self.storage.append(self.launch_file, assets)
        self._log("saas_launch_assets_created", f"Generated launch assets for project {project_id}.")
        return assets

    # ------------------------------------------------------------------
    # Feedback / bug loop
    # ------------------------------------------------------------------
    def create_feedback(self, project_id: str, data: dict) -> dict:
        self._require_project(project_id)
        feedback = {
            "feedback_id": str(uuid4()),
            "project_id": project_id,
            "type": self._enum(data.get("type"), FEEDBACK_TYPES, "feature"),
            "title": self._clean(data.get("title"), 200),
            "detail": self._clean(data.get("detail"), 2000),
            "linked_phase": self._clean(data.get("linked_phase"), 60),
            "status": self._enum(data.get("status"), FEEDBACK_STATUSES, "open"),
            "created_at": self._now(),
        }
        self.storage.append(self.feedback_file, feedback)
        self._log("saas_feedback_created", f"Logged {feedback['type']} for project {project_id}.")
        return feedback

    def list_feedback(self, project_id: str) -> list[dict]:
        return [f for f in self.storage.read_list(self.feedback_file) if f.get("project_id") == project_id]

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard(self) -> dict:
        projects = self.list_projects()
        feedback = self.storage.read_list(self.feedback_file)
        return {
            "total_projects": len(projects),
            "total_validations": len(self.storage.read_list(self.validations_file)),
            "total_roadmaps": len(self.storage.read_list(self.roadmaps_file)),
            "total_architecture_plans": len(self.storage.read_list(self.architecture_file)),
            "total_launch_assets": len(self.storage.read_list(self.launch_file)),
            "open_feedback": sum(1 for f in feedback if f.get("status") == "open"),
            "total_feedback": len(feedback),
            "recent_projects": list(reversed(projects[-5:])),
            "safety_note": "Plans and drafts only — no deploy, no payments, no account creation, no file changes without approval.",
        }
