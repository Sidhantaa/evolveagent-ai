from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_workflow_create_and_list():
    workflow = client.post(
        "/api/business-operator/workflows",
        json={"workflow_type": "lead_pipeline", "title": "Q3 pipeline"},
    ).json()
    assert workflow["workflow_id"]
    assert workflow["workflow_type"] == "lead_pipeline"
    assert workflow["draft_only"] is True
    assert workflow["next_steps"]
    listed = client.get("/api/business-operator/workflows").json()
    assert any(w["workflow_id"] == workflow["workflow_id"] for w in listed["workflows"])


def test_report_create_and_list():
    report = client.post("/api/business-operator/reports", json={"title": "Ops report"}).json()
    assert report["report_id"]
    assert "kpis" in report
    assert report["headline"]
    listed = client.get("/api/business-operator/reports").json()
    assert any(r["report_id"] == report["report_id"] for r in listed["reports"])


def test_kpi_snapshot():
    snapshot = client.post("/api/business-operator/kpi-snapshots", json={}).json()
    assert snapshot["snapshot_id"]
    assert "kpis" in snapshot
    listed = client.get("/api/business-operator/kpi-snapshots").json()
    assert any(s["snapshot_id"] == snapshot["snapshot_id"] for s in listed["kpi_snapshots"])


def test_approval_create_update_and_no_external_send():
    approval = client.post(
        "/api/business-operator/approvals",
        json={"kind": "external_send", "title": "Send campaign email", "detail": "Newsletter blast"},
    ).json()
    assert approval["approval_id"]
    assert approval["status"] == "pending"
    # Approving records a decision but performs no real external action.
    assert "no real send" in approval["note"].lower()
    updated = client.patch(f"/api/business-operator/approvals/{approval['approval_id']}", json={"decision": "approved"}).json()
    assert updated["status"] == "approved"
    listed = client.get("/api/business-operator/approvals").json()
    assert any(a["approval_id"] == approval["approval_id"] for a in listed["approvals"])
    assert client.patch("/api/business-operator/approvals/missing", json={"decision": "approved"}).status_code == 404


def test_audit_record_written():
    client.post("/api/business-operator/workflows", json={"workflow_type": "support_triage"})
    audit = client.get("/api/business-operator/audit").json()
    assert audit["count"] >= 1
    event_types = {entry["event_type"] for entry in audit["audit"]}
    assert "workflow_created" in event_types or "report_created" in event_types


def test_dashboard_works_and_draft_only():
    body = client.get("/api/business-operator/dashboard").json()
    for key in ("total_workflows", "pending_approvals", "total_reports", "total_kpi_snapshots", "kpis", "draft_only"):
        assert key in body
    assert body["draft_only"] is True
    assert "no real email send" in body["safety_note"].lower()


def test_governance_event_written():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/business-operator/workflows", json={"workflow_type": "custom", "title": "Gov workflow"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "business_workflow_created" in actions


def test_does_not_duplicate_v18_business_endpoints():
    # v18 surface (/api/business/*) and v33 surface (/api/business-operator/*) coexist.
    assert client.get("/api/business/dashboard").status_code == 200
    assert client.get("/api/business-operator/dashboard").status_code == 200


def test_regression_existing_endpoints():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/saas-builder/dashboard").status_code == 200
    assert client.get("/api/team-manager/dashboard").status_code == 200
