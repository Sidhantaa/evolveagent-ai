from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_check_mock_success_has_no_findings():
    body = client.post(
        "/api/self-healing/checks",
        json={"command": "pytest", "mode": "mock", "mock_exit_code": 0, "mock_stdout": "279 passed"},
    ).json()
    assert body["check"]["check_id"]
    assert body["check"]["success"] is True
    assert body["check"]["blocked"] is False
    assert body["findings"] == []
    listed = client.get("/api/self-healing/checks").json()
    assert any(c["check_id"] == body["check"]["check_id"] for c in listed["checks"])


def test_parse_mocked_command_failure_creates_findings():
    body = client.post(
        "/api/self-healing/checks",
        json={
            "command": "pytest",
            "mode": "mock",
            "mock_exit_code": 1,
            "mock_stderr": "FAILED tests/test_x.py::test_a - AssertionError\nModuleNotFoundError: No module named 'foo'",
        },
    ).json()
    assert body["check"]["success"] is False
    assert body["findings"]
    types = {f["finding_type"] for f in body["findings"]}
    assert "test_failure" in types
    assert "dependency_warning" in types


def test_unsafe_command_blocked_via_existing_runner():
    body = client.post(
        "/api/self-healing/checks",
        json={"command": "rm -rf /", "mode": "run"},
    ).json()
    assert body["check"]["blocked"] is True
    assert body["check"]["success"] is False
    # Blocked checks should not generate repair findings.
    assert body["findings"] == []


def test_create_finding_and_repair_task():
    check = client.post(
        "/api/self-healing/checks",
        json={"command": "pytest", "mode": "mock", "mock_exit_code": 1, "mock_stderr": "FAILED test_a - AssertionError"},
    ).json()
    finding_id = check["findings"][0]["finding_id"]
    repair = client.post(f"/api/self-healing/findings/{finding_id}/repair-task").json()
    assert repair["repair_id"]
    assert repair["finding_id"] == finding_id
    assert repair["status"] == "draft"
    assert repair["auto_apply"] is False
    assert repair["requires_approval"] is True
    assert isinstance(repair["suggested_patch_plan"], list) and repair["suggested_patch_plan"]


def test_repair_task_finding_not_found():
    assert client.post("/api/self-healing/findings/missing/repair-task").status_code == 404


def test_list_and_get_repairs():
    """verify_repair() requires a repair_id, but until now nothing returned
    one -- list_repairs()/get_repair() were real but had no route."""
    check = client.post(
        "/api/self-healing/checks",
        json={"command": "pytest", "mode": "mock", "mock_exit_code": 1, "mock_stderr": "FAILED test_a - AssertionError"},
    ).json()
    finding_id = check["findings"][0]["finding_id"]
    repair = client.post(f"/api/self-healing/findings/{finding_id}/repair-task").json()

    listed = client.get("/api/self-healing/repairs").json()
    assert any(r["repair_id"] == repair["repair_id"] for r in listed["repairs"])

    fetched = client.get(f"/api/self-healing/repairs/{repair['repair_id']}").json()
    assert fetched["repair_id"] == repair["repair_id"]
    assert fetched["finding_id"] == finding_id

    assert client.get("/api/self-healing/repairs/missing").status_code == 404


def test_verify_repair():
    check = client.post(
        "/api/self-healing/checks",
        json={"command": "pytest", "mode": "mock", "mock_exit_code": 1, "mock_stderr": "FAILED test_a"},
    ).json()
    finding_id = check["findings"][0]["finding_id"]
    repair = client.post(f"/api/self-healing/findings/{finding_id}/repair-task").json()
    verified = client.post(
        f"/api/self-healing/repairs/{repair['repair_id']}/verify",
        json={"mode": "mock", "mock_exit_code": 0, "mock_stdout": "all passed"},
    ).json()
    assert verified["status"] == "verified"
    assert verified["verification"]["success"] is True

    failed = client.post(
        f"/api/self-healing/repairs/{repair['repair_id']}/verify",
        json={"mode": "mock", "mock_exit_code": 1, "mock_stderr": "still failing"},
    ).json()
    assert failed["status"] == "verify_failed"

    assert client.post("/api/self-healing/repairs/missing/verify", json={"mode": "mock"}).status_code == 404


def test_dashboard_shape():
    body = client.get("/api/self-healing/dashboard").json()
    for key in ("total_checks", "failed_checks", "blocked_checks", "open_findings", "repair_drafts", "verified_repairs", "auto_apply"):
        assert key in body
    assert body["auto_apply"] is False


def test_analytics_summary_counts_checks_findings_repairs():
    check = client.post(
        "/api/self-healing/checks",
        json={"command": "pytest", "mode": "mock", "mock_exit_code": 1, "mock_stderr": "FAILED test_a - AssertionError"},
    ).json()
    finding_id = check["findings"][0]["finding_id"]
    repair = client.post(f"/api/self-healing/findings/{finding_id}/repair-task").json()
    client.post(
        f"/api/self-healing/repairs/{repair['repair_id']}/verify",
        json={"mode": "mock", "mock_exit_code": 0, "mock_stdout": "all passed"},
    )

    analytics = client.get("/api/analytics").json()
    for key in ("self_healing_checks", "self_healing_blocked_checks", "self_healing_open_findings",
                "self_healing_repair_drafts", "self_healing_verified_repairs"):
        assert key in analytics
    assert analytics["self_healing_checks"] >= 1
    assert analytics["self_healing_verified_repairs"] >= 1


def test_governance_event_written():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/self-healing/checks", json={"command": "pytest", "mode": "mock", "mock_exit_code": 0})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "self_healing_check_run" in actions


def test_existing_code_automation_still_works():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/agent-network/dashboard").status_code == 200
    assert client.get("/api/industry-modes/dashboard").status_code == 200
    assert client.get("/api/tools").status_code == 200
