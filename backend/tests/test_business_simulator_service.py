from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_scenario(**overrides) -> dict:
    payload = {
        "title": overrides.get("title", "Launch with 3 features"),
        "description": overrides.get("description", "What happens if we launch this app with only three features?"),
        "scenario_type": overrides.get("scenario_type", "launch"),
        "assumptions": overrides.get("assumptions", ["Team of 2", "Two-week window"]),
        "options": overrides.get("options", ["Launch now", "Wait and add features"]),
    }
    response = client.post("/api/business-simulator/scenarios", json=payload)
    assert response.status_code == 200
    return response.json()


def test_create_list_get_update_scenario():
    created = _create_scenario(title="Create-Test Scenario")
    assert created["scenario_id"]
    assert created["scenario_type"] == "launch"
    assert created["assumptions"] and created["options"]

    listed = client.get("/api/business-simulator/scenarios").json()
    assert any(item["scenario_id"] == created["scenario_id"] for item in listed["scenarios"])

    fetched = client.get(f"/api/business-simulator/scenarios/{created['scenario_id']}").json()
    assert fetched["scenario_id"] == created["scenario_id"]

    updated = client.patch(
        f"/api/business-simulator/scenarios/{created['scenario_id']}",
        json={"scenario_type": "decision", "options": ["A", "B", "C"]},
    ).json()
    assert updated["scenario_type"] == "decision"
    assert updated["options"] == ["A", "B", "C"]


def test_scenario_not_found():
    assert client.get("/api/business-simulator/scenarios/missing").status_code == 404
    assert client.patch("/api/business-simulator/scenarios/missing", json={"title": "x"}).status_code == 404
    assert client.post("/api/business-simulator/scenarios/missing/run").status_code == 404


def test_run_simulation_produces_full_result():
    scenario = _create_scenario(title="Run-Test Scenario")
    result = client.post(f"/api/business-simulator/scenarios/{scenario['scenario_id']}/run").json()
    assert result["result_id"]
    assert result["scenario_id"] == scenario["scenario_id"]
    assert result["simulation_only"] is True

    # decision score
    assert 0 <= result["decision_score"] <= 100
    # cost estimate
    cost = result["cost_estimate"]
    assert cost["low"] <= cost["expected"] <= cost["high"]
    assert isinstance(cost["notes"], list) and cost["notes"]
    # time estimate
    time = result["time_estimate"]
    assert time["best_case_days"] <= time["expected_days"] <= time["worst_case_days"]
    assert isinstance(time["notes"], list) and time["notes"]
    # risk estimate
    risk = result["risk_estimate"]
    assert 0 <= risk["risk_score"] <= 100
    assert risk["risk_level"] in {"low", "medium", "high"}
    assert isinstance(risk["risk_factors"], list)
    assert isinstance(risk["mitigations"], list) and risk["mitigations"]
    # option comparison
    assert isinstance(result["option_comparison"], list) and len(result["option_comparison"]) == 2
    assert result["recommendation"]
    assert 0 <= result["confidence"] <= 100


def test_result_listing_and_fetch():
    scenario = _create_scenario(title="Result-Test Scenario")
    result = client.post(f"/api/business-simulator/scenarios/{scenario['scenario_id']}/run").json()
    listed = client.get("/api/business-simulator/results").json()
    assert any(item["result_id"] == result["result_id"] for item in listed["results"])
    fetched = client.get(f"/api/business-simulator/results/{result['result_id']}").json()
    assert fetched["result_id"] == result["result_id"]
    assert client.get("/api/business-simulator/results/missing").status_code == 404


def test_high_risk_keywords_raise_risk_level():
    scenario = _create_scenario(
        title="Payment compliance launch",
        description="Urgent production launch handling customer payment and legal compliance before the deadline.",
        assumptions=[],
        options=["Go now"],
    )
    result = client.post(f"/api/business-simulator/scenarios/{scenario['scenario_id']}/run").json()
    assert result["risk_estimate"]["risk_level"] in {"medium", "high"}
    assert result["risk_estimate"]["risk_factors"]


def test_dashboard_response_shape():
    scenario = _create_scenario(title="Dashboard-Test Scenario")
    client.post(f"/api/business-simulator/scenarios/{scenario['scenario_id']}/run")
    body = client.get("/api/business-simulator/dashboard").json()
    for key in (
        "total_scenarios",
        "total_results",
        "average_risk_score",
        "high_risk_scenarios",
        "recent_results",
        "recommended_next_simulation",
    ):
        assert key in body
    assert body["simulation_only"] is True
    assert isinstance(body["recent_results"], list)


def test_governance_events_written():
    before = client.get("/api/governance").json()["total_events"]
    scenario = _create_scenario(title="Gov-Test Scenario")
    client.post(f"/api/business-simulator/scenarios/{scenario['scenario_id']}/run")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "business_simulation_run" in actions or "business_simulation_scenario_created" in actions


# ----------------------------------------------------------------------
# Regression
# ----------------------------------------------------------------------
def test_existing_run_endpoint_still_works():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)


def test_existing_v18_v19_endpoints_still_work():
    assert client.get("/api/business/dashboard").status_code == 200
    assert client.get("/api/chief-of-staff/dashboard").status_code == 200
    assert client.get("/api/agent-marketplace/packs").status_code == 200
    assert client.get("/api/departments").status_code == 200
    assert client.get("/api/analytics").status_code == 200
