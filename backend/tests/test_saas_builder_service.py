from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_project(**overrides) -> dict:
    payload = {"name": overrides.get("name", "TaskFlow"), "idea": overrides.get("idea", "Help small teams track tasks without overhead.")}
    response = client.post("/api/saas-builder/projects", json=payload)
    assert response.status_code == 200
    return response.json()


def test_project_create_list_get():
    project = _create_project(name="Create-Test SaaS")
    assert project["project_id"]
    assert project["status"] == "drafting"
    listed = client.get("/api/saas-builder/projects").json()
    assert any(p["project_id"] == project["project_id"] for p in listed["projects"])
    fetched = client.get(f"/api/saas-builder/projects/{project['project_id']}").json()
    assert fetched["project_id"] == project["project_id"]
    assert client.get("/api/saas-builder/projects/missing").status_code == 404


def test_validation_generation():
    project = _create_project()
    validation = client.post(f"/api/saas-builder/projects/{project['project_id']}/validate").json()
    for key in ("target_user", "pain", "value_prop", "market_risk", "mvp_scope", "monetization_hypothesis", "confidence"):
        assert key in validation
    assert 0 <= validation["confidence"] <= 100
    assert client.post("/api/saas-builder/projects/missing/validate").status_code == 404


def test_roadmap_generation():
    project = _create_project()
    roadmap = client.post(f"/api/saas-builder/projects/{project['project_id']}/roadmap").json()
    assert roadmap["roadmap_id"]
    assert isinstance(roadmap["phases"], list) and roadmap["phases"]
    assert all("features" in phase for phase in roadmap["phases"])


def test_architecture_plan_generation():
    project = _create_project()
    plan = client.post(f"/api/saas-builder/projects/{project['project_id']}/architecture").json()
    for key in ("database_entities", "api_routes", "frontend_pages", "integrations", "risks"):
        assert key in plan
    assert plan["database_entities"]


def test_launch_assets_generation():
    project = _create_project(name="Launchy")
    assets = client.post(f"/api/saas-builder/projects/{project['project_id']}/launch-assets").json()
    assert assets["landing_copy"]["headline"]
    assert isinstance(assets["pricing_tiers"], list) and assets["pricing_tiers"]
    assert isinstance(assets["docs_outline"], list)
    # Pricing is placeholder — no real payment.
    assert "no real payment" in assets["note"].lower()


def test_feedback_create_and_list():
    project = _create_project()
    feedback = client.post(
        f"/api/saas-builder/projects/{project['project_id']}/feedback",
        json={"type": "bug", "title": "Login fails", "detail": "Cannot log in"},
    ).json()
    assert feedback["feedback_id"]
    assert feedback["type"] == "bug"
    listed = client.get(f"/api/saas-builder/projects/{project['project_id']}/feedback").json()
    assert any(f["feedback_id"] == feedback["feedback_id"] for f in listed["feedback"])
    assert client.post("/api/saas-builder/projects/missing/feedback", json={"title": "x"}).status_code == 404


def test_dashboard_works():
    _create_project()
    body = client.get("/api/saas-builder/dashboard").json()
    for key in ("total_projects", "total_validations", "total_roadmaps", "open_feedback", "safety_note"):
        assert key in body
    assert "no deploy" in body["safety_note"].lower()


def test_governance_event_written():
    before = client.get("/api/governance").json()["total_events"]
    _create_project(name="Gov SaaS")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "saas_project_created" in actions


def test_regression_existing_endpoints():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/universal-operator/dashboard").status_code == 200
    assert client.get("/api/company-brain/dashboard").status_code == 200
