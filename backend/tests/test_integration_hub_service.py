from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cards_list_integrations():
    r = client.get("/api/integration-hub/cards").json()
    ids = {c["id"] for c in r["integrations"]}
    for expected in ("slack", "notion", "linear", "github"):
        assert expected in ids
    assert "secret values are never displayed" in r["note"].lower()


def test_connection_status_is_boolean_no_secret():
    r = client.get("/api/integration-hub/cards").json()
    for card in r["integrations"]:
        assert isinstance(card["connected"], bool)
        assert "required_key" in card  # name only
        # ensure no value-like field is present
        assert "key_value" not in card and "token" not in card
        if not card["connected"]:
            assert card["error"]


def test_dry_run_no_network():
    r = client.post("/api/integration-hub/slack/dry-run").json()
    assert r["result"] in ("ready", "missing_key")
    assert "no real network call" in r["note"].lower()
    assert "scopes" in r


def test_dry_run_unknown_404():
    assert client.post("/api/integration-hub/nope/dry-run").status_code == 404


def test_summary_and_analytics():
    assert "integrations" in client.get("/api/integration-hub/summary").json()
    analytics = client.get("/api/analytics").json()
    for key in ("integration_hub_total", "integration_hub_connected"):
        assert key in analytics


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/integration-hub/cards")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "integration_cards_viewed" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/plugin-marketplace/summary").status_code == 200
    assert client.get("/api/export-center/summary").status_code == 200
