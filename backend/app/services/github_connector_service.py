from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

_API = "https://api.github.com"
_TIMEOUT = 12
_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class GitHubConnectorService:
    """Read-only, governed GitHub connector for repos, issues, and pull requests.

    Safety model:
    * Uses GET requests only against GitHub REST API.
    * Token is read from GITHUB_TOKEN/GH_TOKEN and is never stored, logged, or returned.
    * Missing token, network failure, and GitHub errors degrade to empty results + a note.
    * All read attempts are governance-logged as low-risk read_only activity.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    @staticmethod
    def _token() -> str | None:
        return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or None

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str, blocked: bool = False) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="github_connector",
                agent_name="GitHub Connector",
                action_type=action_type,
                tool_used="GitHubConnectorService",
                permission_level="read_only",
                approved=not blocked,
                blocked=blocked,
                risk_score=1 if not blocked else 20,
                reason=reason,
            )
        )

    def status(self) -> dict:
        token_configured = bool(self._token())
        return {
            "available": True,
            "source": "github_rest_api",
            "mode": "read_only",
            "token_configured": token_configured,
            "authenticated": token_configured,
            "writes_enabled": False,
            "supported_reads": ["repos", "issues", "pull_requests"],
            "note": "Uses GITHUB_TOKEN only for read-only GitHub API calls. Token value is never returned.",
        }

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "EvolveAgent-GitHubConnector",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = self._token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _http_get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        query = urllib.parse.urlencode(params or {})
        url = f"{_API}{path}" + (f"?{query}" if query else "")
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))

    @staticmethod
    def _bounded_limit(limit: int, default: int = 20) -> int:
        try:
            return max(1, min(100, int(limit)))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _validate_repo(repo: str) -> str:
        repo = str(repo or "").strip()
        if not _REPO_RE.match(repo):
            raise ValueError("repo must be in owner/name format")
        owner, name = repo.split("/", 1)
        if owner in {".", ".."} or name in {".", ".."}:
            raise ValueError("repo must be in owner/name format")
        return repo

    @staticmethod
    def _degraded(payload_key: str, note: str, extra: dict | None = None) -> dict:
        return {payload_key: [], "count": 0, "degraded": True, "note": note, **(extra or {})}

    @staticmethod
    def _map_repo(item: dict) -> dict:
        return {
            "id": item.get("id"),
            "full_name": item.get("full_name", ""),
            "name": item.get("name", ""),
            "owner": (item.get("owner") or {}).get("login", ""),
            "private": bool(item.get("private")),
            "description": (item.get("description") or "")[:300],
            "language": item.get("language") or "",
            "stars": item.get("stargazers_count", 0),
            "forks": item.get("forks_count", 0),
            "open_issues": item.get("open_issues_count", 0),
            "url": item.get("html_url", ""),
            "updated_at": item.get("updated_at", ""),
            "default_branch": item.get("default_branch", ""),
        }

    @staticmethod
    def _map_issue(item: dict) -> dict:
        return {
            "id": item.get("id"),
            "number": item.get("number"),
            "title": item.get("title", ""),
            "state": item.get("state", ""),
            "author": (item.get("user") or {}).get("login", ""),
            "labels": [label.get("name", "") for label in item.get("labels", []) if isinstance(label, dict)][:12],
            "url": item.get("html_url", ""),
            "created_at": item.get("created_at", ""),
            "updated_at": item.get("updated_at", ""),
        }

    @staticmethod
    def _map_pull(item: dict) -> dict:
        return {
            "id": item.get("id"),
            "number": item.get("number"),
            "title": item.get("title", ""),
            "state": item.get("state", ""),
            "draft": bool(item.get("draft")),
            "author": (item.get("user") or {}).get("login", ""),
            "head": (item.get("head") or {}).get("ref", ""),
            "base": (item.get("base") or {}).get("ref", ""),
            "url": item.get("html_url", ""),
            "created_at": item.get("created_at", ""),
            "updated_at": item.get("updated_at", ""),
        }

    def list_repos(self, limit: int = 20) -> dict:
        limit = self._bounded_limit(limit)
        if not self._token():
            self._log("github_repos_read_degraded", "GitHub repo read skipped because GITHUB_TOKEN is not configured")
            return self._degraded(
                "repos",
                "GITHUB_TOKEN is not configured. Add a token to enable read-only repository listing.",
                {"token_configured": False},
            )
        try:
            items = self._http_get("/user/repos", {"per_page": limit, "sort": "updated", "affiliation": "owner,collaborator,organization_member"})
            repos = [self._map_repo(item) for item in (items or [])[:limit]]
            self._log("github_repos_read", f"Read {len(repos)} GitHub repositories")
            return {"repos": repos, "count": len(repos), "degraded": False, "token_configured": True, "note": ""}
        except Exception as exc:  # noqa: BLE001 - degrade, never crash
            self._log("github_repos_read_degraded", f"GitHub repo read unavailable ({type(exc).__name__})")
            return self._degraded("repos", f"GitHub repositories unavailable ({type(exc).__name__}).", {"token_configured": True})

    def list_issues(self, repo: str, state: str = "open", limit: int = 20) -> dict:
        repo = self._validate_repo(repo)
        limit = self._bounded_limit(limit)
        state = state if state in {"open", "closed", "all"} else "open"
        try:
            items = self._http_get(f"/repos/{repo}/issues", {"state": state, "per_page": limit})
            issues = [self._map_issue(item) for item in (items or []) if not item.get("pull_request")][:limit]
            self._log("github_issues_read", f"Read {len(issues)} GitHub issues from {repo}")
            return {"repo": repo, "state": state, "issues": issues, "count": len(issues), "degraded": False, "note": ""}
        except Exception as exc:  # noqa: BLE001
            self._log("github_issues_read_degraded", f"GitHub issues read unavailable for {repo} ({type(exc).__name__})")
            return self._degraded("issues", f"GitHub issues unavailable ({type(exc).__name__}).", {"repo": repo, "state": state})

    def list_pull_requests(self, repo: str, state: str = "open", limit: int = 20) -> dict:
        repo = self._validate_repo(repo)
        limit = self._bounded_limit(limit)
        state = state if state in {"open", "closed", "all"} else "open"
        try:
            items = self._http_get(f"/repos/{repo}/pulls", {"state": state, "per_page": limit})
            pulls = [self._map_pull(item) for item in (items or [])[:limit]]
            self._log("github_pulls_read", f"Read {len(pulls)} GitHub pull requests from {repo}")
            return {"repo": repo, "state": state, "pull_requests": pulls, "count": len(pulls), "degraded": False, "note": ""}
        except Exception as exc:  # noqa: BLE001
            self._log("github_pulls_read_degraded", f"GitHub pull request read unavailable for {repo} ({type(exc).__name__})")
            return self._degraded("pull_requests", f"GitHub pull requests unavailable ({type(exc).__name__}).", {"repo": repo, "state": state})

    def analytics_summary(self) -> dict:
        events = self.storage.read_list("governance_log.json")
        connector_events = [item for item in events if item.get("task_type") == "github_connector"]
        return {
            "github_connector_events": len(connector_events),
            "github_connector_degraded_events": sum(1 for item in connector_events if "degraded" in str(item.get("action_type", ""))),
        }

    def summary(self) -> dict:
        return {**self.status(), **self.analytics_summary(), "generated_at": self._now()}
