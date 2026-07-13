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


def test_seed_default_templates_gives_each_newly_seeded_department_a_real_goal_and_budget(tmp_path):
    # Isolated instance (fresh tmp_path storage) rather than the shared
    # app-level singleton -- avoids any dependency on whether the shared
    # dev-data store already has these template names seeded from an earlier
    # test/run, which would make seed_templates() a no-op (idempotent skip)
    # and give a false negative for goal/budget seeding.
    from app.services.agent_department_service import AgentDepartmentService
    from app.services.goal_service import GoalService
    from app.services.governance_service import GovernanceService
    from app.services.permission_service import PermissionService
    from app.services.storage_service import StorageService
    from app.services.usage_ledger_service import UsageLedgerService

    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    service = AgentDepartmentService(
        storage, governance, PermissionService(),
        goal_service=GoalService(storage), usage_ledger=UsageLedgerService(storage, governance),
    )
    body = service.seed_templates()
    assert body["seeded_count"] == 7
    for department in body["departments"]:
        scorecard = service.department_scorecard(department["department_id"])
        assert scorecard["goals"], f"{department['name']} has no starter goal"
        assert scorecard["goals"][0]["workspace_id"] == f"dept:{department['department_id']}"
        assert scorecard["budget"]["monthly_limit"] == 100.0

    # Idempotent: seeding again creates no duplicate goals/budgets either.
    second = service.seed_templates()
    assert second["seeded_count"] == 0
    first_dept_id = body["departments"][0]["department_id"]
    assert len(service.list_department_goals(first_dept_id)) == 1


def test_plan_run_blocked_when_department_is_over_its_own_budget(tmp_path):
    from app.services.agent_department_service import AgentDepartmentService
    from app.services.governance_service import GovernanceService
    from app.services.permission_service import PermissionService
    from app.services.storage_service import StorageService
    from app.services.usage_ledger_service import UsageLedgerService

    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    usage_ledger = UsageLedgerService(storage, governance)
    service = AgentDepartmentService(storage, governance, PermissionService(), usage_ledger=usage_ledger)
    department = service.create_department(name="Over-Budget Dept", permission_level="read_only")
    service.set_department_budget(department["department_id"], 10.0)
    usage_ledger.record_usage({
        "workspace_id": f"dept:{department['department_id']}", "capability": "text",
        "units": 1, "estimated_cost": 20.0,
    })
    run = service.plan_run(department["department_id"], "Do some work")
    assert run["status"] == "blocked"
    assert run["block_reason"] == "budget_exceeded"


def test_plan_run_not_blocked_when_department_is_under_budget(tmp_path):
    from app.services.agent_department_service import AgentDepartmentService
    from app.services.governance_service import GovernanceService
    from app.services.permission_service import PermissionService
    from app.services.storage_service import StorageService
    from app.services.usage_ledger_service import UsageLedgerService

    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    usage_ledger = UsageLedgerService(storage, governance)
    service = AgentDepartmentService(storage, governance, PermissionService(), usage_ledger=usage_ledger)
    department = service.create_department(name="Under-Budget Dept", permission_level="read_only")
    service.set_department_budget(department["department_id"], 100.0)
    usage_ledger.record_usage({
        "workspace_id": f"dept:{department['department_id']}", "capability": "text",
        "units": 1, "estimated_cost": 5.0,
    })
    run = service.plan_run(department["department_id"], "Do some work")
    assert run["status"] == "planned"
    assert run["block_reason"] is None


def test_plan_run_permission_block_takes_priority_over_budget_state():
    """A permission-blocked department still reports permission_blocked as the
    reason even if it happens to also be within budget -- permission is the
    stricter, human-set gate."""
    created = _create_department(name="Permission-Block-Test Dept", permission_level="blocked")
    response = client.post(f"/api/departments/{created['department_id']}/runs", json={"task": "x"})
    run = response.json()
    assert run["status"] == "blocked"
    assert run["block_reason"] == "permission_blocked"


def test_plan_run_never_blocks_when_no_usage_ledger_wired(tmp_path):
    from app.services.agent_department_service import AgentDepartmentService
    from app.services.governance_service import GovernanceService
    from app.services.permission_service import PermissionService
    from app.services.storage_service import StorageService

    storage = StorageService(data_dir=str(tmp_path / "data"))
    service = AgentDepartmentService(storage, GovernanceService(storage), PermissionService())
    department = service.create_department(name="No-Ledger Dept", permission_level="read_only")
    run = service.plan_run(department["department_id"], "Do some work")
    assert run["status"] == "planned"
    assert run["block_reason"] is None


