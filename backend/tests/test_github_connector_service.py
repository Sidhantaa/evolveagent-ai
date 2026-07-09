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


# ------------------------------------------------------------------
# v120 — the one real write: create_issue (opt-in, never called directly by an
# agent; only reachable via an approved DurableWorkflowService step).
# ------------------------------------------------------------------
def test_writes_disabled_by_default_in_status(monkeypatch):
    monkeypatch.delenv("GITHUB_WRITES_ENABLED", raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    result = client.get("/api/github/status").json()
    assert result["writes_enabled"] is False
    assert result["supported_writes"] == []


def test_create_issue_declines_without_token(monkeypatch, tmp_path):
    from app.services.governance_service import GovernanceService
    from app.services.storage_service import StorageService
    monkeypatch.setenv("GITHUB_WRITES_ENABLED", "true")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    svc = GitHubConnectorService(s, g)
    result = svc.create_issue("manit0700/evolveagent-ai", "Bug report")
    assert result["wrote"] is False
    assert result["degraded"] is True
    assert "GITHUB_TOKEN" in result["note"]


def test_create_issue_requires_a_title(tmp_path):
    from app.services.governance_service import GovernanceService
    from app.services.storage_service import StorageService
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    svc = GitHubConnectorService(s, g)
    try:
        svc.create_issue("manit0700/evolveagent-ai", "   ")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_create_issue_performs_a_real_write_when_opted_in(monkeypatch, tmp_path):
    from app.services.governance_service import GovernanceService
    from app.services.storage_service import StorageService
    monkeypatch.setenv("GITHUB_WRITES_ENABLED", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    created_payload = {}

    def fake_post(self, path, body):
        created_payload["path"] = path
        created_payload["body"] = body
        return {"id": 99, "number": 42, "title": body["title"], "state": "open",
                "user": {"login": "eva-bot"}, "labels": [], "html_url": "https://github.com/o/r/issues/42",
                "created_at": "2026-07-08T00:00:00Z", "updated_at": "2026-07-08T00:00:00Z"}

    monkeypatch.setattr(GitHubConnectorService, "_http_post", fake_post)
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    svc = GitHubConnectorService(s, g)
    result = svc.create_issue("owner/repo", "Ship the feature", body="details here", labels=["bug"])
    assert result["wrote"] is True
    assert result["issue"]["number"] == 42
    assert created_payload["path"] == "/repos/owner/repo/issues"
    assert created_payload["body"]["labels"] == ["bug"]


def test_create_issue_network_failure_degrades(monkeypatch, tmp_path):
    from app.services.governance_service import GovernanceService
    from app.services.storage_service import StorageService
    monkeypatch.setenv("GITHUB_WRITES_ENABLED", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def boom(self, path, body):
        raise TimeoutError("network unavailable")

    monkeypatch.setattr(GitHubConnectorService, "_http_post", boom)
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    svc = GitHubConnectorService(s, g)
    result = svc.create_issue("owner/repo", "Ship the feature")
    assert result["wrote"] is False
    assert result["degraded"] is True
    assert "TimeoutError" in result["note"]


# ------------------------------------------------------------------
# v150 task 2 — the connector's second real write: create_pull_request (same
# opt-in/token gating as create_issue; never called directly by an agent).
# ------------------------------------------------------------------
def test_create_pull_request_declines_without_token(monkeypatch, tmp_path):
    from app.services.governance_service import GovernanceService
    from app.services.storage_service import StorageService
    monkeypatch.setenv("GITHUB_WRITES_ENABLED", "true")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    svc = GitHubConnectorService(s, g)
    result = svc.create_pull_request("owner/repo", "Add helper", head="feature/helper")
    assert result["wrote"] is False
    assert result["degraded"] is True
    assert "GITHUB_TOKEN" in result["note"]


def test_create_pull_request_requires_a_title_and_head(tmp_path):
    from app.services.governance_service import GovernanceService
    from app.services.storage_service import StorageService
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    svc = GitHubConnectorService(s, g)
    try:
        svc.create_pull_request("owner/repo", "   ", head="feature/x")
        assert False, "expected ValueError for missing title"
    except ValueError:
        pass
    try:
        svc.create_pull_request("owner/repo", "Add helper", head="   ")
        assert False, "expected ValueError for missing head"
    except ValueError:
        pass


def test_create_pull_request_performs_a_real_write_when_opted_in(monkeypatch, tmp_path):
    from app.services.governance_service import GovernanceService
    from app.services.storage_service import StorageService
    monkeypatch.setenv("GITHUB_WRITES_ENABLED", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    created_payload = {}

    def fake_post(self, path, body):
        created_payload["path"] = path
        created_payload["body"] = body
        return {"id": 7, "number": 12, "title": body["title"], "state": "open", "draft": False,
                "user": {"login": "eva-bot"}, "head": {"ref": body["head"]}, "base": {"ref": body["base"]},
                "html_url": "https://github.com/owner/repo/pull/12",
                "created_at": "2026-07-08T00:00:00Z", "updated_at": "2026-07-08T00:00:00Z"}

    monkeypatch.setattr(GitHubConnectorService, "_http_post", fake_post)
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    svc = GitHubConnectorService(s, g)
    result = svc.create_pull_request("owner/repo", "Add helper", head="feature/helper", base="main", body="details")
    assert result["wrote"] is True
    assert result["pull_request"]["number"] == 12
    assert created_payload["path"] == "/repos/owner/repo/pulls"
    assert created_payload["body"]["head"] == "feature/helper"
    assert created_payload["body"]["base"] == "main"


def test_create_pull_request_network_failure_degrades(monkeypatch, tmp_path):
    from app.services.governance_service import GovernanceService
    from app.services.storage_service import StorageService
    monkeypatch.setenv("GITHUB_WRITES_ENABLED", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def boom(self, path, body):
        raise TimeoutError("network unavailable")

    monkeypatch.setattr(GitHubConnectorService, "_http_post", boom)
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    svc = GitHubConnectorService(s, g)
    result = svc.create_pull_request("owner/repo", "Add helper", head="feature/helper")
    assert result["wrote"] is False
    assert result["degraded"] is True
    assert "TimeoutError" in result["note"]


def test_status_reports_create_pull_request_when_writes_enabled(monkeypatch):
    monkeypatch.setenv("GITHUB_WRITES_ENABLED", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    result = client.get("/api/github/status").json()
    assert "create_pull_request" in result["supported_writes"]
