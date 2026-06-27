from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_aggregation_shape():
    # Seed some cross-domain data so aggregation has content.
    client.post("/api/departments/templates/seed")
    client.post("/api/business/leads", json={"name": "Brain Lead", "status": "won"})
    body = client.get("/api/company-brain/dashboard").json()
    for key in (
        "company_health_score",
        "departments",
        "agent_workforce",
        "business",
        "projects",
        "risks",
        "decisions",
        "recommended_next_actions",
    ):
        assert key in body
    assert 0 <= body["company_health_score"] <= 100
    assert isinstance(body["departments"], dict)
    assert isinstance(body["business"], dict)
    assert isinstance(body["risks"], list)
    assert isinstance(body["recommended_next_actions"], list) and body["recommended_next_actions"]
    # Departments seeded → active count should be present.
    assert body["departments"]["active"] >= 1


def test_create_strategy():
    strategy = client.post(
        "/api/company-brain/strategy",
        json={"title": "Q3 plan", "horizon": "quarter", "objectives": ["Grow pipeline", "Reduce risk"]},
    ).json()
    assert strategy["strategy_id"]
    assert strategy["title"] == "Q3 plan"
    assert strategy["objectives"] == ["Grow pipeline", "Reduce risk"]
    assert "health_score_at_creation" in strategy
    listed = client.get("/api/company-brain/strategy").json()
    assert any(s["strategy_id"] == strategy["strategy_id"] for s in listed["strategy"])


def test_create_decision():
    decision = client.post(
        "/api/company-brain/decisions",
        json={"title": "Adopt mock-first demos", "decision": "Default to mock providers", "impact": "high"},
    ).json()
    assert decision["decision_id"]
    assert decision["title"] == "Adopt mock-first demos"
    assert decision["impact"] == "high"
    listed = client.get("/api/company-brain/decisions").json()
    assert any(d["decision_id"] == decision["decision_id"] for d in listed["decisions"])


def test_create_report():
    report = client.post("/api/company-brain/reports", json={}).json()
    assert report["report_id"]
    assert "company_health_score" in report
    assert report["headline"]
    assert "top_risks" in report
    assert "recommended_next_actions" in report
    listed = client.get("/api/company-brain/reports").json()
    assert any(r["report_id"] == report["report_id"] for r in listed["reports"])


def test_governance_events_written():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/company-brain/strategy", json={"title": "Gov strategy"})
    client.post("/api/company-brain/decisions", json={"title": "Gov decision"})
    client.post("/api/company-brain/reports", json={})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert actions & {"company_brain_strategy_created", "company_brain_decision_logged", "company_brain_report_generated"}


def test_existing_v21_v24_endpoints_still_work():
    assert client.get("/api/multimodal/dashboard").status_code == 200
    assert client.get("/api/industry-modes/dashboard").status_code == 200
    assert client.get("/api/agent-network/dashboard").status_code == 200
    assert client.get("/api/self-healing/dashboard").status_code == 200


def test_existing_run_and_core_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/business/dashboard").status_code == 200
    assert client.get("/api/chief-of-staff/dashboard").status_code == 200
    assert client.get("/api/analytics").status_code == 200
    assert client.get("/api/governance").status_code == 200
