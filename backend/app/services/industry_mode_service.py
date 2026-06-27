from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Default industry mode profiles. Each configures terminology, recommended
# agents, workflow templates, risk rules, and approval defaults. All are
# advisory/configuration only — they never bypass governance or permissions.
DEFAULT_MODES = [
    {
        "name": "Pharmacy",
        "description": "Prior-authorization and pharmacy support workflows. Decision support only — not medical advice.",
        "terminology": ["prior authorization", "formulary", "NDC", "step therapy", "PA criteria"],
        "recommended_agents": ["Pharmacy PA Agent", "Research Agent", "Writing Agent", "Risk Agent"],
        "workflow_templates": ["Draft PA justification", "Summarize clinical notes", "Check formulary alternatives"],
        "risk_rules": ["Never present output as medical advice", "Flag PHI for human review"],
        "approval_rules": ["Any patient-facing output requires human approval"],
    },
    {
        "name": "Construction",
        "description": "Bid preparation, scope, and project planning for construction work.",
        "terminology": ["RFI", "change order", "punch list", "takeoff", "submittal"],
        "recommended_agents": ["Construction Bid Agent", "Strategy Agent", "Logic Agent", "Risk Agent"],
        "workflow_templates": ["Draft bid summary", "Estimate scope and risks", "Compare subcontractor options"],
        "risk_rules": ["Cost figures are estimates only", "Flag safety-critical items"],
        "approval_rules": ["Bids require human review before sending"],
    },
    {
        "name": "Student",
        "description": "Study notes, summaries, and learning workflows for students.",
        "terminology": ["study notes", "flashcards", "rubric", "citation", "syllabus"],
        "recommended_agents": ["Study Notes Agent", "Research Agent", "Writing Agent"],
        "workflow_templates": ["Turn lecture into study notes", "Summarize reading", "Generate practice questions"],
        "risk_rules": ["Encourage original work — do not enable academic dishonesty"],
        "approval_rules": ["No approval required for personal study output"],
    },
    {
        "name": "Software",
        "description": "Software engineering workflows: code review, bug fixing, and planning.",
        "terminology": ["pull request", "regression", "refactor", "unit test", "CI"],
        "recommended_agents": ["Coder Agent", "Code Review Agent", "Bug Fix Agent", "Test Generation Agent"],
        "workflow_templates": ["Plan a feature", "Review a diff", "Draft a bug-fix plan"],
        "risk_rules": ["No unrestricted shell", "Only allowlisted build/test commands"],
        "approval_rules": ["File edits and command runs require approval"],
    },
    {
        "name": "Business",
        "description": "General business operations: leads, proposals, and strategy.",
        "terminology": ["pipeline", "conversion", "proposal", "KPI", "follow-up"],
        "recommended_agents": ["Strategy Agent", "Writing Agent", "Logic Agent"],
        "workflow_templates": ["Draft a proposal", "Plan outreach", "Summarize KPIs"],
        "risk_rules": ["No real external sending", "Financial figures are estimates"],
        "approval_rules": ["Outbound content requires human review"],
    },
    {
        "name": "Healthcare Admin",
        "description": "Administrative healthcare workflows. Not clinical advice.",
        "terminology": ["intake", "claim", "EOB", "coordination of benefits", "authorization"],
        "recommended_agents": ["Research Agent", "Writing Agent", "Risk Agent", "Compliance Auditor Agent"],
        "workflow_templates": ["Summarize an intake form", "Draft a claim follow-up", "Explain a denial reason"],
        "risk_rules": ["Never provide clinical advice", "Flag PHI for human review"],
        "approval_rules": ["Patient-facing output requires human approval"],
    },
    {
        "name": "Legal Document",
        "description": "Legal document review and drafting support. Not legal advice.",
        "terminology": ["clause", "indemnity", "non-compete", "termination", "governing law"],
        "recommended_agents": ["Research Agent", "Risk Agent", "Writing Agent", "Compliance Auditor Agent"],
        "workflow_templates": ["Summarize a contract", "Flag risky clauses", "Draft a plain-language summary"],
        "risk_rules": ["Never present output as legal advice", "Flag high-risk clauses"],
        "approval_rules": ["Any external-facing document requires human review"],
    },
    {
        "name": "Finance",
        "description": "Financial analysis and cost workflows. Not financial advice.",
        "terminology": ["runway", "burn rate", "margin", "forecast", "variance"],
        "recommended_agents": ["Logic Agent", "Strategy Agent", "Risk Agent"],
        "workflow_templates": ["Estimate costs", "Compare options", "Summarize a budget"],
        "risk_rules": ["Never present output as financial advice", "All figures are estimates"],
        "approval_rules": ["No real payments or transfers"],
    },
]


