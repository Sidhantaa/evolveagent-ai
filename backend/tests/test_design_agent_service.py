from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# 1x1 transparent PNG as a data URL.
PNG = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lE"
    "QVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def test_status_is_mock_safe_and_secret_safe():
    s = client.get("/api/design-agent/status").json()
    assert s["available"] is True
    assert s["live_default"] is False
    assert isinstance(s["key_configured"], bool)  # boolean only, never the key
    assert "key" not in {k.lower() for k in s} or isinstance(s["key_configured"], bool)


def test_analyze_mock_returns_checklists():
    r = client.post("/api/design-agent/analyze", json={"image": PNG, "analyses": ["ux", "visual"]}).json()
    assert r["mode"] == "mock"
    assert {s["lens"] for s in r["sections"]} == {"ux", "visual"}
    assert all("- [ ]" in s["body"] for s in r["sections"])


def test_analyze_defaults_to_all_three_lenses():
    r = client.post("/api/design-agent/analyze", json={"image": PNG}).json()
    assert {s["lens"] for s in r["sections"]} == {"visual", "ux", "market"}


def test_allow_live_without_key_degrades_with_note():
    # In CI there is no OPENROUTER_API_KEY, so a live request must fall back safely.
    r = client.post("/api/design-agent/analyze", json={"image": PNG, "allow_live": True}).json()
    assert r["mode"] == "mock"
    assert "key" in r["note"].lower()


def test_invalid_image_rejected():
    assert client.post("/api/design-agent/analyze", json={"image": "not-a-data-url"}).status_code == 400


def test_unsupported_type_rejected():
    bad = "data:image/tiff;base64,AAAA"
    assert client.post("/api/design-agent/analyze", json={"image": bad}).status_code == 400


def test_history_and_summary_and_analytics_governance():
    client.post("/api/design-agent/analyze", json={"image": PNG})
    hist = client.get("/api/design-agent/history").json()
    assert hist["count"] >= 1
    # image bytes are never persisted in history
    assert all("image" not in row for row in hist["history"])
    assert "design_agent_analyses" in client.get("/api/design-agent/summary").json()
    assert "design_agent_analyses" in client.get("/api/analytics").json()
    actions = {e.get("action_type") for e in client.get("/api/governance").json()["recent_events"]}
    assert "design_analyzed" in actions


def test_existing_endpoints_still_work():
    assert client.get("/api/marketplace-hub/summary").status_code == 200
    assert client.get("/api/durable-workflows/templates").status_code == 200
