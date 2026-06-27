from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_department(**overrides) -> dict:
    payload = {
        "name": overrides.get("name", "QA Department"),
        "description": overrides.get("description", "Tests things."),
        "manager_agent": overrides.get("manager_agent", "QA Manager Agent"),
        "worker_agents": overrides.get("worker_agents", ["Test Generation Agent"]),
        "reviewer_agents": overrides.get("reviewer_agents", ["Judge Agent"]),
        "auditor_agents": overrides.get("auditor_agents", ["Security Governance Layer"]),
        "allowed_tools": overrides.get("allowed_tools", ["knowledge_search"]),
        "permission_level": overrides.get("permission_level", "read_only"),
    }
    response = client.post("/api/departments", json=payload)
    assert response.status_code == 200
    return response.json()


def test_create_department():
    department = _create_department(name="Create-Test Dept")
    assert department["department_id"]
    assert department["name"] == "Create-Test Dept"
    assert department["manager_agent"] == "QA Manager Agent"
    assert department["worker_agents"] == ["Test Generation Agent"]
    assert department["permission_level"] == "read_only"
    assert department["active"] is True
    assert department["created_at"] and department["updated_at"]


def test_list_departments():
    created = _create_department(name="List-Test Dept")
    body = client.get("/api/departments").json()
    assert isinstance(body["departments"], list)
    assert any(item["department_id"] == created["department_id"] for item in body["departments"])
    assert "total_departments" in body
    assert "active_departments" in body


def test_seed_default_templates():
    body = client.post("/api/departments/templates/seed").json()
    assert body["seeded_count"] + body["skipped_existing"] == 7
    names = {item["name"] for item in client.get("/api/departments?include_archived=true").json()["departments"]}
    for expected in ("Engineering", "Research", "Document", "Pharmacy PA", "Sales/Email", "Finance/Cost", "Compliance"):
        assert expected in names
    # Seeding again is idempotent (no duplicate departments created).
    second = client.post("/api/departments/templates/seed").json()
    assert second["seeded_count"] == 0


def test_department_templates_listing():
    body = client.get("/api/departments/templates").json()
    assert body["count"] == 7
    assert all("permission_level" in template for template in body["templates"])


def test_update_department():
    created = _create_department(name="Update-Test Dept")
    response = client.patch(
        f"/api/departments/{created['department_id']}",
        json={"description": "Updated description", "permission_level": "plan_only"},
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["description"] == "Updated description"
    assert updated["permission_level"] == "plan_only"


def test_archive_department():
    created = _create_department(name="Archive-Test Dept")
    response = client.delete(f"/api/departments/{created['department_id']}")
    assert response.status_code == 200
    assert response.json()["active"] is False
    active_ids = {item["department_id"] for item in client.get("/api/departments").json()["departments"]}
    assert created["department_id"] not in active_ids


def test_create_department_run():
    created = _create_department(name="Run-Test Dept", permission_level="approve_to_run")
    response = client.post(
        f"/api/departments/{created['department_id']}/runs",
        json={"task": "Build a new settings page"},
    )
    assert response.status_code == 200
    run = response.json()
    assert run["department_run_id"]
    assert run["department_id"] == created["department_id"]
    assert run["task"] == "Build a new settings page"
    assert run["manager_agent"] == "QA Manager Agent"
    assert isinstance(run["workflow_plan"], list) and run["workflow_plan"]
    assert run["requires_approval"] is True
    assert run["risk_level"] == "high"
    assert run["status"] == "planned"


def test_create_collaboration_plan():
    client.post("/api/departments/templates/seed")
    response = client.post(
        "/api/departments/collaborations",
        json={
            "goal": "Ship a documented feature",
            "departments": ["Engineering", "Document", "Compliance"],
            "lead_department": "Engineering",
        },
    )
    assert response.status_code == 200
    collab = response.json()
    assert collab["collaboration_id"]
    assert collab["goal"] == "Ship a documented feature"
    assert collab["lead_department"] == "Engineering"
    assert collab["departments"] == ["Engineering", "Document", "Compliance"]
    assert len(collab["handoffs"]) == 2
    assert collab["status"] == "planned"


def test_department_run_not_found():
    response = client.post("/api/departments/does-not-exist/runs", json={"task": "x"})
    assert response.status_code == 404


def test_governance_event_written_for_department_actions():
    before = client.get("/api/governance").json()["total_events"]
    _create_department(name="Governance-Test Dept")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "department_created" in actions


def test_analytics_includes_organization_metrics():
    _create_department(name="Analytics-Test Dept")
    body = client.get("/api/analytics").json()
    for key in ("total_departments", "active_departments", "department_runs", "collaboration_count"):
        assert key in body
        assert isinstance(body[key], int)


# ----------------------------------------------------------------------
# Regression: existing endpoints still work
# ----------------------------------------------------------------------
def test_existing_run_endpoint_still_works():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    body = response.json()
    assert body.get("run_id")
    assert isinstance(body.get("final_output"), str) and body["final_output"]


def test_existing_core_endpoints_still_work():
    assert client.get("/api/analytics").status_code == 200
    assert client.get("/api/governance").status_code == 200
    assert client.get("/api/tools").status_code == 200
    assert client.get("/api/plugins").status_code == 200
    assert client.get("/api/providers/status").status_code == 200
    assert client.get("/api/os/summary").status_code == 200
