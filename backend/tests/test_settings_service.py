from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_settings_has_categories_and_enforced_safety():
    data = client.get("/api/settings").json()
    for cat in ("provider", "modes", "features", "safety", "voice", "theme"):
        assert cat in data["settings"]
    assert len(data["enforced_safety"]) >= 5
    assert any("shell" in s.lower() for s in data["enforced_safety"])


def test_update_allowed_setting():
    result = client.patch("/api/settings", json={"settings": {"theme": {"mode": "light"}}}).json()
    assert result["settings"]["theme"]["mode"] == "light"
    assert result["applied"].get("theme", {}).get("mode") == "light"
    # revert
    client.patch("/api/settings", json={"settings": {"theme": {"mode": "dark"}}})


def test_bad_value_rejected():
    result = client.patch("/api/settings", json={"settings": {"theme": {"mode": "rainbow"}}}).json()
    assert any("theme.mode" in r for r in result["rejected"])
    assert result["settings"]["theme"]["mode"] in ("dark", "light")


def test_secret_like_keys_are_rejected():
    result = client.patch("/api/settings", json={"settings": {"provider": {"api_key": "sk-123", "openai_token": "x"}}}).json()
    joined = " ".join(result["rejected"])
    assert "forbidden" in joined
    # nothing secret-like stored
    assert "api_key" not in result["settings"].get("provider", {})


def test_unknown_category_rejected():
    result = client.patch("/api/settings", json={"settings": {"nonsense": {"x": 1}}}).json()
    assert "nonsense" in result["rejected"]


def test_export_import_roundtrip():
    client.patch("/api/settings", json={"settings": {"voice": {"push_to_talk": False}}})
    exported = client.get("/api/settings/export").json()
    assert "no secret" in exported["note"].lower()
    imported = client.post("/api/settings/import", json={"settings": exported["settings"]}).json()
    assert imported["settings"]["voice"]["push_to_talk"] is False
    client.post("/api/settings/reset")


def test_reset_restores_defaults():
    client.patch("/api/settings", json={"settings": {"theme": {"mode": "light"}}})
    data = client.post("/api/settings/reset").json()
    assert data["settings"]["theme"]["mode"] == "dark"


def test_import_invalid_400():
    assert client.post("/api/settings/import", json={"settings": "notadict"}).status_code == 422


def test_governance_logged_and_analytics():
    before = client.get("/api/governance").json()["total_events"]
    client.patch("/api/settings", json={"settings": {"modes": {"deep_mode_default": True}}})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "settings_updated" in {e.get("action_type") for e in after["recent_events"]}
    assert "settings_editable_keys" in client.get("/api/analytics").json()
    client.post("/api/settings/reset")


def test_existing_endpoints_still_work():
    assert client.get("/api/demo/summary").status_code == 200
    assert client.get("/api/features/summary").status_code == 200
