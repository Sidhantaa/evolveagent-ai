from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# One-click demo script — an ordered set of beats with the prompt/route to show.
# v200: refreshed from the original v66 script, which stopped at "EvolveAgent OS
# 2.0 (v1-v60)" and never mentioned anything built since -- the same staleness
# this session found and fixed in EvolveAgentOS2Service's SYSTEM_INDEX (PR #210).
DEMO_SCRIPT = [
    {"step": 1, "title": "Master Agent", "route": "/api/master-agent", "action": "Ask: 'Review this Python function and suggest a refactor.'", "why": "Shows one AI routing across every subsystem with a confidence + why-this-route."},
    {"step": 2, "title": "Global Search", "route": "/api/search", "action": "Search a keyword across chats, files, goals, agents, memory.", "why": "One read-only search bar over the whole OS."},
    {"step": 3, "title": "Command Center", "route": "/api/os2", "action": "Show the v200 command center + platform scorecard.", "why": "Unified capstone across the full v1-v200 platform."},
    {"step": 4, "title": "Capability Directory", "route": "/api/capability-directory", "action": "Show the real/local/mock/needs-config breakdown across ~20 capabilities.", "why": "Honest inventory of what's actually real right now, not a marketing claim."},
    {"step": 5, "title": "Model Router", "route": "/api/provider-control/dashboard", "action": "Show real task-based routing and per-provider health.", "why": "Not locked to one model — routes by task, cost, and quality."},
    {"step": 6, "title": "Agent Network", "route": "/api/agent-network/dashboard", "action": "Create a contract, resolve a target by capability, and run a governed handoff.", "why": "Real agent-to-agent delegation, enforced by a real policy decision, not a mock."},
    {"step": 7, "title": "Marketplace Hub", "route": "/api/marketplace-hub/listings", "action": "Install and rate an agent listing.", "why": "Real installs and ratings, not placeholder counts."},
    {"step": 8, "title": "Chief of Staff", "route": "/api/chief-of-staff/dashboard", "action": "Generate a daily plan; note the real GitHub-informed priorities.", "why": "External signal folded into ranking, not just internal data."},
    {"step": 9, "title": "Governance & Approvals", "route": "/api/approvals-center", "action": "Trigger a risky request and show it held for approval.", "why": "Planning-first, approval-gated safety — the one rule nothing bypasses."},
    {"step": 10, "title": "Feature Registry", "route": "/api/features", "action": "Search features and open the route map.", "why": "The whole v1-v200 route surface is discoverable."},
]

WALKTHROUGH = [
    "Welcome — EvolveAgent AI is a local-first AI operating system (FastAPI + React) spanning 200+ iterative versions.",
    "It's not trying to out-model Claude — it's the governed layer that routes across Claude/OpenAI/Gemini, coordinates agents, and verifies outcomes.",
    "Everything runs on one governed pattern: thin route -> service -> local storage -> governance log.",
    "Talk to the Master Agent — it routes across every subsystem and explains why, with real multi-model consensus available in deep mode.",
    "Real agent-to-agent delegation is enforced by real policy, not just labeled 'agent': a denied or unapproved agent is refused, never silently run.",
    "Risky actions (send/pay/delete/deploy/code writes/PRs) are always held for human approval — this is the one rule nothing bypasses.",
    "It works with or without API keys thanks to mock/local fallback everywhere — it always demos cleanly, and the Capability Directory shows you exactly which parts are live right now.",
]

RESUME_BULLETS = [
    "Built EvolveAgent AI, a local-first AI operating system (FastAPI + React) spanning 200+ iterative versions, repositioned as a governed orchestration layer over Claude/OpenAI/Gemini rather than a rival foundation model.",
    "Designed a governed architecture — per-action audit logging, approval gates that risky actions can never bypass, and opt-in real providers with mock/local fallback everywhere.",
    "Implemented real task-based multi-model routing, agent-to-agent delegation enforced by a real policy engine, and a verification layer (real test-execution gates, multi-model consensus comparison, execution-outcome checks) — closing three architecture gaps identified from a strategic audit.",
    "Migrated production data (200+ collections, 100K+ documents) to PostgreSQL/pgvector with a real semantic-memory layer, and built a Capability Directory giving an honest real/mock/needs-config inventory across ~20 opt-in-real capabilities.",
]

