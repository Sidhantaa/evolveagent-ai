from __future__ import annotations

import os
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Integration → env key (readiness = boolean only), declared scopes, and the local
# collection whose newest timestamp represents "last sync". Secret values are NEVER shown.
INTEGRATIONS = [
    {"id": "slack", "name": "Slack", "env_key": "SLACK_BOT_TOKEN", "scopes": ["chat:write"], "sync_file": "slack_notifications.json"},
    {"id": "notion", "name": "Notion", "env_key": "NOTION_API_KEY", "scopes": ["read_pages", "write_pages"], "sync_file": "notion_exports.json"},
    {"id": "linear", "name": "Linear", "env_key": "LINEAR_API_KEY", "scopes": ["issues:read", "issues:write"], "sync_file": "linear_links.json"},
    {"id": "github", "name": "GitHub", "env_key": "GITHUB_TOKEN", "scopes": ["repo"], "sync_file": "codex_jobs.json"},
]


class IntegrationHubService:
    """v87.0 Integration Hub 3.0 — cleaner Slack/Notion/Linear/GitHub-style integrations.

    A read-only hub of **integration cards** with **connection status** (is the env key
    set? boolean only), declared **scopes/permissions**, **last sync** (newest local
    timestamp for that integration), a plain-language **error explanation** when not
    connected, and a **dry-run test** (checks readiness without any real network call).
    **Secret values are never displayed** — only whether each key is set. Governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _key_set(key: str) -> bool:
        value = os.environ.get(key)
        return bool(value and value.strip())

    def _last_sync(self, sync_file: str) -> str | None:
        rows = self.storage.read_list(sync_file)
        stamps = [r.get("created_at") or r.get("updated_at") or r.get("timestamp") for r in rows if isinstance(r, dict)]
        stamps = [s for s in stamps if s]
        return max(stamps) if stamps else None

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="integration_hub",
                agent_name="Integration Hub",
                action_type=action_type,
                tool_used="IntegrationHubService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def cards(self) -> dict:
        rows = []
        for integ in INTEGRATIONS:
            connected = self._key_set(integ["env_key"])
            rows.append({
                "id": integ["id"],
                "name": integ["name"],
                "connected": connected,
                "required_key": integ["env_key"],          # name only, never the value
                "scopes": integ["scopes"],
                "last_sync": self._last_sync(integ["sync_file"]),
                "error": None if connected else f"Not connected — set {integ['env_key']} in the environment to enable {integ['name']}.",
            })
        self._log("integration_cards_viewed", f"Rendered {len(rows)} integration card(s).")
        return {"integrations": rows, "connected_count": sum(1 for r in rows if r["connected"]), "count": len(rows),
                "note": "Connection status is a boolean (is the key set?) — secret values are never displayed."}

    def dry_run(self, integration_id: str) -> dict:
        integ = next((i for i in INTEGRATIONS if i["id"] == integration_id), None)
        if integ is None:
            raise ValueError("Integration not found")
        connected = self._key_set(integ["env_key"])
        self._log("integration_dry_run", f"Dry-run test of {integ['name']} (key set={connected}).")
        return {
            "id": integ["id"],
            "name": integ["name"],
            "would_connect": connected,
            "result": "ready" if connected else "missing_key",
            "scopes": integ["scopes"],
            "explanation": ("Key is set — a real connection could be attempted (still approval-gated)." if connected
                            else f"Set {integ['env_key']} to enable {integ['name']}."),
            "note": "Dry-run only — no real network call is made; secret values are never read or shown.",
        }

    def analytics_summary(self) -> dict:
        return {"integration_hub_total": len(INTEGRATIONS),
                "integration_hub_connected": sum(1 for i in INTEGRATIONS if self._key_set(i["env_key"]))}

    def summary(self) -> dict:
        return {
            "integrations": [i["id"] for i in INTEGRATIONS],
            "connected": sum(1 for i in INTEGRATIONS if self._key_set(i["env_key"])),
            "note": "Read-only integration hub — boolean connection status only; no secret values displayed.",
        }
