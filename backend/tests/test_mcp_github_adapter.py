"""v100 MCP GitHub Adapter — unit tests + wiring into the execution flow."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.mcp_github_adapter import MCPGitHubAdapter, OPT_IN_ENV, REAL_GITHUB_ACTIONS

client = TestClient(app)

GITHUB_CONNECTOR = {"connector_id": "c1", "slug": "github", "name": "GitHub MCP"}
OTHER_CONNECTOR = {"connector_id": "c2", "slug": "custom", "name": "Something Else"}


class StubGitHub:
    """A minimal stand-in for GitHubConnectorService, no network involved."""

    def __init__(self, degraded: bool = False, raise_on_issues: bool = False):
        self.degraded = degraded
        self.raise_on_issues = raise_on_issues
        self.calls: list[str] = []

    def status(self):
        return {"token_configured": not self.degraded}

    def list_repos(self, limit=20):
        self.calls.append("list_repos")
        if self.degraded:
            return {"repos": [], "count": 0, "degraded": True, "note": "no token"}
        return {"repos": [{"full_name": "acme/widgets"}], "count": 1, "degraded": False, "note": ""}

    def list_issues(self, repo, state="open", limit=20):
        self.calls.append("list_issues")
        if self.raise_on_issues:
            raise ValueError("repo must be in owner/name format")
        return {"repo": repo, "issues": [{"title": "bug"}], "count": 1, "degraded": False, "note": ""}

    def list_pull_requests(self, repo, state="open", limit=20):
        self.calls.append("list_pull_requests")
        return {"repo": repo, "pull_requests": [], "count": 0, "degraded": False, "note": ""}


def test_disabled_by_default_declines(monkeypatch):
    monkeypatch.delenv(OPT_IN_ENV, raising=False)
    adapter = MCPGitHubAdapter(StubGitHub())
    assert adapter.enabled() is False
    assert adapter.try_execute(GITHUB_CONNECTOR, "read_repo_metadata") is None


def test_declines_for_non_github_connector(monkeypatch):
    monkeypatch.setenv(OPT_IN_ENV, "1")
    adapter = MCPGitHubAdapter(StubGitHub())
    assert adapter.try_execute(OTHER_CONNECTOR, "read_repo_metadata") is None


def test_declines_for_write_action(monkeypatch):
    monkeypatch.setenv(OPT_IN_ENV, "1")
    adapter = MCPGitHubAdapter(StubGitHub())
    assert adapter.supports("draft_pr_comment") is False
    assert adapter.try_execute(GITHUB_CONNECTOR, "draft_pr_comment") is None


def test_real_execution_when_enabled(monkeypatch):
    monkeypatch.setenv(OPT_IN_ENV, "1")
    stub = StubGitHub()
    adapter = MCPGitHubAdapter(stub)
    result = adapter.try_execute(GITHUB_CONNECTOR, "read_repo_metadata")
    assert result["execution_mode"] == "real_read_only"
    assert result["real_call_made"] is True
    assert result["secrets_used"] is False
    assert result["success"] is True
    assert result["output"]["repos"][0]["full_name"] == "acme/widgets"
    assert stub.calls == ["list_repos"]


def test_list_issues_passes_payload_through(monkeypatch):
    monkeypatch.setenv(OPT_IN_ENV, "1")
    stub = StubGitHub()
    adapter = MCPGitHubAdapter(stub)
    result = adapter.try_execute(GITHUB_CONNECTOR, "list_issues", {"repo": "acme/widgets", "state": "open"})
    assert result["success"] is True
    assert result["output"]["repo"] == "acme/widgets"


def test_invalid_repo_degrades_without_raising(monkeypatch):
    monkeypatch.setenv(OPT_IN_ENV, "1")
    adapter = MCPGitHubAdapter(StubGitHub(raise_on_issues=True))
    result = adapter.try_execute(GITHUB_CONNECTOR, "list_issues", {"repo": "not-a-repo"})
    assert result["success"] is False
    assert "owner/name" in result["message"]
    assert result["real_call_made"] is True  # we did try — just got a validation failure


def test_status_reports_allowlist_and_token(monkeypatch):
    monkeypatch.setenv(OPT_IN_ENV, "1")
    adapter = MCPGitHubAdapter(StubGitHub(degraded=False))
    status = adapter.status()
    assert status["real_github_enabled"] is True
    assert set(status["allowed_actions"]) == set(REAL_GITHUB_ACTIONS)
    assert status["token_configured"] is True
    assert status["capabilities"]["writes"] is False


def test_adapter_status_endpoint_merges_github_without_breaking_readonly_shape(monkeypatch):
    monkeypatch.delenv(OPT_IN_ENV, raising=False)
    resp = client.get("/api/mcp/adapter/status").json()
    # readonly (v43) flat shape is unchanged
    assert "real_readonly_enabled" in resp
    assert "allowed_actions" in resp
    # v100 addition, nested so it can't collide with readonly's keys
    assert "github" in resp
    assert "real_github_enabled" in resp["github"]


def _github_connector_id() -> str:
    connector = client.post("/api/mcp/connectors", json={"slug": "github"}).json()
    client.post(f"/api/mcp/connectors/{connector['connector_id']}/enable")
    return connector["connector_id"]


def _approved_request(connector_id: str, action_name: str) -> str:
    request = client.post(f"/api/mcp/connectors/{connector_id}/execute", json={"action_name": action_name}).json()
    if request["status"] == "pending_approval":
        client.post(f"/api/mcp/executions/{request['request_id']}/approve")
    return request["request_id"]


def test_execution_flow_uses_mock_when_github_adapter_disabled(monkeypatch):
    monkeypatch.delenv(OPT_IN_ENV, raising=False)  # real GitHub execution OFF (default)
    connector_id = _github_connector_id()
    request_id = _approved_request(connector_id, "read_repo_metadata")
    ran = client.post(f"/api/mcp/executions/{request_id}/run").json()
    assert ran["result"]["execution_mode"] == "mock"
    assert ran["result"]["real_call_made"] is False


def test_execution_flow_uses_real_adapter_when_enabled(monkeypatch):
    monkeypatch.setenv(OPT_IN_ENV, "1")  # real GitHub execution ON, opt-in
    connector_id = _github_connector_id()
    request_id = _approved_request(connector_id, "read_repo_metadata")
    ran = client.post(f"/api/mcp/executions/{request_id}/run").json()
    result = ran["result"]
    # Real adapter engaged (execution_mode flips to real_read_only) even though no
    # GITHUB_TOKEN is configured in this test env — it degrades gracefully rather
    # than falling back to mock, proving the wiring (not the network) is what's tested.
    assert result["execution_mode"] == "real_read_only"
    assert result["real_call_made"] is True
    assert result["secrets_used"] is False
