from fastapi.testclient import TestClient

from app.main import app
from app.services.mcp_readonly_adapter import MCPReadOnlyAdapter

client = TestClient(app)

OPT_IN = "MCP_REAL_READONLY"


def _connector_enabled(slug: str = "git") -> str:
    connector = client.post("/api/mcp/connectors", json={"slug": slug}).json()
    client.post(f"/api/mcp/connectors/{connector['connector_id']}/enable")
    return connector["connector_id"]


def _approved_request(connector_id: str, action_name: str) -> str:
    request = client.post(
        f"/api/mcp/connectors/{connector_id}/execute",
        json={"action_name": action_name},
    ).json()
    if request["status"] == "pending_approval":
        client.post(f"/api/mcp/executions/{request['request_id']}/approve")
    return request["request_id"]


# ----------------------------------------------------------------------
# Adapter status
# ----------------------------------------------------------------------
def test_adapter_status_disabled_by_default(monkeypatch):
    monkeypatch.delenv(OPT_IN, raising=False)
    status = client.get("/api/mcp/adapter/status").json()
    assert status["real_readonly_enabled"] is False
    assert set(status["allowed_actions"]) == {"git_current_branch", "git_list_branches", "fs_list_directory", "fs_file_metadata"}
    caps = status["capabilities"]
    assert caps["shell"] is False
    assert caps["network"] is False
    assert caps["writes"] is False
    assert caps["returns_secrets"] is False


def test_opt_in_off_runs_mock_even_for_allowlisted(monkeypatch):
    monkeypatch.delenv(OPT_IN, raising=False)
    connector_id = _connector_enabled("git")
    request_id = _approved_request(connector_id, "git_current_branch")
    ran = client.post(f"/api/mcp/executions/{request_id}/run").json()
    assert ran["result"]["execution_mode"] == "mock"
    assert ran["result"]["real_call_made"] is False


def test_opt_in_on_runs_real_git_current_branch(monkeypatch):
    monkeypatch.setenv(OPT_IN, "1")
    connector_id = _connector_enabled("git")
    request_id = _approved_request(connector_id, "git_current_branch")
    ran = client.post(f"/api/mcp/executions/{request_id}/run").json()
    result = ran["result"]
    assert result["execution_mode"] == "real_read_only"
    assert result["real_call_made"] is True
    assert result["secrets_used"] is False
    assert result["success"] is True
    assert "branch" in result["output"] or "detached_head" in result["output"]


def test_non_allowlisted_action_always_mock(monkeypatch):
    monkeypatch.setenv(OPT_IN, "1")
    connector_id = _connector_enabled("github")
    # 'draft_pr_comment' is a valid github action but NOT on the real-adapter allow-list.
    request_id = _approved_request(connector_id, "draft_pr_comment")
    ran = client.post(f"/api/mcp/executions/{request_id}/run").json()
    assert ran["result"]["execution_mode"] == "mock"


# ----------------------------------------------------------------------
# Sandbox safety (unit-level, deterministic)
# ----------------------------------------------------------------------
def test_sandbox_blocks_traversal_and_absolute(monkeypatch, tmp_path):
    monkeypatch.setenv(OPT_IN, "1")
    adapter = MCPReadOnlyAdapter(sandbox_root=str(tmp_path))
    (tmp_path / "docs").mkdir()
    # Traversal escape → refused.
    out = adapter.try_execute({"name": "FS"}, "fs_list_directory", {"path": "../"})
    assert out["success"] is False
    # Absolute path → refused.
    out = adapter.try_execute({"name": "FS"}, "fs_list_directory", {"path": "/etc"})
    assert out["success"] is False
    # Valid in-sandbox dir → allowed.
    out = adapter.try_execute({"name": "FS"}, "fs_list_directory", {"path": "docs"})
    assert out["success"] is True


def test_sandbox_hides_sensitive_files(monkeypatch, tmp_path):
    monkeypatch.setenv(OPT_IN, "1")
    (tmp_path / ".env").write_text("SECRET_TOKEN=abcdef123456")
    (tmp_path / "readme.txt").write_text("hello")
    adapter = MCPReadOnlyAdapter(sandbox_root=str(tmp_path))
    out = adapter.try_execute({"name": "FS"}, "fs_list_directory", {"path": "."})
    assert out["success"] is True
    names = {e["name"] for e in out["output"]["entries"]}
    assert ".env" not in names  # dotfiles + sensitive names are hidden
    assert "readme.txt" in names
    assert "abcdef123456" not in str(out)
    # Directly targeting a sensitive file is refused, and contents never leak.
    meta = adapter.try_execute({"name": "FS"}, "fs_file_metadata", {"path": ".env"})
    assert meta["success"] is False
    assert "abcdef123456" not in str(meta)


def test_fs_metadata_returns_no_contents(monkeypatch, tmp_path):
    monkeypatch.setenv(OPT_IN, "1")
    (tmp_path / "note.txt").write_text("visible-body-should-not-appear")
    adapter = MCPReadOnlyAdapter(sandbox_root=str(tmp_path))
    out = adapter.try_execute({"name": "FS"}, "fs_file_metadata", {"path": "note.txt"})
    assert out["success"] is True
    assert "size_bytes" in out["output"]
    assert "visible-body-should-not-appear" not in str(out)


def test_adapter_declines_when_disabled(monkeypatch):
    monkeypatch.delenv(OPT_IN, raising=False)
    adapter = MCPReadOnlyAdapter()
    # Disabled → returns None so the caller falls back to mock.
    assert adapter.try_execute({"name": "Git"}, "git_current_branch", {}) is None


def test_adapter_declines_unsupported_action(monkeypatch):
    monkeypatch.setenv(OPT_IN, "1")
    adapter = MCPReadOnlyAdapter()
    assert adapter.try_execute({"name": "X"}, "not_a_real_action", {}) is None


# ----------------------------------------------------------------------
# Integration: safety flags + regression
# ----------------------------------------------------------------------
def test_execution_summary_reflects_adapter(monkeypatch):
    monkeypatch.setenv(OPT_IN, "1")
    summary = client.get("/api/mcp/executions/summary").json()
    assert summary["real_readonly_enabled"] is True
    assert summary["safety_summary"]["real_execution_readonly_only"] is True
    assert summary["safety_summary"]["shell_used"] is False
    assert summary["safety_summary"]["network_calls_made"] is False


def test_analytics_includes_readonly_fields():
    analytics = client.get("/api/analytics").json()
    for key in ("mcp_executions_real_readonly", "mcp_real_readonly_enabled"):
        assert key in analytics


def test_v42_mock_default_still_holds(monkeypatch):
    # With opt-in off, behaviour is identical to v42 (mock).
    monkeypatch.delenv(OPT_IN, raising=False)
    connector_id = _connector_enabled("context7")
    request_id = _approved_request(connector_id, "fetch_library_docs")
    ran = client.post(f"/api/mcp/executions/{request_id}/run").json()
    assert ran["result"]["execution_mode"] == "mock"


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/mcp/summary").status_code == 200
    assert client.get("/api/operating-layer/dashboard").status_code == 200
