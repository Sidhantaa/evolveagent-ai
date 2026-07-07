from __future__ import annotations

import os

# ----------------------------------------------------------------------
# v100 MCP GitHub Adapter
#
# Extends the v43 "try a real adapter first, fall back to mock" pattern (see
# mcp_readonly_adapter.py) to the GitHub connector: routes the MCP execution
# framework's approved read-only GitHub actions to GitHubConnectorService's real
# GitHub REST calls, instead of the generic mock output.
#
# Same safety posture as the read-only adapter: opt-in via an env flag, no
# writes/deletes, no secrets returned (the token is used by GitHubConnectorService
# internally and never surfaces here), and any failure degrades to "decline ->
# caller falls back to mock" rather than raising.
# ----------------------------------------------------------------------

OPT_IN_ENV = "MCP_REAL_GITHUB"

# Only read-only GitHub actions are ever executed for real here. Anything else
# (e.g. draft_pr_comment, which writes) is intentionally NOT in this list and
# stays on the mock path until a future write-approval design lands.
REAL_GITHUB_ACTIONS = [
    "read_repo_metadata",
    "list_issues",
    "list_pull_requests",
]


class MCPGitHubAdapter:
    def __init__(self, github_connector_service):
        self.github = github_connector_service

    def enabled(self) -> bool:
        return str(os.environ.get(OPT_IN_ENV, "")).strip().lower() in ("1", "true", "yes", "on")

    def supports(self, action_name: str) -> bool:
        return action_name in REAL_GITHUB_ACTIONS

    def status(self) -> dict:
        return {
            "real_github_enabled": self.enabled(),
            "opt_in_env": OPT_IN_ENV,
            "allowed_actions": list(REAL_GITHUB_ACTIONS),
            "token_configured": self.github.status().get("token_configured", False),
            "capabilities": {
                "shell": False,
                "network": True,  # the only real-adapter that calls out (GitHub REST, read-only)
                "writes": False,
                "deletes": False,
                "returns_secrets": False,
            },
            "note": "Real GitHub reads are opt-in and read-only. Uses GITHUB_TOKEN via GitHubConnectorService; "
                    "the token value is never returned here or logged.",
        }

    def try_execute(self, connector: dict, action_name: str, payload: dict | None = None) -> dict | None:
        """Return a real GitHub result, or None to signal 'fall back to mock'."""
        if not self.enabled() or not self.supports(action_name):
            return None
        if (connector or {}).get("slug") != "github":
            return None  # this adapter only ever serves the github connector
        payload = payload or {}
        try:
            if action_name == "read_repo_metadata":
                data = self.github.list_repos(limit=int(payload.get("limit", 20)))
            elif action_name == "list_issues":
                data = self.github.list_issues(
                    repo=payload.get("repo", ""),
                    state=payload.get("state", "open"),
                    limit=int(payload.get("limit", 20)),
                )
            else:  # list_pull_requests
                data = self.github.list_pull_requests(
                    repo=payload.get("repo", ""),
                    state=payload.get("state", "open"),
                    limit=int(payload.get("limit", 20)),
                )
            success = not data.get("degraded", False)
            message = data.get("note") or "GitHub read completed."
        except ValueError as exc:
            data, success, message = {}, False, str(exc)
        except Exception:  # never leak internals; degrade to a safe refusal
            data, success, message = {}, False, "GitHub action could not be completed safely."
        return {
            "execution_mode": "real_read_only",
            "success": success,
            "output": data,
            "message": message,
            "secrets_used": False,
            "real_call_made": True,
            "shell_used": False,
            "network_used": True,
            "wrote_data": False,
            "note": "Real read-only GitHub execution via GitHubConnectorService — no writes, no secrets returned.",
        }
