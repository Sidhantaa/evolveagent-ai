from fastapi.testclient import TestClient

from app.main import app
from app.services.github_connector_service import GitHubConnectorService

client = TestClient(app)

FAKE_REPOS = [
    {
        "id": 1,
        "full_name": "manit0700/evolveagent-ai",
        "name": "evolveagent-ai",
        "owner": {"login": "manit0700"},
        "private": True,
        "description": "Multi-agent AI workspace",
        "language": "Python",
        "stargazers_count": 4,
        "forks_count": 1,
        "open_issues_count": 3,
        "html_url": "https://github.com/manit0700/evolveagent-ai",
        "updated_at": "2026-07-01T00:00:00Z",
        "default_branch": "main",
    }
]

FAKE_ISSUES = [
    {
        "id": 10,
        "number": 7,
        "title": "Add status card",
        "state": "open",
        "user": {"login": "octocat"},
        "labels": [{"name": "enhancement"}],
        "html_url": "https://github.com/manit0700/evolveagent-ai/issues/7",
        "created_at": "2026-07-01T00:00:00Z",
        "updated_at": "2026-07-02T00:00:00Z",
    },
    {
        "id": 11,
        "number": 8,
        "title": "This is a PR from the issues endpoint",
        "state": "open",
        "pull_request": {"url": "https://api.github.com/repos/manit0700/evolveagent-ai/pulls/8"},
    },
]

FAKE_PULLS = [
    {
        "id": 20,
        "number": 9,
        "title": "Improve connector",
        "state": "open",
        "draft": False,
        "user": {"login": "octocat"},
        "head": {"ref": "feat/connector"},
        "base": {"ref": "main"},
        "html_url": "https://github.com/manit0700/evolveagent-ai/pull/9",
        "created_at": "2026-07-03T00:00:00Z",
        "updated_at": "2026-07-04T00:00:00Z",
    }
]


def _patch_http(monkeypatch):
    def fake_get(self, path, params=None):
        if path == "/user/repos":
            return FAKE_REPOS
        if path.endswith("/issues"):
            return FAKE_ISSUES
        if path.endswith("/pulls"):
            return FAKE_PULLS
        return {}

    monkeypatch.setattr(GitHubConnectorService, "_http_get", fake_get)


def test_status_is_secret_safe(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_secret_should_not_leak")
    body = client.get("/api/github/status").json()
    assert body["available"] is True
    assert body["token_configured"] is True
    assert body["authenticated"] is True
    assert body["writes_enabled"] is False
    assert "ghp_" not in str(body)
    assert "secret_should_not_leak" not in str(body)


def test_list_repos_maps_real_response(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    _patch_http(monkeypatch)
    body = client.get("/api/github/repos?limit=5").json()
    assert body["count"] == 1
    assert body["degraded"] is False
    repo = body["repos"][0]
    assert repo["full_name"] == "manit0700/evolveagent-ai"
    assert repo["private"] is True
    assert repo["stars"] == 4
    assert repo["default_branch"] == "main"


def test_missing_token_degrades_without_500(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    body = client.get("/api/github/repos").json()
    assert body["count"] == 0
    assert body["degraded"] is True
    assert body["token_configured"] is False
    assert "GITHUB_TOKEN" in body["note"]


def test_issues_filter_out_pull_request_items(monkeypatch):
    _patch_http(monkeypatch)
    body = client.get("/api/github/issues?repo=manit0700/evolveagent-ai").json()
    assert body["count"] == 1
    assert body["issues"][0]["number"] == 7
    assert body["issues"][0]["labels"] == ["enhancement"]


def test_pull_requests_map_response(monkeypatch):
    _patch_http(monkeypatch)
    body = client.get("/api/github/pulls?repo=manit0700/evolveagent-ai").json()
    assert body["count"] == 1
    assert body["pull_requests"][0]["number"] == 9
    assert body["pull_requests"][0]["head"] == "feat/connector"
    assert body["pull_requests"][0]["base"] == "main"


def test_invalid_repo_rejected():
    assert client.get("/api/github/issues?repo=../secret").status_code == 400
    assert client.get("/api/github/pulls?repo=missing-owner").status_code == 400


def test_network_failure_degrades(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def boom(self, path, params=None):
        raise TimeoutError("network unavailable")

    monkeypatch.setattr(GitHubConnectorService, "_http_get", boom)
    body = client.get("/api/github/repos").json()
    assert body["count"] == 0
    assert body["degraded"] is True
    assert "TimeoutError" in body["note"]


def test_summary_analytics_and_governance(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    _patch_http(monkeypatch)
    client.get("/api/github/repos")
    summary = client.get("/api/github/summary").json()
    assert summary["github_connector_events"] >= 1
    assert client.get("/api/analytics").json()["github_connector_events"] >= 1
    actions = {e.get("action_type") for e in client.get("/api/governance").json()["recent_events"]}
    assert "github_repos_read" in actions


def test_existing_endpoints_still_work():
    assert client.get("/api/repo-finder/status").status_code == 200
    assert client.get("/api/master-agent/summary").status_code == 200
