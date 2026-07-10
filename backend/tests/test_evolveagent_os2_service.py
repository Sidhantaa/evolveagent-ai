from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_command_center_indexes_all_domains():
    cc = client.get("/api/os2/command-center").json()
    assert cc["version"] == "v200.0"
    assert cc["total_systems"] >= 25
    assert 0 <= cc["coverage_pct"] <= 100
    domains = {d["domain"] for d in cc["domains"]}
    for expected in ("Core", "MCP Arc", "Ops & Observability"):
        assert expected in domains
    assert "not AGI" in cc["disclaimer"]


# ------------------------------------------------------------------
# v200 — the "unified" command center was missing every v100-v190 domain
# built this session, and had one latent bug (a "Chief of staff" entry
# pointing at a filename that was never actually written to).
# ------------------------------------------------------------------
def test_command_center_indexes_v100_through_v190_domains():
    cc = client.get("/api/os2/command-center").json()
    domains = {d["domain"] for d in cc["domains"]}
    for expected in (
        "Real Foundation (v100)", "Workflow Automation (v120)",
        "Autonomous Software Team (v150)", "Agent Marketplace (v160)",
        "Multimodal AI OS (v170)", "Enterprise AI OS (v190)",
    ):
        assert expected in domains


def test_chief_of_staff_command_center_entry_reflects_real_usage():
    """Regression: this entry used to point at chief_of_staff_items.json, a
    filename ChiefOfStaffService never wrote to, so it always showed
    active=false regardless of real usage."""
    client.post("/api/chief-of-staff/daily-plan", json={})
    cc = client.get("/api/os2/command-center").json()
    personal = next(d for d in cc["domains"] if d["domain"] == "Personal & Org")
    chief = next(s for s in personal["systems"] if s["label"] == "Chief of staff")
    assert chief["active"] is True
    assert chief["record_count"] > 0


def test_new_domains_reflect_real_data_from_this_session():
    client.post("/api/memory-v2/add", json={"text": "os2 coverage check", "kind": "note"})
    client.post("/api/marketplace-hub/listings", json={
        "kind": "workflow", "manifest": {"name": "OS2 check", "steps": [{"name": "x"}]},
    })
    cc = client.get("/api/os2/command-center").json()
    foundation = next(d for d in cc["domains"] if d["domain"] == "Real Foundation (v100)")
    memory_v2 = next(s for s in foundation["systems"] if s["label"] == "Memory v2 (semantic recall)")
    assert memory_v2["active"] is True
    marketplace = next(d for d in cc["domains"] if d["domain"] == "Agent Marketplace (v160)")
    hub = next(s for s in marketplace["systems"] if s["label"] == "Marketplace hub")
    assert hub["active"] is True


def test_command_center_marks_active_by_data():
    # A run creates governance events, so the Core/Governance system is active.
    client.post("/api/run", json={"user_input": "Warm up EvolveAgent."})
    cc = client.get("/api/os2/command-center").json()
    core = next(d for d in cc["domains"] if d["domain"] == "Core")
    gov = next(s for s in core["systems"] if s["route"] == "/api/governance")
    assert gov["active"] is True
    assert gov["record_count"] > 0


def test_dashboard_bundles_scorecard_health_and_stats():
    dash = client.get("/api/os2/dashboard").json()
    for key in ("command_center", "scorecard", "health", "stats", "safety_boundaries", "disclaimer"):
        assert key in dash
    assert dash["stats"]["implementation_versions"] == 200
    assert "overall_grade" in dash["scorecard"]
    assert any("shell" in boundary.lower() for boundary in dash["safety_boundaries"])


def test_snapshot_create_and_list():
    snap = client.post("/api/os2/snapshots").json()
    for key in ("snapshot_id", "active_systems", "total_systems", "coverage_pct", "overall_grade"):
        assert key in snap
    listing = client.get("/api/os2/snapshots").json()
    assert listing["count"] >= 1
    assert any(s["snapshot_id"] == snap["snapshot_id"] for s in listing["snapshots"])


def test_report_has_headline_and_disclaimer():
    report = client.post("/api/os2/report").json()
    assert report["version"] == "v200.0"
    assert "200 implementation versions" in report["headline"]
    assert "not AGI" in report["disclaimer"]
    assert len(report["safety_boundaries"]) >= 5


def test_analytics_includes_os2():
    analytics = client.get("/api/analytics").json()
    for key in ("os2_active_systems", "os2_total_systems", "os2_coverage_pct"):
        assert key in analytics


def test_governance_logged_on_snapshot():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/os2/snapshots")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "os2_snapshot_created" in actions


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/data-export/summary").status_code == 200
    assert client.get("/api/operating-layer-2/dashboard").status_code == 200
