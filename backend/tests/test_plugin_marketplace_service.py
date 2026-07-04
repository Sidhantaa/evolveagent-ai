from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_safe_plugin_enabled():
    r = client.post("/api/plugin-marketplace/register", json={
        "name": "Read-only summarizer", "description": "summarizes text", "permissions": ["read", "analyze"],
    }).json()
    assert r["validation"]["valid"] is True
    assert r["enabled"] is True  # no high-risk permissions
    assert r["health"]["score"] >= 70


def test_register_high_risk_plugin_disabled_by_default():
    r = client.post("/api/plugin-marketplace/register", json={
        "name": "Shell runner", "description": "runs shell", "permissions": ["shell", "execute"],
    }).json()
    assert r["enabled"] is False  # high-risk stays disabled
    assert r["validation"]["high_risk_permissions"]


def test_enabling_high_risk_is_blocked():
    reg = client.post("/api/plugin-marketplace/register", json={"name": "Net tool", "permissions": ["network"]}).json()
    result = client.post(f"/api/plugin-marketplace/{reg['plugin_id']}/toggle", json={"enabled": True}).json()
    assert result["blocked"] is True
    assert result["enabled"] is False


def test_toggle_safe_plugin():
    reg = client.post("/api/plugin-marketplace/register", json={"name": "Safe", "permissions": ["read"]}).json()
    off = client.post(f"/api/plugin-marketplace/{reg['plugin_id']}/toggle", json={"enabled": False}).json()
    assert off["enabled"] is False
    on = client.post(f"/api/plugin-marketplace/{reg['plugin_id']}/toggle", json={"enabled": True}).json()
    assert on["enabled"] is True


def test_test_runner_is_mock():
    reg = client.post("/api/plugin-marketplace/register", json={"name": "T", "permissions": ["read"]}).json()
    r = client.post(f"/api/plugin-marketplace/{reg['plugin_id']}/test").json()
    assert r["result"] == "dry_ok"
    assert "nothing is executed" in r["note"].lower()


def test_catalog_and_activity():
    assert "plugins" in client.get("/api/plugin-marketplace/catalog").json()
    assert "events" in client.get("/api/plugin-marketplace/activity").json()


def test_summary_and_analytics():
    assert "total_plugins" in client.get("/api/plugin-marketplace/summary").json()
    analytics = client.get("/api/analytics").json()
    for key in ("marketplace_plugins", "marketplace_plugins_enabled"):
        assert key in analytics


def test_register_is_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/plugin-marketplace/register", json={"name": "Logged", "permissions": ["read"]})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "plugin_registered" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/export-center/summary").status_code == 200
    assert client.get("/api/import-center/summary").status_code == 200
