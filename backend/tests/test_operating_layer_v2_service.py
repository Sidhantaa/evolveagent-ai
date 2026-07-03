from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

DISCLAIMER = "this is not agi"


def test_dashboard_and_disclaimer():
    body = client.get("/api/operating-layer-2/dashboard").json()
    for key in ("version", "overall_score", "overall_grade", "dimensions", "capability_groups", "coverage_pct", "safety_boundaries", "disclaimer"):
        assert key in body
    assert body["version"] == "v55.0"
    assert DISCLAIMER in body["disclaimer"].lower()


def test_capabilities_include_new_versions():
    body = client.get("/api/operating-layer-2/capabilities").json()
    groups = {g["group"] for g in body["capability_groups"]}
    for expected in ("MCP Connectors", "MCP Execution", "MCP Policy", "Secret Registry", "Health", "Usage", "Retrieval", "Evaluation", "Playbooks"):
        assert expected in groups
    assert 0 <= body["coverage_pct"] <= 100


def test_scorecard_dimensions_and_grade():
    body = client.get("/api/operating-layer-2/scorecard").json()
    assert 0 <= body["overall_score"] <= 100
    assert body["overall_grade"] in ("A", "B", "C", "D", "F")
    names = {d["name"] for d in body["dimensions"]}
    for expected in ("capability_coverage", "governance", "health", "approvals_backlog"):
        assert expected in names
    for d in body["dimensions"]:
        assert d["grade"] in ("A", "B", "C", "D", "F")


def test_snapshot_create_and_list():
    snapshot = client.post("/api/operating-layer-2/snapshots").json()
    assert snapshot["snapshot_id"]
    assert snapshot["overall_grade"] in ("A", "B", "C", "D", "F")
    listed = client.get("/api/operating-layer-2/snapshots").json()
    assert any(s.get("snapshot_id") == snapshot["snapshot_id"] for s in listed["snapshots"])


def test_report_generated_with_disclaimer_and_boundaries():
    report = client.post("/api/operating-layer-2/report").json()
    assert report["report_id"]
    assert report["version"] == "v55.0"
    assert report["headline"]
    assert DISCLAIMER in report["disclaimer"].lower()
    joined = " ".join(report["safety_boundaries"]).lower()
    assert "no unrestricted shell" in joined
    assert "mock by default" in joined


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/operating-layer-2/snapshots")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "operating_layer_v2_snapshot_created" in actions


def test_analytics_includes_v2_fields():
    analytics = client.get("/api/analytics").json()
    for key in ("operating_layer_v2_score", "operating_layer_v2_grade", "operating_layer_v2_coverage_pct"):
        assert key in analytics


def test_v40_operating_layer_still_works():
    # The original v40 operating layer is untouched.
    assert client.get("/api/operating-layer/dashboard").status_code == 200


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/playbooks/summary").status_code == 200
