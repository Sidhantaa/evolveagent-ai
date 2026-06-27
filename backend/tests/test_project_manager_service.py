from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_workspace(name: str) -> str:
    response = client.post("/api/workspaces", json={"name": name, "description": "PM test"})
    assert response.status_code == 200
    return response.json()["workspace_id"]


def _make_goal(workspace_id: str, title: str, tasks: list[dict]) -> str:
    created = client.post(
        "/api/goals",
        json={"title": title, "description": "PM goal", "workspace_id": workspace_id},
    )
    assert created.status_code == 200
    goal_id = created.json()["goal"]["goal_id"]
    for task in tasks:
        added = client.post(f"/api/goals/{goal_id}/tasks", json=task)
        assert added.status_code == 200
    return goal_id


def test_timeline_reports_milestones_and_progress():
    workspace_id = _make_workspace("PM Timeline Workspace")
    goal_id = _make_goal(
        workspace_id,
        "Ship onboarding flow",
        [
            {"title": "Design", "estimated_effort": "large", "recommended_agent": "Strategy Agent"},
            {"title": "Build", "estimated_effort": "medium", "recommended_agent": "Coder Agent"},
        ],
    )

    timeline = client.get(f"/api/project-manager/timeline?workspace_id={workspace_id}").json()
    assert timeline["milestone_count"] == 1
    milestone = timeline["milestones"][0]
    assert milestone["goal_id"] == goal_id
    assert milestone["task_count"] == 2
    assert milestone["status"] in {"not_started", "in_progress", "at_risk", "completed"}


def test_resource_allocation_aggregates_effort_and_agents():
    workspace_id = _make_workspace("PM Resource Workspace")
    _make_goal(
        workspace_id,
        "Build billing module",
        [
            {"title": "Schema", "estimated_effort": "large", "recommended_agent": "Coder Agent"},
            {"title": "Tests", "estimated_effort": "small", "recommended_agent": "Tester Agent"},
        ],
    )

    resources = client.get(f"/api/project-manager/resources?workspace_id={workspace_id}").json()
    assert resources["active_goal_count"] == 1
    allocation = resources["allocations"][0]
    # large (5) + small (1) = 6 effort points
    assert allocation["effort_points"] == 6
    assert "Coder Agent" in allocation["assigned_agents"]
    assert {entry["agent"] for entry in resources["agent_load"]} >= {"Coder Agent", "Tester Agent"}


def test_risk_register_combines_manual_and_derived_risks():
    workspace_id = _make_workspace("PM Risk Workspace")
    goal_id = _make_goal(workspace_id, "Risky goal", [{"title": "Edge case"}])
    # Block a task so a risk is auto-derived.
    goal = client.get(f"/api/goals/{goal_id}").json()
    task_id = goal["task_graph"]["tasks"][0]["task_id"]
    client.patch(f"/api/goals/{goal_id}/tasks/{task_id}", json={"status": "blocked"})

    created = client.post(
        "/api/project-manager/risks",
        json={
            "title": "Vendor API may change",
            "severity": "high",
            "mitigation": "Pin version and add contract test",
            "goal_id": goal_id,
            "workspace_id": workspace_id,
        },
    )
    assert created.status_code == 200
    risk_id = created.json()["risk_id"]

    register = client.get(f"/api/project-manager/risks?workspace_id={workspace_id}").json()
    titles = [risk["title"] for risk in register["risks"]]
    assert "Vendor API may change" in titles
    assert any("Blocked tasks" in title for title in titles)
    assert register["open_risk_count"] >= 2

    # Resolving the manual risk removes it from the open list.
    resolved = client.patch(
        f"/api/project-manager/risks/{risk_id}", json={"status": "resolved"}
    )
    assert resolved.status_code == 200
    after = client.get(f"/api/project-manager/risks?workspace_id={workspace_id}").json()
    assert "Vendor API may change" not in [risk["title"] for risk in after["risks"]]


def test_update_unknown_risk_returns_404():
    response = client.patch("/api/project-manager/risks/does-not-exist", json={"status": "resolved"})
    assert response.status_code == 404


def test_status_report_generation_and_history():
    workspace_id = _make_workspace("PM Report Workspace")
    _make_goal(workspace_id, "Launch demo", [{"title": "Prep", "estimated_effort": "medium"}])

    report = client.post(
        "/api/project-manager/reports", json={"workspace_id": workspace_id}
    ).json()
    assert report["period"] == "weekly"
    assert report["milestone_summary"]["total"] == 1
    assert report["highlights"]

    history = client.get(f"/api/project-manager/reports?workspace_id={workspace_id}").json()
    assert len(history) == 1
    assert history[0]["report_id"] == report["report_id"]


def test_dashboard_unifies_project_state_and_logs_governance():
    workspace_id = _make_workspace("PM Dashboard Workspace")
    _make_goal(workspace_id, "Unified goal", [{"title": "Step", "estimated_effort": "large"}])
    client.post("/api/project-manager/reports", json={"workspace_id": workspace_id})

    dashboard = client.get(f"/api/project-manager/dashboard?workspace_id={workspace_id}").json()
    assert dashboard["goal_count"] == 1
    assert dashboard["milestone_summary"]["total"] == 1
    assert dashboard["latest_report"] is not None
    assert "open_risk_count" in dashboard["risk_summary"]

    governance = client.get(f"/api/governance?workspace_id={workspace_id}").json()
    action_types = {event.get("action_type") for event in governance["recent_events"]}
    assert "project_status_report_generated" in action_types
