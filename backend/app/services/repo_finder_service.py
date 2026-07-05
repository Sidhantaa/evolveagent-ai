from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

_API = "https://api.github.com/search/repositories"
_SORTS = {"stars", "forks", "updated", "best"}
_TIMEOUT = 12


class RepoFinderService:
    """Find relevant GitHub repositories for a natural-language query.

    Given a question or topic (e.g. "multi-agent framework", "voice assistant"),
    this searches GitHub's public code-search API and returns several ranked
    repositories — with stars, language, description, topics and links — plus a
    set of related topics to refine the search. The goal is to surface multiple
    good references so the user can compare and pick.

    Read-only and safe:
    * Only performs an **outbound GET** to GitHub's public search API — no writes,
      no mutations, no other hosts.
    * Works unauthenticated; if a ``GITHUB_TOKEN`` is present in the environment it
      is used only to raise the rate limit. The token is **never stored, logged, or
      returned** (status exposes an ``authenticated`` boolean only).
    * Degrades gracefully: on a network error or rate-limit it returns an empty
      result set with a note rather than failing.
    Every search is governance-logged.
    """

    searches_file = "repo_finder_searches.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _token() -> str | None:
        return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or None

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="repo_finder",
                agent_name="Repo Finder",
                action_type=action_type,
                tool_used="RepoFinderService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def status(self) -> dict:
        return {
            "available": True,
            "source": "github_search_api",
            "authenticated": bool(self._token()),  # boolean only — never the token
            "sorts": sorted(_SORTS),
            "note": "Read-only search of public GitHub repositories. Token (if set) is used only for rate limits.",
        }

    # -- HTTP (isolated so it can be mocked in tests) ------------------------
    def _http_get(self, url: str) -> dict:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "EvolveAgent-RepoFinder",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = self._token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))

    @staticmethod
    def _map_repo(item: dict) -> dict:
        return {
            "full_name": item.get("full_name", ""),
            "description": (item.get("description") or "")[:300],
            "stars": item.get("stargazers_count", 0),
            "forks": item.get("forks_count", 0),
            "language": item.get("language") or "",
            "topics": (item.get("topics") or [])[:8],
            "url": item.get("html_url", ""),
            "updated_at": item.get("updated_at", ""),
            "owner": (item.get("owner") or {}).get("login", ""),
        }

    def search(self, query: str, limit: int = 8, sort: str = "best") -> dict:
        query = str(query or "").strip()
        if not query:
            raise ValueError("query is required")
        query = query[:200]
        try:
            limit = max(1, min(25, int(limit)))
        except (TypeError, ValueError):
            limit = 8
        sort = sort if sort in _SORTS else "best"

        params = {"q": query, "per_page": str(limit)}
        if sort != "best":
            params["sort"] = sort
            params["order"] = "desc"
        url = f"{_API}?{urllib.parse.urlencode(params)}"

        results: list[dict] = []
        note = ""
        try:
            data = self._http_get(url)
            for item in (data.get("items") or [])[:limit]:
                results.append(self._map_repo(item))
        except Exception as exc:  # noqa: BLE001 — degrade, never crash
            note = f"GitHub search unavailable ({type(exc).__name__}). Try again shortly or set GITHUB_TOKEN for higher limits."

        # Related topics: the most common topics/languages across results, to refine.
        topic_counter: Counter = Counter()
        for r in results:
            topic_counter.update(r["topics"])
            if r["language"]:
                topic_counter.update([r["language"].lower()])
        related = [t for t, _ in topic_counter.most_common(10) if t.lower() not in query.lower()][:8]

        record = {
            "id": str(uuid4()),
            "query": query,
            "sort": sort,
            "result_count": len(results),
            "top": results[0]["full_name"] if results else "",
            "created_at": self._now(),
        }
        self.storage.append(self.searches_file, record)
        self._log("repo_search", f"Repo search '{query}' -> {len(results)} results")
        return {"query": query, "sort": sort, "count": len(results), "results": results, "related_topics": related, "note": note}

    def history(self, limit: int = 20) -> dict:
        rows = sorted(self.storage.read_list(self.searches_file), key=lambda r: r.get("created_at", ""), reverse=True)
        try:
            limit = max(1, min(100, int(limit)))
        except (TypeError, ValueError):
            limit = 20
        return {"history": rows[:limit], "count": len(rows)}

    def analytics_summary(self) -> dict:
        rows = self.storage.read_list(self.searches_file)
        return {"repo_finder_searches": len(rows)}

    def summary(self) -> dict:
        return {**self.status(), **self.analytics_summary()}
