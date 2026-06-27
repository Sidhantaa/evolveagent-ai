from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_list_update_lead():
    created = client.post(
        "/api/business/leads",
        json={"name": "Ada Lovelace", "company": "Analytical Engines", "email": "ada@example.com", "source": "manual"},
    ).json()
    assert created["lead_id"]
    assert created["status"] == "new"
    assert created["source"] == "manual"
    assert created["created_at"] and created["updated_at"]

    listed = client.get("/api/business/leads").json()
    assert any(item["lead_id"] == created["lead_id"] for item in listed["leads"])

    updated = client.patch(f"/api/business/leads/{created['lead_id']}", json={"status": "qualified", "next_step": "Send proposal"}).json()
    assert updated["status"] == "qualified"
    assert updated["next_step"] == "Send proposal"


def test_update_lead_not_found():
    assert client.patch("/api/business/leads/missing", json={"status": "won"}).status_code == 404


def test_create_list_update_support_case_with_triage():
    created = client.post(
        "/api/business/support-cases",
        json={"customer": "Acme", "subject": "Login broken", "description": "Cannot log in since update.", "priority": "high"},
    ).json()
    assert created["case_id"]
    assert created["priority"] == "high"
    assert created["status"] == "open"
    assert created["triage_summary"]
    assert "DRAFT" in created["draft_reply"]

    listed = client.get("/api/business/support-cases").json()
    assert any(item["case_id"] == created["case_id"] for item in listed["support_cases"])

    updated = client.patch(f"/api/business/support-cases/{created['case_id']}", json={"status": "resolved"}).json()
    assert updated["status"] == "resolved"


def test_process_document_summary_actions_and_risk_flags():
    content = "Invoice total due. Please pay the balance. This invoice is overdue and a late fee applies."
    created = client.post(
        "/api/business/documents",
        json={"title": "March Invoice", "document_type": "invoice", "content": content},
    ).json()
    assert created["document_id"]
    assert created["document_type"] == "invoice"
    assert created["extracted_summary"]
    assert any("pay" in item.lower() for item in created["action_items"])
    assert created["risk_flags"]  # overdue + late fee should flag

    updated = client.patch(
        f"/api/business/documents/{created['document_id']}",
        json={"content": "Receipt only. No issues."},
    ).json()
    assert updated["risk_flags"] == []


def test_document_not_found():
    assert client.patch("/api/business/documents/missing", json={"title": "x"}).status_code == 404


def test_create_and_update_proposal_draft():
    created = client.post(
        "/api/business/proposals",
        json={"title": "Website Rebuild", "client": "Acme", "scope": "Rebuild marketing site."},
    ).json()
    assert created["proposal_id"]
    assert created["status"] == "draft"
    assert "DRAFT" in created["draft"]

    updated = client.patch(f"/api/business/proposals/{created['proposal_id']}", json={"status": "reviewed"}).json()
    assert updated["status"] == "reviewed"

    listed = client.get("/api/business/proposals").json()
    assert any(item["proposal_id"] == created["proposal_id"] for item in listed["proposals"])


def test_create_and_update_marketing_item():
    created = client.post(
        "/api/business/marketing-calendar",
        json={"title": "Launch post", "channel": "linkedin", "scheduled_for": "2026-07-01", "status": "planned"},
    ).json()
    assert created["item_id"]
    assert created["channel"] == "linkedin"
    assert created["status"] == "planned"

    updated = client.patch(f"/api/business/marketing-calendar/{created['item_id']}", json={"status": "drafted"}).json()
    assert updated["status"] == "drafted"

    listed = client.get("/api/business/marketing-calendar").json()
    assert any(item["item_id"] == created["item_id"] for item in listed["marketing_items"])


def test_kpi_dashboard_calculations():
    # Seed a won and a lost lead to exercise conversion_rate.
    won = client.post("/api/business/leads", json={"name": "Won Co"}).json()
    client.patch(f"/api/business/leads/{won['lead_id']}", json={"status": "won"})
    lost = client.post("/api/business/leads", json={"name": "Lost Co"}).json()
    client.patch(f"/api/business/leads/{lost['lead_id']}", json={"status": "lost"})

    dashboard = client.get("/api/business/dashboard").json()
    for key in (
        "total_leads",
        "qualified_leads",
        "open_support_cases",
        "high_priority_cases",
        "proposal_count",
        "draft_proposals",
        "planned_marketing_items",
        "won_leads",
        "lost_leads",
        "conversion_rate",
        "recent_activity",
    ):
        assert key in dashboard
    assert dashboard["won_leads"] >= 1
    assert dashboard["lost_leads"] >= 1
    assert 0 <= dashboard["conversion_rate"] <= 100
    assert isinstance(dashboard["recent_activity"], list)


def test_governance_events_written_for_business_actions():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/business/leads", json={"name": "Gov Test Lead"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "business_lead_created" in actions


def test_safety_no_real_send_language_in_drafts():
    case = client.post("/api/business/support-cases", json={"subject": "Question"}).json()
    assert "never sends email" in case["draft_reply"].lower() or "draft" in case["draft_reply"].lower()


# ----------------------------------------------------------------------
# Regression: existing endpoints still work
# ----------------------------------------------------------------------
def test_existing_run_endpoint_still_works():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)


def test_existing_marketplace_and_department_endpoints_still_work():
    assert client.get("/api/departments").status_code == 200
    assert client.get("/api/agent-marketplace/packs").status_code == 200
    assert client.get("/api/analytics").status_code == 200
    assert client.get("/api/governance").status_code == 200
