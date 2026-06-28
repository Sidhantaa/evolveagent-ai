from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_member(**overrides) -> dict:
    payload = {
        "name": overrides.get("name", "Alice"),
        "member_type": overrides.get("member_type", "human"),
        "role": overrides.get("role", "Engineer"),
    }
    response = client.post("/api/team-manager/members", json=payload)
    assert response.status_code == 200
    return response.json()


def test_member_crud():
    member = _create_member(name="CRUD Member")
    assert member["member_id"]
    assert member["member_type"] == "human"
    listed = client.get("/api/team-manager/members").json()
    assert any(m["member_id"] == member["member_id"] for m in listed["members"])
    updated = client.patch(f"/api/team-manager/members/{member['member_id']}", json={"role": "Lead", "active": False}).json()
    assert updated["role"] == "Lead"
    assert updated["active"] is False
    assert client.patch("/api/team-manager/members/missing", json={"role": "x"}).status_code == 404


def test_assignment_crud():
    member = _create_member(member_type="ai_agent", name="Coder Agent")
    assignment = client.post(
        "/api/team-manager/assignments",
        json={"title": "Build feature", "owner_id": member["member_id"], "owner_name": "Coder Agent", "priority": "high"},
    ).json()
    assert assignment["assignment_id"]
    assert assignment["priority"] == "high"
    listed = client.get("/api/team-manager/assignments").json()
    assert any(a["assignment_id"] == assignment["assignment_id"] for a in listed["assignments"])
    updated = client.patch(f"/api/team-manager/assignments/{assignment['assignment_id']}", json={"status": "done"}).json()
    assert updated["status"] == "done"
    assert client.patch("/api/team-manager/assignments/missing", json={"status": "done"}).status_code == 404


def test_standup_generation():
    member = _create_member(name="Standup Owner")
    client.post("/api/team-manager/assignments", json={"title": "In progress task", "owner_name": "Standup Owner", "status": "in_progress"})
    client.post("/api/team-manager/assignments", json={"title": "Blocked task", "status": "blocked", "blocked_reason": "Waiting on API"})
    standup = client.post("/api/team-manager/standups", json={}).json()
    assert standup["standup_id"]
    assert standup["summary"]
    assert isinstance(standup["in_progress"], list)
    assert isinstance(standup["blockers"], list)
    listed = client.get("/api/team-manager/standups").json()
    assert any(s["standup_id"] == standup["standup_id"] for s in listed["standups"])


def test_sprint_creation_and_review():
    sprint = client.post(
        "/api/team-manager/sprints",
        json={"name": "Sprint 1", "goals": ["Ship v1"], "tasks": ["Task A", "Task B"], "owners": ["Alice"]},
    ).json()
    assert sprint["sprint_id"]
    assert sprint["review_checklist"]
    assert sprint["status"] == "planned"
    review = client.post(f"/api/team-manager/sprints/{sprint['sprint_id']}/review", json={"summary": "Good sprint"}).json()
    assert review["review_id"]
    assert review["sprint_id"] == sprint["sprint_id"]
    assert client.post("/api/team-manager/sprints/missing/review", json={}).status_code == 404


def test_analytics_counts():
    _create_member(name="Analytics Human", member_type="human")
    ai = _create_member(name="Analytics AI", member_type="ai_agent")
    client.post("/api/team-manager/assignments", json={"title": "AI task", "owner_id": ai["member_id"], "owner_name": "Analytics AI", "status": "done"})
    body = client.get("/api/team-manager/analytics").json()
    for key in ("total_assignments", "completed_tasks", "blocked_tasks", "overdue_tasks", "ai_tasks", "human_tasks", "workload_by_owner"):
        assert key in body
    assert body["completed_tasks"] >= 1


def test_dashboard_works():
    body = client.get("/api/team-manager/dashboard").json()
    for key in ("member_count", "ai_member_count", "human_member_count", "analytics", "sprint_count"):
        assert key in body


def test_governance_event_written():
    before = client.get("/api/governance").json()["total_events"]
    _create_member(name="Gov Member")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "team_member_created" in actions


def test_regression_run_still_works():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/universal-operator/dashboard").status_code == 200
