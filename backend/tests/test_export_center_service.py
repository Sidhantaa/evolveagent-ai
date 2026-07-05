from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_export_goals_markdown():
    client.post("/api/goals", json={"title": "v85 export goal", "description": "x"})
    r = client.post("/api/export-center/export", json={"kind": "goals", "format": "markdown"}).json()
    assert r["kind"] == "goals" and r["format"] == "markdown"
    assert "Export: goals" in r["content"]


def test_export_json():
    r = client.post("/api/export-center/export", json={"kind": "memory", "format": "json"}).json()
    assert r["format"] == "json"
    assert r["content"].strip().startswith("[")


def test_unsupported_kind_400():
    assert client.post("/api/export-center/export", json={"kind": "nope", "format": "markdown"}).status_code == 400


def test_package_bundles_kinds():
    r = client.post("/api/export-center/package", json={"kinds": ["goals", "memory"], "format": "markdown"}).json()
    assert set(r["kinds"]) == {"goals", "memory"}
    assert "Export: goals" in r["content"] and "Export: memory" in r["content"]


def test_case_study_export():
    r = client.get("/api/export-center/case-study").json()
    assert r["format"] == "markdown"
    assert "EvolveAgent AI" in r["content"] and "Safety" in r["content"]


def test_summary_and_analytics():
    s = client.get("/api/export-center/summary").json()
    assert "supported_kinds" in s and "formats" in s
    assert "export_center_kinds" in client.get("/api/analytics").json()


def test_export_is_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/export-center/export", json={"kind": "goals", "format": "markdown"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "export_generated" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/import-center/summary").status_code == 200
    assert client.get("/api/data-manager/summary").status_code == 200
