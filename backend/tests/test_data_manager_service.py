from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_browse_lists_collections():
    r = client.get("/api/data-manager/browse").json()
    assert r["count"] >= 10
    row = r["collections"][0]
    for key in ("collection", "records", "bytes"):
        assert key in row
    assert row["collection"].endswith(".json")


def test_usage_totals():
    r = client.get("/api/data-manager/usage").json()
    for key in ("total_bytes", "total_kb", "collection_count", "largest"):
        assert key in r
    assert r["total_bytes"] >= 0


def test_cleanup_suggestions_are_advisory():
    r = client.get("/api/data-manager/cleanup-suggestions").json()
    assert "suggestions" in r
    assert "never deletes" in r["note"].lower()


def test_redaction_preview_counts_only():
    r = client.post("/api/data-manager/redaction-preview", json={"collection": "governance_log.json"}).json()
    assert "sensitive_matches" in r and "total_matches" in r
    assert "nothing is redacted" in r["note"].lower()


def test_redaction_unknown_collection_404():
    assert client.post("/api/data-manager/redaction-preview", json={"collection": "nope.json"}).status_code == 404


def test_summary_and_analytics():
    assert "collection_count" in client.get("/api/data-manager/summary").json()
    analytics = client.get("/api/analytics").json()
    for key in ("data_manager_collections", "data_manager_total_kb"):
        assert key in analytics


def test_browse_is_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/data-manager/browse")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "data_browsed" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/governance-console/summary").status_code == 200
    assert client.get("/api/permissions/summary").status_code == 200
