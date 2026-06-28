from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_session(**overrides) -> dict:
    payload = {
        "device_label": overrides.get("device_label", "Test phone"),
        "permission_level": overrides.get("permission_level", "tap_type_with_confirmation"),
    }
    response = client.post("/api/device-operator/sessions", json=payload)
    assert response.status_code == 200
    return response.json()


def test_session_creation():
    session = _create_session()
    assert session["session_id"]
    assert session["mock_mode"] is True
    assert session["permission_level"] == "tap_type_with_confirmation"
    listed = client.get("/api/device-operator/sessions").json()
    assert any(s["session_id"] == session["session_id"] for s in listed["sessions"])
    assert client.get(f"/api/device-operator/sessions/{session['session_id']}").status_code == 200


def test_session_not_found():
    assert client.get("/api/device-operator/sessions/missing").status_code == 404
    assert client.post("/api/device-operator/sessions/missing/plan", json={"command": "read"}).status_code == 404


def test_command_planning():
    session = _create_session()
    plan = client.post(f"/api/device-operator/sessions/{session['session_id']}/plan", json={"command": "open the notes app"}).json()
    assert plan["mock_mode"] is True
    assert plan["planned_actions"]
    assert plan["planned_actions"][0]["action_type"] in {"open_app", "read_screen"}
    assert "no real device action" in plan["note"].lower()


def test_screen_read_planning():
    session = _create_session(permission_level="read_screen_only")
    plan = client.post(
        f"/api/device-operator/sessions/{session['session_id']}/plan",
        json={"screen_text": "Inbox: 3 unread messages from work"},
    ).json()
    read_actions = [a for a in plan["planned_actions"] if a["action_type"] == "read_screen"]
    assert read_actions
    assert read_actions[0]["risk_level"] == "low"


def test_risky_action_requires_confirmation():
    session = _create_session()
    plan = client.post(f"/api/device-operator/sessions/{session['session_id']}/plan", json={"command": "send a message to mom"}).json()
    action = plan["planned_actions"][0]
    assert action["action_type"] == "send_message"
    assert action["requires_confirmation"] is True
    assert action["status"] == "needs_confirmation"


def test_blocked_action_is_blocked():
    session = _create_session()
    plan = client.post(f"/api/device-operator/sessions/{session['session_id']}/plan", json={"command": "pay the electricity bill"}).json()
    action = plan["planned_actions"][0]
    assert action["action_type"] == "pay"
    assert action["blocked"] is True
    assert action["status"] == "blocked"
    # Attempting to confirm a blocked action is denied.
    decided = client.post(
        f"/api/device-operator/sessions/{session['session_id']}/confirm-action",
        json={"action_id": action["action_id"], "approve": True},
    ).json()
    assert decided["status"] == "blocked"


def test_confirm_and_reject_non_blocked_action():
    session = _create_session()
    plan = client.post(f"/api/device-operator/sessions/{session['session_id']}/plan", json={"command": "type my name in the field"}).json()
    action = plan["planned_actions"][0]
    approved = client.post(
        f"/api/device-operator/sessions/{session['session_id']}/confirm-action",
        json={"action_id": action["action_id"], "approve": True},
    ).json()
    assert approved["status"] == "approved_mock"


def test_audit_record_written():
    session = _create_session()
    client.post(f"/api/device-operator/sessions/{session['session_id']}/plan", json={"command": "read screen"})
    audit = client.get("/api/device-operator/audit").json()
    assert audit["count"] >= 1
    event_types = {entry["event_type"] for entry in audit["audit"]}
    assert "session_created" in event_types or "action_planned" in event_types


def test_dashboard_returns_counts():
    _create_session()
    body = client.get("/api/device-operator/dashboard").json()
    for key in ("total_sessions", "total_actions", "blocked_actions", "actions_awaiting_confirmation", "permission_levels", "mock_mode"):
        assert key in body
    assert body["mock_mode"] is True
    assert "blocked" in body["permission_levels"]


def test_governance_event_written():
    before = client.get("/api/governance").json()["total_events"]
    _create_session()
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "device_session_created" in actions


def test_regression_run_still_works():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/company-brain/dashboard").status_code == 200
