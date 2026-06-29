from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_device(**overrides) -> dict:
    payload = {
        "name": overrides.get("name", "Office speaker"),
        "device_type": overrides.get("device_type", "speaker"),
        "has_mic": overrides.get("has_mic", True),
        "has_speaker": overrides.get("has_speaker", True),
        "local_processing": overrides.get("local_processing", True),
    }
    response = client.post("/api/hardware-companion/devices", json=payload)
    assert response.status_code == 200
    return response.json()


def test_device_create_list_update():
    device = _create_device()
    assert device["device_id"]
    assert device["registered"] is True
    listed = client.get("/api/hardware-companion/devices").json()
    assert any(d["device_id"] == device["device_id"] for d in listed["devices"])
    updated = client.patch(f"/api/hardware-companion/devices/{device['device_id']}", json={"name": "Updated"}).json()
    assert updated["name"] == "Updated"
    assert client.patch("/api/hardware-companion/devices/missing", json={"name": "x"}).status_code == 404


def test_settings_update_keeps_safety_invariants():
    settings = client.get("/api/hardware-companion/settings").json()
    assert settings["background_listening"] is False
    assert settings["wake_word_listener"] is False
    updated = client.patch("/api/hardware-companion/settings", json={"companion_mode": "push_to_talk_ready"}).json()
    assert updated["companion_mode"] == "push_to_talk_ready"
    # Safety invariants stay locked regardless of mode.
    assert updated["background_listening"] is False
    assert updated["wake_word_listener"] is False
    assert updated["microphone_recording"] is False
    assert updated["requires_user_activation"] is True


def test_readiness_check():
    device = _create_device(has_mic=True, has_speaker=True, local_processing=True)
    check = client.post("/api/hardware-companion/readiness-checks", json={"device_id": device["device_id"]}).json()
    assert check["check_id"]
    assert check["readiness"] in {"ready", "partial", "not_ready"}
    assert check["total"] == len(check["checklist"])
    assert "no hardware is accessed" in check["note"].lower()
    listed = client.get("/api/hardware-companion/readiness-checks").json()
    assert any(c["check_id"] == check["check_id"] for c in listed["readiness_checks"])


def test_session_create_and_list():
    session = client.post("/api/hardware-companion/sessions", json={"title": "Morning brief"}).json()
    assert session["session_id"]
    assert session["activation"] == "user_activated"
    assert session["background_listening"] is False
    listed = client.get("/api/hardware-companion/sessions").json()
    assert any(s["session_id"] == session["session_id"] for s in listed["sessions"])


def test_dashboard_works_and_no_hardware_access():
    body = client.get("/api/hardware-companion/dashboard").json()
    for key in ("device_count", "session_count", "companion_mode", "available_modes", "safety_rules", "note"):
        assert key in body
    assert body["background_listening"] is False
    assert body["microphone_recording"] is False
    assert body["wake_word_listener"] is False
    assert "no mic recording" in body["note"].lower()


def test_audit_and_governance_written():
    before = client.get("/api/governance").json()["total_events"]
    _create_device()
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "companion_device_created" in actions
    audit = client.get("/api/hardware-companion/audit").json()
    assert audit["count"] >= 1


def test_regression_existing_endpoints():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/organization-os/dashboard").status_code == 200
    assert client.get("/api/simulation-world/dashboard").status_code == 200