# Collections the demo seeder may write to (always tagged demo_seed=true) and the id key to track.
# v200: added custom_agents alongside the original v66 trio so a seeded demo
# shows a v100+ capability too, not just goals/ideas. Deliberately did NOT add
# memory_v2_items here -- Memory v2 has its own pgvector-mode storage path (a
# dedicated Postgres table via MemoryService.add(), not the generic JSON/
# document backend every other SEEDABLE entry goes through) and no delete
# method exists yet, so seeding it here could never honor the "always
# reversible" guarantee this service promises.
SEEDABLE = [
    {"file": "workspaces.json", "id_key": "workspace_id"},
    {"file": "goals.json", "id_key": "goal_id"},
    {"file": "innovation_ideas.json", "id_key": "idea_id"},
    {"file": "custom_agents.json", "id_key": "agent_id"},
]


class DemoService:
    """Demo Mode / Portfolio Mode — make the app impressive and demo-safe.

    Provides a one-click demo script, a guided walkthrough, an auto-open feature
    sequence, a refreshed resume-bullet set, and a project case-study export (all
    read-only, generated content). It can also seed a demo-safe sample workspace
    (records tagged ``demo_seed=true`` and tracked in a seed log) and reset that
    demo data — reset removes **only** demo-tagged records it created, never user
    data. Seeding/reset are explicit and governance-logged.

    v200: refreshed from the original v66 content, which had gone stale the same
    way EvolveAgentOS2Service's SYSTEM_INDEX had (docs/roadmap/EvolveAgent-v200-
    Strategy.md's Current Execution Priority #3 -- "stabilize demo seed/reset").
    The script/walkthrough/resume bullets now reference the real v100-v200
    capabilities built this session instead of stopping at "EvolveAgent OS 2.0
    (v1-v60)", and the seed set gained a custom agent (a v100+ capability)
    alongside the original v66 trio of workspace/goals/ideas.
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
        return {"script": DEMO_SCRIPT, "step_count": len(DEMO_SCRIPT), "note": "Follow in order for a 5–6 minute demo."}

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
            "200+ iterative versions on one additive pattern — Master Agent routing, real multi-model routing (task-based, not locked",
            "to one provider), real agent-to-agent delegation enforced by a policy engine, a verification layer (real test-execution",
            "gates, multi-model consensus comparison), and a Capability Directory giving an honest real/mock/needs-config inventory —",
            "all planning-first and approval-gated.",
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

        for title, desc in [("Ship the v200 demo", "Walk through the one-click demo script."), ("Prepare portfolio pack", "Export the case study and resume bullets.")]:
            goal_id = f"demo-goal-{uuid4().hex[:8]}"
            self.storage.append("goals.json", {
                "goal_id": goal_id, "workspace_id": workspace_id, "title": title, "description": desc,
                "status": "active", "demo_seed": True, "demo_batch": batch_id, "created_at": self._now(),
            })
            created.append({"file": "goals.json", "id_key": "goal_id", "id": goal_id})

        agent_id = f"demo-agent-{uuid4().hex[:8]}"
        self.storage.append("custom_agents.json", {
            "agent_id": agent_id, "workspace_id": workspace_id, "name": "Demo Research Agent",
            "description": "Seeded demo custom agent.", "role": "Answer questions about a given topic concisely.",
            "prompt": "You are a helpful research assistant. Answer clearly and cite what you're unsure about.",
            "tools_allowed": [], "model_preference": "default", "memory_scope": "session",
            "approval_level": "read_only", "enabled": True, "template_name": None,
            "demo_seed": True, "demo_batch": batch_id, "created_at": self._now(), "updated_at": self._now(),
        })
        created.append({"file": "custom_agents.json", "id_key": "agent_id", "id": agent_id})

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
