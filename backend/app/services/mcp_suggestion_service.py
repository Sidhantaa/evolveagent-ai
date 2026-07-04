from __future__ import annotations

import os
import re
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.mcp_connector_service import MCPConnectorService

# Task keywords → connector slug. Used to suggest which MCP a spoken/typed task needs.
_INTENT_KEYWORDS = {
    "github": ["github", "pull request", " pr ", "repo", "repository", "issue", "commit to", "merge"],
    "linear": ["linear", "ticket", "sprint", "backlog", "issue tracker"],
    "slack": ["slack", "message the team", "channel", "post to slack", "notify the team"],
    "notion": ["notion", "notion page", "export to notion", "wiki", "knowledge base page"],
    "filesystem": ["file", "directory", "folder", "read the file", "list files", "project files"],
    "git": ["git ", "branch", "diff", "git status", "current branch", "checkout"],
    "playwright": ["playwright", "browser", "screenshot", "ui test", "test my frontend", "inspect the page"],
    "context7": ["documentation", "library docs", "api docs", "current docs", "reference for"],
    "desktop-commander": ["desktop", "open app", "open the application", "desktop tool"],
}


class MCPSuggestionService:
    """v57.0 Task-aware MCP suggestion + key detection.

    Given a task (typed or spoken), suggests which MCP connector(s) it needs and
    reports each connector's required environment keys **by name** with a
    readiness flag (is the key set? true/false). It NEVER reads, fetches, or
    returns a secret value — only the key name and whether it exists in the
    environment. Suggestions are read-only and governance-logged.
    """

    def __init__(self, connector_service: MCPConnectorService, governance_service: GovernanceService):
        self.connectors = connector_service
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _key_set(key_name: str) -> bool:
        value = os.environ.get(key_name)
        return bool(value and value.strip())

    def _existing_connector(self, slug: str) -> dict | None:
        return next((c for c in self.connectors.list_connectors() if c.get("slug") == slug), None)

    def suggest(self, task: str) -> dict:
        text = f" {(task or '').lower()} "
        text = re.sub(r"\s+", " ", text)
        templates = {t["slug"]: t for t in self.connectors.get_default_mcp_templates()}
        scored: list[tuple[str, int]] = []
        for slug, keywords in _INTENT_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw.strip() in text)
            if hits:
                scored.append((slug, hits))
        scored.sort(key=lambda s: s[1], reverse=True)

        suggestions = []
        for slug, score in scored:
            template = templates.get(slug)
            if not template:
                continue
            env_keys = template.get("env_keys_required", []) or []
            key_status = [{"key_name": k, "is_set": self._key_set(k)} for k in env_keys]
            missing = [k["key_name"] for k in key_status if not k["is_set"]]
            existing = self._existing_connector(slug)
            suggestions.append({
                "slug": slug,
                "name": template.get("name"),
                "category": template.get("category"),
                "risk_level": template.get("risk_level"),
                "mode": template.get("mode"),
                "match_score": score,
                "required_keys": key_status,          # names + booleans only — never values
                "missing_keys": missing,
                "keys_ready": len(missing) == 0,
                "already_registered": existing is not None,
                "already_enabled": bool(existing and existing.get("enabled")),
                "recommended_action": (
                    "Ready — register/enable this connector."
                    if not missing else
                    f"Set {', '.join(missing)} in the environment to enable this connector."
                ),
            })

        self.governance.log_event(
            GovernanceEvent(
                task_type="mcp_suggestion",
                agent_name="MCP Suggestion",
                action_type="mcp_suggested",
                tool_used="MCPSuggestionService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=3,
                reason=f"Suggested {len(suggestions)} MCP connector(s) for task.",
            )
        )
        return {
            "task": (task or "")[:500],
            "suggestions": suggestions,
            "suggestion_count": len(suggestions),
            "note": "Key detection reports only whether each required env key is set (true/false) — secret values are never read or returned.",
        }
