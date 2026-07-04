from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_lists_providers():
    data = client.get("/api/provider-control/dashboard").json()
    ids = {p["id"] for p in data["providers"]}
    for expected in ("openai", "anthropic", "gemini", "mistral", "local"):
        assert expected in ids
    # local is always ready
    assert next(p for p in data["providers"] if p["id"] == "local")["ready"] is True
    assert "fallback_policy" in data and "cost_estimate_usd" in data


def test_key_check_is_boolean_only():
    data = client.get("/api/provider-control/key-check").json()
    for check in data["checks"]:
        for key in check["keys"]:
            assert set(key.keys()) == {"key_name", "is_set"}
            assert isinstance(key["is_set"], bool)  # never a value
    assert "booleans only" in data["note"].lower()


def test_update_model_and_capability_prefs():
    result = client.patch("/api/provider-control", json={
        "model_by_task": {"coding": "claude-opus-4-8"},
        "capability_modes": {"chat": "real"},
    }).json()
    assert result["config"]["model_by_task"]["coding"] == "claude-opus-4-8"
    assert result["config"]["capability_modes"]["chat"] == "real"
    assert result["rejected"] == []


def test_bad_capability_mode_rejected():
    result = client.patch("/api/provider-control", json={"capability_modes": {"chat": "turbo"}}).json()
    assert any("capability_modes.chat" in r for r in result["rejected"])


def test_unknown_task_rejected():
    result = client.patch("/api/provider-control", json={"model_by_task": {"nonsense": "x"}}).json()
    assert any("model_by_task.nonsense" in r for r in result["rejected"])


def test_summary_and_analytics():
    summary = client.get("/api/provider-control/summary").json()
    for key in ("total_providers", "ready_providers", "capability_modes"):
        assert key in summary
    analytics = client.get("/api/analytics").json()
    for key in ("provider_control_ready_providers", "provider_control_total_providers"):
        assert key in analytics


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/provider-control/dashboard")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "provider_control_viewed" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/settings").status_code == 200
    assert client.get("/api/demo/summary").status_code == 200
