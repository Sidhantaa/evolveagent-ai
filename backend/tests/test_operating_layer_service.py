from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

DISCLAIMER_FRAGMENT = "this is not agi"


def test_dashboard_works_and_disclaimer_present():
    body = client.get("/api/operating-layer/dashboard").json()
    for key in ("version", "active_capability_groups", "total_capability_groups", "capability_groups", "safety_boundaries", "disclaimer"):
        assert key in body
    assert body["version"] == "v40.0"
    assert DISCLAIMER_FRAGMENT in body["disclaimer"].lower()


def test_capabilities_returned():
    body = client.get("/api/operating-layer/capabilities").json()
    assert isinstance(body["capability_groups"], list) and body["capability_groups"]
    assert all("group" in g and "active" in g for g in body["capability_groups"])
    assert body["total_group_count"] == len(body["capability_groups"])
    assert DISCLAIMER_FRAGMENT in body["disclaimer"].lower()


def test_snapshot_generated():
    snapshot = client.post("/api/operating-layer/snapshots").json()
    assert snapshot["snapshot_id"]
    assert 0 <= snapshot["readiness_score"] <= 100
    assert snapshot["safety_boundaries"]
    assert DISCLAIMER_FRAGMENT in snapshot["disclaimer"].lower()
    listed = client.get("/api/operating-layer/snapshots").json()
    assert any(s.get("snapshot_id") == snapshot["snapshot_id"] for s in listed["snapshots"])


def test_recommendations_generated():
    rec = client.post("/api/operating-layer/recommendations").json()
    assert rec["recommendation_id"]
    assert isinstance(rec["recommendations"], list) and rec["recommendations"]
    listed = client.get("/api/operating-layer/recommendations").json()
    assert any(r["recommendation_id"] == rec["recommendation_id"] for r in listed["recommendations"])


def test_report_generated_with_disclaimer():
    report = client.post("/api/operating-layer/report").json()
    assert report["report_id"]
    assert report["version"] == "v40.0"
    assert "capability_groups" in report
    assert report["headline"]
    assert DISCLAIMER_FRAGMENT in report["disclaimer"].lower()


def test_safety_boundaries_listed():
    body = client.get("/api/operating-layer/dashboard").json()
    joined = " ".join(body["safety_boundaries"]).lower()
    assert "no unrestricted shell" in joined
    assert "no real external sending" in joined
    assert "no production auth" in joined


def test_governance_and_audit_written():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/operating-layer/snapshots")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "operating_layer_snapshot_created" in actions
    audit = client.get("/api/operating-layer/audit").json()
    assert audit["count"] >= 1


def test_regression_existing_endpoints():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/hardware-companion/dashboard").status_code == 200
    assert client.get("/api/organization-os/dashboard").status_code == 200
    assert client.get("/api/innovation-lab/dashboard").status_code == 200
