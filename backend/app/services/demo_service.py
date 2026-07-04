from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# One-click demo script — an ordered set of beats with the prompt/route to show.
DEMO_SCRIPT = [
    {"step": 1, "title": "Master Agent", "route": "/api/master-agent", "action": "Ask: 'Review this Python function and suggest a refactor.'", "why": "Shows one AI routing across every subsystem with a confidence + why-this-route."},
    {"step": 2, "title": "Global Search", "route": "/api/search", "action": "Search a keyword across chats, files, goals, agents, memory.", "why": "One read-only search bar over the whole OS."},
    {"step": 3, "title": "Activity Timeline", "route": "/api/activity", "action": "Open the timeline and filter by type.", "why": "Everything the OS did, chronologically, governance-linked."},
    {"step": 4, "title": "Dashboard Home", "route": "/api/home", "action": "Show Today, approvals, health, suggested actions.", "why": "One professional homepage."},
    {"step": 5, "title": "Governance & Approvals", "route": "/api/approvals-center", "action": "Trigger a risky request and show it held for approval.", "why": "Planning-first, approval-gated safety."},
    {"step": 6, "title": "Feature Registry", "route": "/api/features", "action": "Search features and open the route map.", "why": "All 60+ versions are discoverable."},
    {"step": 7, "title": "EvolveAgent OS 2.0", "route": "/api/os2", "action": "Show the command center + platform scorecard.", "why": "Unified capstone across v1–v60."},
]

WALKTHROUGH = [
    "Welcome — EvolveAgent AI is a local-first, multi-agent AI operating system (FastAPI + React).",
    "Everything runs on one governed pattern: thin route → service → local JSON → governance log.",
    "Talk to the Master Agent — speak or type; it routes across every subsystem and explains why.",
    "Simple Mode is the clean console; Developer Mode exposes every layer for review.",
    "Risky actions (send/pay/delete/deploy) are always held for human approval.",
    "It works with or without API keys thanks to mock fallback — it always demos cleanly.",
]

RESUME_BULLETS = [
    "Built EvolveAgent AI, a local-first multi-agent AI operating system (FastAPI + React) spanning 65+ iterative versions, with a Master Agent that routes any request across every subsystem.",
    "Designed a governed architecture — per-action audit logging, approval gates that risky actions can never bypass, and opt-in real providers with mock fallback.",
    "Shipped a discoverable platform: global search, unified activity timeline, dashboard home, and a canonical feature registry over 60+ versions.",
    "Implemented an AI-native voice console (push-to-talk + spoken answers) and a governed MCP tool-connection layer with boolean-only secret key-readiness.",
]

# Collections the demo seeder may write to (always tagged demo_seed=true) and the id key to track.
SEEDABLE = [
    {"file": "workspaces.json", "id_key": "workspace_id"},
    {"file": "goals.json", "id_key": "goal_id"},
    {"file": "innovation_ideas.json", "id_key": "idea_id"},
]


