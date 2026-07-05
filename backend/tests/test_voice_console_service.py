from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_status_privacy_guarantees():
    s = client.get("/api/voice-console/status").json()
    assert s["available"] is True
    assert s["push_to_talk_only"] is True
    assert s["always_on_recording"] is False
    assert s["stores_audio"] is False


def test_default_settings():
    s = client.get("/api/voice-console/settings", params={"workspace_id": "ws-default"}).json()
    assert s["workspace_id"] == "ws-default"
    assert s["rate"] == 1.0 and s["pitch"] == 1.0 and s["volume"] == 1.0
    assert s["read_aloud"] is False
    assert s["store_transcripts"] is False


def test_update_and_persist_settings():
    r = client.put("/api/voice-console/settings", json={
        "workspace_id": "ws1", "voice_name": "Samantha", "rate": 1.4, "read_aloud": True,
    }).json()
    assert r["voice_name"] == "Samantha" and r["rate"] == 1.4 and r["read_aloud"] is True
    got = client.get("/api/voice-console/settings", params={"workspace_id": "ws1"}).json()
    assert got["voice_name"] == "Samantha" and got["read_aloud"] is True
    # partial update keeps prior fields
    r2 = client.put("/api/voice-console/settings", json={"workspace_id": "ws1", "pitch": 1.2}).json()
    assert r2["voice_name"] == "Samantha" and r2["pitch"] == 1.2


def test_rate_is_clamped():
    r = client.put("/api/voice-console/settings", json={"workspace_id": "ws-clamp", "rate": 3.0}).json()
    assert r["rate"] == 2.0  # service clamps display range to <= 2.0


def test_activity_metadata_only_by_default():
    r = client.post("/api/voice-console/activity", json={
        "kind": "transcribe", "workspace_id": "ws2", "text": "book me a flight to tokyo",
    }).json()
    assert r["char_count"] == len("book me a flight to tokyo")
    assert "transcript" not in r  # not stored unless opted in


def test_activity_stores_transcript_only_when_opted_in():
    client.put("/api/voice-console/settings", json={"workspace_id": "ws3", "store_transcripts": True})
    r = client.post("/api/voice-console/activity", json={
        "kind": "transcribe", "workspace_id": "ws3", "text": "remember this note",
    }).json()
    assert r.get("transcript") == "remember this note"


def test_unknown_kind_rejected():
    assert client.post("/api/voice-console/activity", json={"kind": "record_forever", "workspace_id": "ws4"}).status_code == 400


def test_events_and_clear():
    client.post("/api/voice-console/activity", json={"kind": "speak", "workspace_id": "ws5"})
    ev = client.get("/api/voice-console/events", params={"workspace_id": "ws5"}).json()
    assert ev["count"] >= 1
    cleared = client.delete("/api/voice-console/events", params={"workspace_id": "ws5"}).json()
    assert cleared["cleared"] >= 1
    assert client.get("/api/voice-console/events", params={"workspace_id": "ws5"}).json()["count"] == 0


def test_summary_and_analytics_and_governance():
    client.post("/api/voice-console/activity", json={"kind": "listen_start", "workspace_id": "ws6"})
    summary = client.get("/api/voice-console/summary").json()
    assert "voice_console_events" in summary and summary["push_to_talk_only"] is True
    assert "voice_console_events" in client.get("/api/analytics").json()
    actions = {e.get("action_type") for e in client.get("/api/governance").json()["recent_events"]}
    assert "voice_activity" in actions or "voice_settings_updated" in actions


def test_existing_endpoints_still_work():
    assert client.get("/api/agent-studio/summary").status_code == 200
    assert client.get("/api/git-intel/status").status_code == 200
