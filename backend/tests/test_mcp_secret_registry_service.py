from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register(**payload) -> dict:
    response = client.post("/api/mcp/secrets", json=payload)
    assert response.status_code == 200
    return response.json()


def test_register_records_key_name_not_value(monkeypatch):
    monkeypatch.setenv("V47_TEST_KEY", "super-secret-abcdef-1234567890")
    ref = _register(key_name="V47_TEST_KEY", label="Test key", owner="me", category="api_key")
    assert ref["ref_id"]
    assert ref["key_name"] == "V47_TEST_KEY"
    assert ref["is_set"] is True
    # The value must never appear anywhere in the response.
    assert "super-secret-abcdef-1234567890" not in str(ref)
    assert "value" not in ref
    listed = client.get("/api/mcp/secrets").json()
    assert "super-secret-abcdef-1234567890" not in str(listed)


def test_unset_key_reports_false(monkeypatch):
    monkeypatch.delenv("V47_MISSING_KEY", raising=False)
    ref = _register(key_name="V47_MISSING_KEY")
    assert ref["is_set"] is False


def test_summary_counts(monkeypatch):
    monkeypatch.setenv("V47_SET", "x")
    monkeypatch.delenv("V47_UNSET", raising=False)
    _register(key_name="V47_SET")
    _register(key_name="V47_UNSET")
    summary = client.get("/api/mcp/secrets/summary").json()
    for key in ("total_refs", "set_count", "unset_count", "rotation_due_count", "note"):
        assert key in summary
    assert summary["total_refs"] >= 2
    assert "never stored" in summary["note"].lower()


def test_rotation_due_flag():
    # rotation_days=1 with no last_rotated → due immediately (created just now, but
    # created_at is "now", so not due yet). Use a service-level check via update.
    ref = _register(key_name="V47_ROT", rotation_days=1)
    # Freshly created → not due yet.
    assert ref["rotation_due"] is False


def test_mark_rotated_updates_timestamp():
    ref = _register(key_name="V47_ROTATE_ME", rotation_days=30)
    rotated = client.post(f"/api/mcp/secrets/{ref['ref_id']}/rotate").json()
    assert rotated["last_rotated_at"] is not None
    assert rotated["rotation_due"] is False
    assert client.post("/api/mcp/secrets/missing/rotate").status_code == 404


def test_update_ref_metadata_never_accepts_value():
    ref = _register(key_name="V47_UPD")
    updated = client.patch(f"/api/mcp/secrets/{ref['ref_id']}", json={"owner": "new-owner", "rotation_days": 90}).json()
    assert updated["owner"] == "new-owner"
    assert updated["rotation_days"] == 90
    assert "value" not in updated
    assert client.patch("/api/mcp/secrets/missing", json={"owner": "x"}).status_code == 404


def test_governance_logged_on_register():
    before = client.get("/api/governance").json()["total_events"]
    _register(key_name="V47_GOV")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "secret_ref_registered" in actions


def test_analytics_includes_secret_fields():
    analytics = client.get("/api/analytics").json()
    for key in ("mcp_secret_refs_total", "mcp_secret_refs_set", "mcp_secret_refs_rotation_due"):
        assert key in analytics


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/mcp/summary").status_code == 200
    assert client.get("/api/mcp/audit/summary").status_code == 200
    assert client.get("/api/operating-layer/dashboard").status_code == 200