class DemoService:
    """v66.0 Demo Mode / Portfolio Mode 2.0 — make the app impressive and demo-safe.

    Provides a one-click demo script, a guided walkthrough, an auto-open feature
    sequence, a refreshed resume-bullet set, and a project case-study export (all
    read-only, generated content). It can also seed a demo-safe sample workspace
    (records tagged ``demo_seed=true`` and tracked in a seed log) and reset that
    demo data — reset removes **only** demo-tagged records it created, never user
    data. Seeding/reset are explicit and governance-logged.
    """

    seed_log = "demo_seed_log.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str, risk: int = 1, blocked: bool = False) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="demo_mode",
                agent_name="Demo Mode",
                action_type=action_type,
                tool_used="DemoService",
                permission_level="read_only",
                approved=True,
                blocked=blocked,
                risk_score=risk,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Read-only demo/portfolio content
    # ------------------------------------------------------------------
    def script(self) -> dict:
        self._log("demo_script_viewed", "Served the one-click demo script.")
        return {"script": DEMO_SCRIPT, "step_count": len(DEMO_SCRIPT), "note": "Follow in order for a 3–4 minute demo."}

    def walkthrough(self) -> dict:
        return {"walkthrough": WALKTHROUGH, "step_count": len(WALKTHROUGH)}

    def feature_sequence(self) -> dict:
        return {"open_sequence": [{"title": s["title"], "route": s["route"]} for s in DEMO_SCRIPT], "count": len(DEMO_SCRIPT)}

    def resume_bullets(self) -> dict:
        return {"bullets": RESUME_BULLETS, "count": len(RESUME_BULLETS), "note": "Portfolio-ready wording; verify current version count before use."}

    def case_study(self) -> dict:
        lines = [
            "# EvolveAgent AI — Case Study",
            "",
            "**A local-first, multi-agent AI operating system (FastAPI + React).**",
            "",
            "## Problem",
            "A standard chatbot gives one opaque answer — no visibility, no memory, no safety gates, no quality measurement.",
            "",
            "## Approach",
            "Replace the single call with an inspectable, governed pipeline: a Master Agent routes each request across specialist",
            "subsystems, a governance layer records every stateful action, workspace memory provides context, and a judge/eval step",
            "scores quality. Simple Mode stays clean; Developer Mode exposes every layer.",
            "",
            "## Result",
            "65+ iterative versions on one additive pattern — Master Agent routing, global search, activity timeline, dashboard home,",
            "feature registry, MCP tool-connection layer, and an AI-native voice console — all planning-first and approval-gated.",
            "",
            "## Safety",
            "Local-first, mock/planning-first, no unrestricted shell, no real send/pay/deploy without approval, boolean-only secret",
            "key readiness, and per-action governance logging. It is not AGI and does not retrain the base model.",
        ]
        self._log("demo_case_study_exported", "Exported the project case study (markdown).")
        return {"format": "markdown", "content": "\n".join(lines)}

    # ------------------------------------------------------------------
    # Demo-safe sample data (scoped, tagged, reversible)
    # ------------------------------------------------------------------
    def seed(self) -> dict:
        batch_id = str(uuid4())
        created: list[dict] = []

        workspace_id = f"demo-{uuid4().hex[:8]}"
        self.storage.append("workspaces.json", {
            "workspace_id": workspace_id, "name": "Demo Workspace", "demo_seed": True, "demo_batch": batch_id, "created_at": self._now(),
        })
        created.append({"file": "workspaces.json", "id_key": "workspace_id", "id": workspace_id})

        for title, desc in [("Ship the v66 demo", "Walk through the one-click demo script."), ("Prepare portfolio pack", "Export the case study and resume bullets.")]:
            goal_id = f"demo-goal-{uuid4().hex[:8]}"
            self.storage.append("goals.json", {
                "goal_id": goal_id, "workspace_id": workspace_id, "title": title, "description": desc,
                "status": "active", "demo_seed": True, "demo_batch": batch_id, "created_at": self._now(),
            })
            created.append({"file": "goals.json", "id_key": "goal_id", "id": goal_id})

        idea_id = f"demo-idea-{uuid4().hex[:8]}"
        self.storage.append("innovation_ideas.json", {
            "idea_id": idea_id, "workspace_id": workspace_id, "title": "Demo idea: AI-native command bar",
            "description": "Seeded demo idea.", "demo_seed": True, "demo_batch": batch_id, "created_at": self._now(),
        })
        created.append({"file": "innovation_ideas.json", "id_key": "idea_id", "id": idea_id})

        self.storage.append(self.seed_log, {"batch_id": batch_id, "workspace_id": workspace_id, "items": created, "created_at": self._now()})
        self._log("demo_seeded", f"Seeded a demo-safe sample workspace ({len(created)} records, batch {batch_id[:8]}).", risk=2)
        return {"batch_id": batch_id, "workspace_id": workspace_id, "seeded_count": len(created), "note": "All records tagged demo_seed=true and tracked for reset."}

    def reset(self) -> dict:
        batches = self.storage.read_list(self.seed_log)
        removed = 0
        # Remove only records this service seeded (tagged demo_seed=true and tracked in the log).
        for source in SEEDABLE:
            items = self.storage.read_list(source["file"])
            kept = [i for i in items if not (isinstance(i, dict) and i.get("demo_seed") is True)]
            removed += len(items) - len(kept)
            if len(kept) != len(items):
                self.storage.write_list(source["file"], kept)
        self.storage.write_list(self.seed_log, [])
        self._log("demo_reset", f"Reset demo data — removed {removed} demo-tagged record(s) across {len(batches)} batch(es).", risk=2)
        return {"removed_count": removed, "batches_cleared": len(batches), "note": "Only demo_seed-tagged records were removed; user data is untouched."}

    def analytics_summary(self) -> dict:
        return {"demo_batches_active": len(self.storage.read_list(self.seed_log))}

    def summary(self) -> dict:
        batches = self.storage.read_list(self.seed_log)
        return {
            "demo_script_steps": len(DEMO_SCRIPT),
            "walkthrough_steps": len(WALKTHROUGH),
            "active_demo_batches": len(batches),
            "seeded_workspaces": [b.get("workspace_id") for b in batches],
            "note": "Demo Mode content is read-only; sample data is scoped and reversible.",
        }
