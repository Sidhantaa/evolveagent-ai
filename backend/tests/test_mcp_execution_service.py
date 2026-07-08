from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _connector(slug: str) -> dict:
    return client.post("/api/mcp/connectors", json={"slug": slug}).json()


def _enable(connector_id: str) -> None:
    client.post(f"/api/mcp/connectors/{connector_id}/enable")


def test_read_only_low_risk_auto_approved_and_runs_mock():
    connector = _connector("context7")  # low risk, read_only
    _enable(connector["connector_id"])
    request = client.post(
        f"/api/mcp/connectors/{connector['connector_id']}/execute",
        json={"action_name": "fetch_library_docs"},
    ).json()
    assert request["request_id"]
    assert request["status"] == "approved"  # auto-approved
    assert request["requires_approval"] is False
    # Run it — result is mock only.
    ran = client.post(f"/api/mcp/executions/{request['request_id']}/run").json()
    assert ran["status"] == "executed"
    result = ran["result"]
    assert result["execution_mode"] == "mock"
    assert result["real_call_made"] is False
    assert result["secrets_used"] is False
    assert "no real" in result["note"].lower()


def test_write_action_requires_approval_before_run():
    connector = _connector("github")  # approval_required
    _enable(connector["connector_id"])
    request = client.post(
        f"/api/mcp/connectors/{connector['connector_id']}/execute",
        json={"action_name": "draft_pr_comment"},
    ).json()
    assert request["status"] == "pending_approval"
    assert request["requires_approval"] is True
    # Cannot run until approved.
    blocked_run = client.post(f"/api/mcp/executions/{request['request_id']}/run")
    assert blocked_run.status_code == 409
    # Approve, then run → mock result.
    approved = client.post(f"/api/mcp/executions/{request['request_id']}/approve").json()
    assert approved["status"] == "approved"
    ran = client.post(f"/api/mcp/executions/{request['request_id']}/run").json()
    assert ran["status"] == "executed"
    assert ran["result"]["execution_mode"] == "mock"


def test_blocked_action_creates_blocked_request_not_runnable():
    connector = _connector("github")
    _enable(connector["connector_id"])
    request = client.post(
        f"/api/mcp/connectors/{connector['connector_id']}/execute",
        json={"action_name": "delete repo"},
    ).json()
    assert request["status"] == "blocked"
    assert request["blocked_reason"]
    # A blocked request can never run.
    run = client.post(f"/api/mcp/executions/{request['request_id']}/run")
    assert run.status_code == 409


def test_disabled_connector_cannot_request_execution_run():
    connector = _connector("desktop-commander")  # mode disabled
    request = client.post(
        f"/api/mcp/connectors/{connector['connector_id']}/execute",
        json={"action_name": "plan_desktop_action"},
    ).json()
    # Planning blocks disabled-mode connectors, so the request is blocked.
    assert request["status"] == "blocked"


def test_run_revalidates_connector_enabled_state():
    connector = _connector("context7")
    _enable(connector["connector_id"])
    request = client.post(
        f"/api/mcp/connectors/{connector['connector_id']}/execute",
        json={"action_name": "fetch_library_docs"},
    ).json()
    # Disable the connector after the request is approved.
    client.post(f"/api/mcp/connectors/{connector['connector_id']}/disable")
    ran = client.post(f"/api/mcp/executions/{request['request_id']}/run").json()
    assert ran["status"] == "blocked"
    assert "disabled" in (ran.get("blocked_reason") or "").lower()


def test_reject_execution():
    connector = _connector("linear")
    _enable(connector["connector_id"])
    request = client.post(
        f"/api/mcp/connectors/{connector['connector_id']}/execute",
        json={"action_name": "update_status_with_approval"},
    ).json()
    rejected = client.post(f"/api/mcp/executions/{request['request_id']}/reject").json()
    assert rejected["status"] == "rejected"
    # Rejected request cannot run.
    assert client.post(f"/api/mcp/executions/{request['request_id']}/run").status_code == 409


def test_list_and_get_execution():
    connector = _connector("git")
    _enable(connector["connector_id"])
    request = client.post(
        f"/api/mcp/connectors/{connector['connector_id']}/execute",
        json={"action_name": "git_status"},
    ).json()
    listed = client.get(f"/api/mcp/executions?connector_id={connector['connector_id']}").json()
    assert any(r["request_id"] == request["request_id"] for r in listed["requests"])
    fetched = client.get(f"/api/mcp/executions/{request['request_id']}").json()
    assert fetched["request_id"] == request["request_id"]
    assert client.get("/api/mcp/executions/missing").status_code == 404


def test_execution_summary_safety():
    summary = client.get("/api/mcp/executions/summary").json()
    for key in ("total_requests", "by_status", "execution_mode", "safety_summary"):
        assert key in summary
    assert summary["execution_mode"] == "mock"
    safety = summary["safety_summary"]
    assert safety["real_execution_enabled"] is False
    assert safety["secrets_used"] is False
    assert safety["shell_used"] is False
    assert safety["network_calls_made"] is False
    assert safety["write_actions_require_approval"] is True


def test_governance_written_for_request_and_run():
    before = client.get("/api/governance").json()["total_events"]
    connector = _connector("context7")
    _enable(connector["connector_id"])
    request = client.post(
        f"/api/mcp/connectors/{connector['connector_id']}/execute",
        json={"action_name": "fetch_library_docs"},
    ).json()
    client.post(f"/api/mcp/executions/{request['request_id']}/run")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "mcp_execution_run" in actions or "mcp_execution_requested" in actions


def test_analytics_includes_execution_fields():
    analytics = client.get("/api/analytics").json()
    for key in ("mcp_execution_requests", "mcp_executions_run", "mcp_executions_pending", "mcp_executions_blocked", "mcp_execution_mode"):
        assert key in analytics
    assert analytics["mcp_execution_mode"] == "mock"


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/mcp/summary").status_code == 200
    assert client.get("/api/operating-layer/dashboard").status_code == 200
    assert client.get("/api/governance").status_code == 200


def test_request_payload_is_persisted_on_the_record():
    """Regression: the payload a caller submits used to be validated at planning
    time and then silently discarded — never stored, never passed to run_execution.
    It must now round-trip onto the request record."""
    connector = _connector("context7")
    _enable(connector["connector_id"])
    request = client.post(
        f"/api/mcp/connectors/{connector['connector_id']}/execute",
        json={"action_name": "fetch_library_docs", "payload": {"library": "fastapi", "limit": 5}},
    ).json()
    assert request["payload"] == {"library": "fastapi", "limit": "5"}
    fetched = client.get(f"/api/mcp/executions/{request['request_id']}").json()
    assert fetched["payload"]["library"] == "fastapi"