def test_seed_default_templates_without_collaborators_still_creates_departments(tmp_path):
    from app.services.agent_department_service import AgentDepartmentService
    from app.services.governance_service import GovernanceService
    from app.services.permission_service import PermissionService
    from app.services.storage_service import StorageService

    storage = StorageService(data_dir=str(tmp_path / "data"))
    service = AgentDepartmentService(storage, GovernanceService(storage), PermissionService())
    body = service.seed_templates()
    assert body["seeded_count"] == 7  # missing collaborators never block department creation
    for department in body["departments"]:
        assert service.list_department_goals(department["department_id"]) == []


def test_department_templates_listing():
    body = client.get("/api/departments/templates").json()
    assert body["count"] == 7
    assert all("permission_level" in template for template in body["templates"])


def test_department_overview_endpoint():
    """overview() was real, purpose-built for the Developer Mode Agent
    Organization panel, but had no route -- every other aggregation on this
    service already has one. Also confirms /departments/overview resolves to
    the static overview route, not the /departments/{department_id} matcher."""
    _create_department(name="Overview-Test Dept")
    body = client.get("/api/departments/overview").json()
    assert "departments" in body and isinstance(body["departments"], list)
    assert "recent_runs" in body
    assert "recent_collaborations" in body
    assert "permission_levels" in body
    assert "permission_level_counts" in body
    assert "total_departments" in body  # from analytics_summary()
    assert any(d["name"] == "Overview-Test Dept" for d in body["departments"])


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


# ----------------------------------------------------------------------
# v300 Digital Departments: real goals, real budgets, measurable outcomes
# ----------------------------------------------------------------------
def test_create_and_list_department_goal():
    created = _create_department(name="Goals-Test Dept")
    dept_id = created["department_id"]
    goal = client.post(f"/api/departments/{dept_id}/goals", json={
        "title": "Ship the v300 rollout", "description": "Real department goal.",
    }).json()
    assert goal["goal_id"]
    assert goal["title"] == "Ship the v300 rollout"
    assert goal["workspace_id"] == f"dept:{dept_id}"
    listed = client.get(f"/api/departments/{dept_id}/goals").json()
    assert listed["count"] == 1
    assert listed["goals"][0]["goal_id"] == goal["goal_id"]
    # a goal for a DIFFERENT department must not leak into this one's list
    other = _create_department(name="Other-Goals-Test Dept")
    other_listed = client.get(f"/api/departments/{other['department_id']}/goals").json()
    assert other_listed["count"] == 0


def test_department_goal_not_found():
    response = client.post("/api/departments/does-not-exist/goals", json={"title": "x"})
    assert response.status_code == 404


def test_set_and_read_department_budget():
    created = _create_department(name="Budget-Test Dept")
    dept_id = created["department_id"]
    budget = client.post(f"/api/departments/{dept_id}/budget", json={"monthly_limit": 50.0}).json()
    assert budget["workspace_id"] == f"dept:{dept_id}"
    assert budget["monthly_limit"] == 50.0
    scorecard = client.get(f"/api/departments/{dept_id}/scorecard").json()
    assert scorecard["budget"]["workspace_id"] == f"dept:{dept_id}"
    assert scorecard["department"]["department_id"] == dept_id


def test_department_budget_not_found():
    response = client.post("/api/departments/does-not-exist/budget", json={"monthly_limit": 10})
    assert response.status_code == 404


def test_department_scorecard_reflects_real_run_outcomes():
    created = _create_department(name="Scorecard-Test Dept", permission_level="read_only")
    dept_id = created["department_id"]
    client.post(f"/api/departments/{dept_id}/runs", json={"task": "Draft a research brief"})
    scorecard = client.get(f"/api/departments/{dept_id}/scorecard").json()
    assert scorecard["measurable_outcomes"]["total_runs"] == 1
    assert scorecard["measurable_outcomes"]["planned"] == 1
    assert scorecard["measurable_outcomes"]["blocked"] == 0


def test_department_scorecard_not_found():
    response = client.get("/api/departments/does-not-exist/scorecard")
    assert response.status_code == 404


def test_department_goal_governance_logged():
    created = _create_department(name="Goal-Governance-Test Dept")
    before = client.get("/api/governance").json()["total_events"]
    client.post(f"/api/departments/{created['department_id']}/goals", json={"title": "Track this"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "department_goal_created" in actions


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
