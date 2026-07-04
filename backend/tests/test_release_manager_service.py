from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_has_checklists():
    dash = client.get("/api/release-manager/dashboard").json()
    for key in ("version_checklist", "demo_checklist", "linear_sync_checklist", "tag_planner"):
        assert key in dash
    assert "no git tag/push" in dash["note"].lower()


def test_changelog_generated():
    r = client.get("/api/release-manager/changelog").json()
    assert r["format"] == "markdown"
    assert "Changelog" in r["content"]
    assert r["version_groups"] >= 5


def test_tag_planner_suggests_semver():
    dash = client.get("/api/release-manager/dashboard").json()
    tp = dash["tag_planner"]
    assert tp["suggested_patch"] == "v90.0.1"
    assert tp["suggested_minor"] == "v90.1.0"
    assert tp["suggested_major"] == "v91.0.0"


def test_pr_summary_generator():
    r = client.post("/api/release-manager/pr-summary", json={"title": "v89", "changes": ["added X", "fixed Y"]}).json()
    assert "## v89" in r["content"]
    assert "added X" in r["content"]


def test_release_notes_generator():
    r = client.post("/api/release-manager/release-notes", json={"version": "v89.0", "highlights": ["Release Manager"]}).json()
    assert "Release v89.0" in r["content"]
    assert "Release Manager" in r["content"]


def test_summary_and_analytics():
    assert "generators" in client.get("/api/release-manager/summary").json()
    assert "release_manager_checklists" in client.get("/api/analytics").json()


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/release-manager/changelog")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "changelog_generated" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/qa-center/summary").status_code == 200
    assert client.get("/api/integration-hub/summary").status_code == 200
