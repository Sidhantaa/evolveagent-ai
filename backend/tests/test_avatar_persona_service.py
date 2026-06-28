from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_persona_get_and_update():
    persona = client.get("/api/avatar/persona").json()
    assert "avatar_name" in persona
    assert persona["impersonation_allowed"] is False
    assert persona["voice_cloning_allowed"] is False

    updated = client.patch("/api/avatar/persona", json={"avatar_name": "Nova", "tone": "professional", "format": "bullets"}).json()
    assert updated["avatar_name"] == "Nova"
    assert updated["tone"] == "professional"
    assert updated["format"] == "bullets"
    # Safety invariants stay locked even if a client tries to flip them.
    assert updated["impersonation_allowed"] is False
    assert updated["voice_cloning_allowed"] is False


def test_voice_settings_update():
    settings = client.get("/api/avatar/voice-settings").json()
    assert settings["voice_mode"] in {"text_only", "spoken_summary_ready", "disabled"}
    assert settings["voice_cloning_allowed"] is False

    updated = client.patch("/api/avatar/voice-settings", json={"voice_mode": "spoken_summary_ready", "spoken_summary_max_chars": 800}).json()
    assert updated["voice_mode"] == "spoken_summary_ready"
    assert updated["spoken_summary_max_chars"] == 800
    assert updated["voice_cloning_allowed"] is False


def test_meeting_session_create():
    session = client.post("/api/avatar/meeting-sessions", json={"title": "Standup", "context": "Daily standup"}).json()
    assert session["meeting_session_id"]
    assert session["status"] == "planned"
    assert session["requires_consent"] is True
    assert session["planned_notes"]
    listed = client.get("/api/avatar/meeting-sessions").json()
    assert any(s["meeting_session_id"] == session["meeting_session_id"] for s in listed["meeting_sessions"])


def test_consent_record():
    consent = client.post("/api/avatar/consent", json={"scope": "meeting_assistant", "granted": True, "note": "ok"}).json()
    assert consent["consent_id"]
    assert consent["granted"] is True
    assert consent["safety_rules_acknowledged"]


def test_safety_text_present():
    dashboard = client.get("/api/avatar/dashboard").json()
    assert dashboard["impersonation_allowed"] is False
    assert dashboard["voice_cloning_allowed"] is False
    joined = " ".join(dashboard["safety_rules"]).lower()
    assert "never claims to be the user" in joined or "no impersonation" in joined
    assert "no voice cloning" in joined


def test_dashboard_works():
    body = client.get("/api/avatar/dashboard").json()
    for key in ("persona", "voice_settings", "meeting_session_count", "consent_record_count", "safety_rules"):
        assert key in body


def test_governance_event_written():
    before = client.get("/api/governance").json()["total_events"]
    client.patch("/api/avatar/persona", json={"style": "warm"})
    client.post("/api/avatar/consent", json={"granted": True})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert actions & {"avatar_persona_updated", "avatar_consent_recorded"}


def test_generate_stylized_avatar_image():
    persona = client.post(
        "/api/avatar/persona/avatar-image",
        json={"description": "short black hair, glasses, friendly smile, hoodie", "style": "illustrated"},
    ).json()
    assert "avatar_image" in persona
    image = persona["avatar_image"]
    assert image["image_url"]
    assert image["style"] == "illustrated"
    # Mock by default in tests (no real image API).
    assert image["mock_preview"] is True
    assert "not a photo-real" in image["note"].lower()
    # Persona still never claims to be the user.
    assert persona["impersonation_allowed"] is False
    # Persisted on the persona.
    fetched = client.get("/api/avatar/persona").json()
    assert fetched.get("avatar_image", {}).get("image_url")


def test_regression_existing_endpoints():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/training-lab/dashboard").status_code == 200
    assert client.get("/api/device-operator/dashboard").status_code == 200
