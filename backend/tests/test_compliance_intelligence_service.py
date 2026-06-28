from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_policy_crud():
    policy = client.post(
        "/api/compliance/policies",
        json={"name": "Data retention", "category": "privacy", "rules": ["Keep 90 days", "Encrypt at rest"]},
    ).json()
    assert policy["policy_id"]
    assert policy["status"] == "draft"
    assert "not legal advice" in policy["disclaimer"].lower()
    listed = client.get("/api/compliance/policies").json()
    assert any(p["policy_id"] == policy["policy_id"] for p in listed["policies"])
    updated = client.patch(f"/api/compliance/policies/{policy['policy_id']}", json={"status": "active"}).json()
    assert updated["status"] == "active"
    assert client.patch("/api/compliance/policies/missing", json={"status": "active"}).status_code == 404


def test_sensitive_classifier_detects_pii_phi_secrets():
    finding = client.post(
        "/api/compliance/scan",
        json={
            "content": "Patient John, MRN 12345, diagnosis flu. Email john@example.com, SSN 123-45-6789. OPENAI_API_KEY=sk-abcdef1234567890",
            "label": "intake note",
        },
    ).json()
    assert finding["secrets_detected"] is True
    assert finding["pii_detected"] is True
    assert "email" in finding["pii_types"]
    assert finding["phi_detected"] is True
    assert finding["hipaa_warning"] is True
    assert finding["risk_level"] == "high"
    listed = client.get("/api/compliance/scans").json()
    assert any(s["finding_id"] == finding["finding_id"] for s in listed["scans"])


def test_contract_review_creates_risk_flags():
    review = client.post(
        "/api/compliance/contracts/review",
        json={"title": "Vendor MSA", "content": "This agreement includes indemnity, auto-renew, and termination clauses under governing law."},
    ).json()
    assert review["review_id"]
    assert review["risk_flags"]
    assert review["risk_level"] in {"low", "medium", "high"}
    assert review["recommended_checklist"]
    listed = client.get("/api/compliance/contracts/reviews").json()
    assert any(r["review_id"] == review["review_id"] for r in listed["reviews"])


def test_checklist_generation():
    checklist = client.post("/api/compliance/checklists", json={"framework": "hipaa"}).json()
    assert checklist["checklist_id"]
    assert checklist["framework"] == "hipaa"
    assert isinstance(checklist["items"], list) and checklist["items"]
    listed = client.get("/api/compliance/checklists").json()
    assert any(c["checklist_id"] == checklist["checklist_id"] for c in listed["checklists"])


def test_audit_package_generation():
    package = client.post("/api/compliance/audit-packages", json={"title": "Q3 audit"}).json()
    assert package["package_id"]
    assert "governance_event_count" in package
    assert "contents" in package
    assert "not legal advice" in package["disclaimer"].lower()
    listed = client.get("/api/compliance/audit-packages").json()
    assert any(p["package_id"] == package["package_id"] for p in listed["audit_packages"])


def test_dashboard_works_and_disclaimer_included():
    body = client.get("/api/compliance/dashboard").json()
    for key in ("policy_count", "scan_count", "high_risk_findings", "phi_findings", "contract_review_count", "checklist_count", "disclaimer"):
        assert key in body
    assert "not legal advice" in body["disclaimer"].lower()


def test_does_not_break_existing_compliance_feature():
    # The pre-existing compliance admin feature stays intact.
    assert client.get("/api/compliance/summary").status_code == 200


def test_governance_event_written():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/compliance/policies", json={"name": "Gov policy"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "compliance_policy_created" in actions


def test_regression_existing_endpoints():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/business-operator/dashboard").status_code == 200
    assert client.get("/api/saas-builder/dashboard").status_code == 200
