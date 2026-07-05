from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_preview_sanitizes_and_does_not_save():
    total_before = client.get("/api/import-center/summary").json()["total_imported"]
    r = client.post("/api/import-center/preview", json={
        "kind": "project_notes",
        "content": "Contact me at alice@example.com about the plan.\n\nSecond note here.",
    }).json()
    assert r["record_count"] >= 2
    assert r["redactions"] >= 1
    assert all("@example.com" not in rec["content"] for rec in r["preview"])  # email redacted
    total_after = client.get("/api/import-center/summary").json()["total_imported"]
    assert total_after == total_before  # preview saves nothing


def test_commit_saves_sanitized_records():
    before = client.get("/api/import-center/summary").json()["total_imported"]
    r = client.post("/api/import-center/commit", json={
        "kind": "markdown",
        "content": "# Heading\n\nBody with token ghp_abcdefghijklmnop here.",
    }).json()
    assert r["imported_count"] >= 1
    assert r["redactions"] >= 1
    after = client.get("/api/import-center/summary").json()["total_imported"]
    assert after > before
    # stored content must be redacted
    recs = client.get("/api/import-center/records?kind=markdown").json()["records"]
    assert all("ghp_" not in rec["content"] for rec in recs)


def test_csv_parsed_into_rows():
    r = client.post("/api/import-center/preview", json={"kind": "csv", "content": "a,b\n1,2\n3,4"}).json()
    assert r["record_count"] == 3  # header + 2 rows


def test_unsupported_kind_400():
    assert client.post("/api/import-center/preview", json={"kind": "exe", "content": "x"}).status_code == 400


def test_summary_and_analytics():
    s = client.get("/api/import-center/summary").json()
    assert "supported_kinds" in s and "by_kind" in s
    assert "import_center_records" in client.get("/api/analytics").json()


def test_commit_is_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/import-center/commit", json={"kind": "document", "content": "some doc"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "import_committed" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/data-manager/summary").status_code == 200
    assert client.get("/api/governance-console/summary").status_code == 200
