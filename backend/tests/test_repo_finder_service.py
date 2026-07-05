from fastapi.testclient import TestClient

from app.main import app
from app.services.repo_finder_service import RepoFinderService

client = TestClient(app)

# Canned GitHub search response so tests never hit the network.
FAKE = {
    "items": [
        {
            "full_name": "langchain-ai/langchain", "description": "Build agents",
            "stargazers_count": 90000, "forks_count": 14000, "language": "Python",
            "topics": ["agents", "llm", "framework"], "html_url": "https://github.com/langchain-ai/langchain",
            "updated_at": "2026-06-01T00:00:00Z", "owner": {"login": "langchain-ai"},
        },
        {
            "full_name": "microsoft/autogen", "description": "Multi-agent framework",
            "stargazers_count": 30000, "forks_count": 4000, "language": "Python",
            "topics": ["agents", "multi-agent"], "html_url": "https://github.com/microsoft/autogen",
            "updated_at": "2026-06-02T00:00:00Z", "owner": {"login": "microsoft"},
        },
    ]
}


def _patch(monkeypatch, payload=FAKE):
    monkeypatch.setattr(RepoFinderService, "_http_get", lambda self, url: payload)


def test_status_is_secret_safe():
    s = client.get("/api/repo-finder/status").json()
    assert s["available"] is True
    assert isinstance(s["authenticated"], bool)  # boolean only, never the token
    assert "token" not in s


def test_search_returns_ranked_results(monkeypatch):
    _patch(monkeypatch)
    r = client.post("/api/repo-finder/search", json={"query": "agent framework", "limit": 5}).json()
    assert r["count"] == 2
    top = r["results"][0]
    assert top["full_name"] == "langchain-ai/langchain"
    assert top["stars"] == 90000 and top["language"] == "Python"
    assert "url" in top and top["topics"]


def test_search_suggests_related_topics(monkeypatch):
    _patch(monkeypatch)
    r = client.post("/api/repo-finder/search", json={"query": "agent"}).json()
    # common topics across results, excluding terms already in the query
    assert "llm" in r["related_topics"] or "multi-agent" in r["related_topics"]


def test_search_degrades_on_network_error(monkeypatch):
    def boom(self, url):
        raise TimeoutError("nope")
    monkeypatch.setattr(RepoFinderService, "_http_get", boom)
    r = client.post("/api/repo-finder/search", json={"query": "agent"}).json()
    assert r["count"] == 0
    assert r["note"]  # graceful note, not a 500


def test_empty_query_rejected():
    assert client.post("/api/repo-finder/search", json={"query": "   "}).status_code == 422 \
        or client.post("/api/repo-finder/search", json={"query": ""}).status_code == 422


def test_history_and_analytics_and_governance(monkeypatch):
    _patch(monkeypatch)
    client.post("/api/repo-finder/search", json={"query": "voice assistant"})
    assert client.get("/api/repo-finder/history").json()["count"] >= 1
    assert "repo_finder_searches" in client.get("/api/analytics").json()
    actions = {e.get("action_type") for e in client.get("/api/governance").json()["recent_events"]}
    assert "repo_search" in actions


def test_existing_endpoints_still_work():
    assert client.get("/api/design-agent/status").status_code == 200
    assert client.get("/api/git-intel/read-status").status_code == 200
