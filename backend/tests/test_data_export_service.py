from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_export_bundle_structure():
    bundle = client.post("/api/data-export/bundle").json()
    for key in ("bundle_version", "created_at", "collections", "total_items", "note"):
        assert key in bundle
    assert isinstance(bundle["collections"], dict)
    assert "no secret values" in bundle["note"].lower()


def test_export_then_import_roundtrip_is_nondestructive():
    # Create a connector so there's content, then export.
    client.post("/api/mcp/connectors", json={"slug": "github", "name": "v59 GH"})
    bundle = client.post("/api/data-export/bundle").json()
    # Importing the same bundle should add 0 new (all ids already exist) — non-destructive.
    result = client.post("/api/data-export/import", json={"bundle": bundle}).json()
    assert result["total_imported"] == 0
    assert "non-destructive" in result["note"].lower()


def test_import_new_items_merges():
    # A synthetic bundle with a brand-new connector id should import 1.
    fake_bundle = {
        "bundle_version": "1.0",
        "collections": {
            "playbooks.json": [
                {"playbook_id": "v59-import-test-id", "name": "Imported playbook", "steps": [], "step_count": 0}
            ]
        },
    }
    result = client.post("/api/data-export/import", json={"bundle": fake_bundle}).json()
    assert result["imported"].get("playbooks.json", 0) >= 1
    # Re-importing the same id skips it.
    result2 = client.post("/api/data-export/import", json={"bundle": fake_bundle}).json()
    assert result2["imported"].get("playbooks.json", 0) == 0
    assert result2["skipped_existing"].get("playbooks.json", 0) >= 1


def test_import_ignores_non_allowlisted_collections():
    result = client.post("/api/data-export/import", json={"bundle": {"collections": {"governance_log.json": [{"id": "x"}]}}}).json()
    # governance_log is not exportable → ignored.
    assert "governance_log.json" not in result["imported"]


def test_import_invalid_bundle_400():
    assert client.post("/api/data-export/import", json={"bundle": {"nope": 1}}).status_code == 400


def test_summary_and_analytics():
    client.post("/api/data-export/bundle")
    s = client.get("/api/data-export/summary").json()
    for key in ("exportable_collections", "current_item_counts", "export_events", "import_events", "note"):
        assert key in s
    assert "no external upload" in s["note"].lower()
    analytics = client.get("/api/analytics").json()
    for key in ("data_exports", "data_imports"):
        assert key in analytics


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/data-export/bundle")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "data_exported" in actions


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/scheduled-tasks/summary").status_code == 200
    assert client.get("/api/operating-layer-2/dashboard").status_code == 200