class IndustryModeService:
    """v22.0 Industry Workflow Modes.

    Configurable industry profiles (terminology, recommended agents, workflow
    templates, risk rules, approval defaults). Modes are advisory configuration
    that shape recommendations — they never bypass governance or permissions.
    Running a mode produces a planning record only. Stateful actions are logged.
    """

    modes_file = "industry_modes.json"
    runs_file = "industry_mode_runs.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _string_list(self, values, limit: int = 30, item_max: int = 200) -> list[str]:
        cleaned: list[str] = []
        for value in values or []:
            text = str(value).strip()[:item_max]
            if text and text not in cleaned:
                cleaned.append(text)
            if len(cleaned) >= limit:
                break
        return cleaned

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="industry_mode",
                agent_name="Industry Mode Service",
                action_type=action_type,
                tool_used="IndustryModeService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Modes
    # ------------------------------------------------------------------
    def list_modes(self, include_disabled: bool = True) -> list[dict]:
        modes = self.storage.read_list(self.modes_file)
        if include_disabled:
            return modes
        return [mode for mode in modes if mode.get("enabled", True)]

    def get_mode(self, mode_id: str) -> dict | None:
        return next((mode for mode in self.storage.read_list(self.modes_file) if mode.get("mode_id") == mode_id), None)

    def templates(self) -> list[dict]:
        return [dict(template) for template in DEFAULT_MODES]

    def seed_modes(self) -> dict:
        existing = {mode.get("name", "").lower() for mode in self.storage.read_list(self.modes_file)}
        created: list[dict] = []
        for template in DEFAULT_MODES:
            if template["name"].lower() in existing:
                continue
            mode = {
                "mode_id": str(uuid4()),
                "name": template["name"],
                "description": template["description"],
                "terminology": list(template["terminology"]),
                "recommended_agents": list(template["recommended_agents"]),
                "workflow_templates": list(template["workflow_templates"]),
                "risk_rules": list(template["risk_rules"]),
                "approval_rules": list(template["approval_rules"]),
                "enabled": True,
                "created_at": self._now(),
                "updated_at": self._now(),
            }
            self.storage.append(self.modes_file, mode)
            created.append(mode)
        self._log("industry_mode_seeded", f"Seeded {len(created)} industry mode(s).")
        return {"seeded_count": len(created), "skipped_existing": len(DEFAULT_MODES) - len(created), "modes": created}

    def update_mode(self, mode_id: str, updates: dict) -> dict:
        modes = self.storage.read_list(self.modes_file)
        mode = next((item for item in modes if item.get("mode_id") == mode_id), None)
        if mode is None:
            raise ValueError("Mode not found")
        if updates.get("name") is not None:
            mode["name"] = self._clean(updates["name"], 120) or mode["name"]
        if updates.get("description") is not None:
            mode["description"] = self._clean(updates["description"], 2000)
        for field in ("terminology", "recommended_agents", "workflow_templates", "risk_rules", "approval_rules"):
            if updates.get(field) is not None:
                mode[field] = self._string_list(updates[field])
        if updates.get("enabled") is not None:
            mode["enabled"] = bool(updates["enabled"])
        mode["updated_at"] = self._now()
        self.storage.write_list(self.modes_file, modes)
        self._log("industry_mode_updated", f"Updated industry mode {mode_id}.")
        return mode

    # ------------------------------------------------------------------
    # Runs
    # ------------------------------------------------------------------
    def run_mode(self, mode_id: str, prompt: str, workspace_id: str | None = None) -> dict:
        mode = self.get_mode(mode_id)
        if mode is None:
            raise ValueError("Mode not found")
        requires_approval = bool(mode.get("approval_rules"))
        run = {
            "run_id": str(uuid4()),
            "mode_id": mode_id,
            "mode_name": mode.get("name"),
            "workspace_id": workspace_id,
            "prompt": self._clean(prompt, 2000),
            "applied_terminology": mode.get("terminology", [])[:8],
            "recommended_agents": mode.get("recommended_agents", []),
            "suggested_templates": mode.get("workflow_templates", []),
            "risk_rules": mode.get("risk_rules", []),
            "requires_approval": requires_approval,
            "plan": [
                f"Interpret the request through the {mode.get('name')} lens.",
                "Apply mode terminology and recommended agents.",
                "Honor risk rules and route risky output through approval.",
            ],
            "status": "planned",
            "created_at": self._now(),
        }
        self.storage.append(self.runs_file, run)
        self._log("industry_mode_run", f"Planned {mode.get('name')} mode run.")
        return run

    def list_runs(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.runs_file)[-limit:]))

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard(self) -> dict:
        modes = self.list_modes()
        runs = self.storage.read_list(self.runs_file)
        return {
            "total_modes": len(modes),
            "enabled_modes": sum(1 for mode in modes if mode.get("enabled", True)),
            "total_runs": len(runs),
            "available_mode_names": [mode.get("name") for mode in modes],
            "recent_runs": list(reversed(runs[-5:])),
            "recommended_next_action": (
                "Seed the default industry modes to get started."
                if not modes
                else "Run a mode against a real prompt to see tailored recommendations."
            ),
        }
