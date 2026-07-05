from __future__ import annotations

from datetime import UTC, datetime

from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


class HomeDashboardService:
    """A read-only 'Today' overview that aggregates activity across the app.

    Pulls lightweight counts from the local stores and the most recent governance
    activity into a single glanceable summary. Read-only — it computes nothing
    new, performs no action, and exposes no secrets.
    """

    # (label, storage filename) — counted by list length.
    _COUNTS = [
        ("agents", "agent_profiles.json"),
        ("workflow_runs", "durable_workflow_runs.json"),
        ("workflow_effects", "durable_workflow_effects.json"),
        ("repo_searches", "repo_finder_searches.json"),
        ("learned_items", "adaptive_learning_items.json"),
        ("design_analyses", "design_agent_analyses.json"),
        ("marketplace_listings", "marketplace_hub_listings.json"),
    ]

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def today(self) -> dict:
        metrics = {label: len(self.storage.read_list(fname)) for label, fname in self._COUNTS}

        # Recent activity — a compact, sanitized slice of the governance log.
        recent = []
        for e in self.governance.recent_events(12):
            recent.append({
                "action_type": e.get("action_type", ""),
                "agent": e.get("agent_name", ""),
                "reason": str(e.get("reason", ""))[:160],
                "risk_score": e.get("risk_score", 0),
            })

        highlights = []
        if metrics["agents"]:
            highlights.append(f"{metrics['agents']} custom agent(s) configured")
        if metrics["workflow_effects"]:
            highlights.append(f"{metrics['workflow_effects']} workflow action(s) performed")
        if metrics["learned_items"]:
            highlights.append(f"{metrics['learned_items']} item(s) in adaptive memory")
        if metrics["repo_searches"]:
            highlights.append(f"{metrics['repo_searches']} repo search(es) run")
        if not highlights:
            highlights.append("No activity yet — try the command palette (⌘K) to get started.")

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "metrics": metrics,
            "recent_activity": recent,
            "highlights": highlights,
            "quick_actions": [
                {"id": "new-chat", "label": "New chat"},
                {"id": "open-workflows", "label": "Run a workflow"},
                {"id": "open-repo-finder", "label": "Find a repo"},
                {"id": "open-adaptive", "label": "Auto-learn"},
            ],
        }
