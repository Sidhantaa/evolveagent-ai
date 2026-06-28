from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_schedule_create_and_list():
    item = client.post("/api/life-os/schedule", json={"title": "Dentist", "date": "2026-07-01", "start_time": "10:00"}).json()
    assert item["schedule_id"]
    assert item["title"] == "Dentist"
    listed = client.get("/api/life-os/schedule").json()
    assert any(s["schedule_id"] == item["schedule_id"] for s in listed["schedule"])


def test_task_priority_ranking():
    # High priority + overdue should outrank low priority + far due.
    high = client.post("/api/life-os/tasks", json={"title": "Submit report", "priority": "high", "importance": "high", "due_date": "2000-01-01"}).json()
    low = client.post("/api/life-os/tasks", json={"title": "Read article", "priority": "low", "importance": "low", "due_date": "2099-01-01"}).json()
    body = client.get("/api/life-os/tasks").json()
    ranked = body["ranked"]
    assert ranked
    scores = [r["priority_score"] for r in ranked]
    assert scores == sorted(scores, reverse=True)
    high_entry = next(r for r in ranked if r["task_id"] == high["task_id"])
    low_entry = next(r for r in ranked if r["task_id"] == low["task_id"])
    assert high_entry["priority_score"] > low_entry["priority_score"]
    assert high_entry["overdue"] is True


def test_task_update_and_not_found():
    task = client.post("/api/life-os/tasks", json={"title": "Email prof"}).json()
    updated = client.patch(f"/api/life-os/tasks/{task['task_id']}", json={"status": "done"}).json()
    assert updated["status"] == "done"
    # Done tasks drop out of the active ranked list.
    ranked_ids = {r["task_id"] for r in client.get("/api/life-os/tasks").json()["ranked"]}
    assert task["task_id"] not in ranked_ids
    assert client.patch("/api/life-os/tasks/missing", json={"status": "done"}).status_code == 404


def test_reminder_create():
    reminder = client.post("/api/life-os/reminders", json={"title": "Call bank", "remind_on": "2026-07-02"}).json()
    assert reminder["reminder_id"]
    assert reminder["status"] == "open"
    listed = client.get("/api/life-os/reminders").json()
    assert any(r["reminder_id"] == reminder["reminder_id"] for r in listed["reminders"])


def test_deadline_create_and_sorted():
    near = client.post("/api/life-os/deadlines", json={"title": "CS project", "kind": "school", "due_date": "2026-07-03", "course_or_project": "CSE-4309"}).json()
    assert near["deadline_id"]
    assert near["kind"] == "school"
    listed = client.get("/api/life-os/deadlines").json()
    assert any(d["deadline_id"] == near["deadline_id"] for d in listed["deadlines"])
    # days_until_due is computed on listing.
    assert all("days_until_due" in d for d in listed["deadlines"])


def test_daily_plan_generation():
    client.post("/api/life-os/tasks", json={"title": "Plan day task", "priority": "high"})
    plan = client.post("/api/life-os/daily-plan", json={}).json()
    assert plan["plan_id"]
    assert plan["date"]
    for key in ("schedule_today", "top_tasks", "reminders_due", "upcoming_deadlines", "focus_suggestion"):
        assert key in plan
    assert isinstance(plan["top_tasks"], list)


def test_dashboard_counts():
    body = client.get("/api/life-os/dashboard").json()
    for key in (
        "today",
        "schedule_item_count",
        "active_task_count",
        "completed_task_count",
        "overdue_task_count",
        "open_reminder_count",
        "deadline_count",
        "top_tasks",
        "recommended_next_action",
    ):
        assert key in body


def test_governance_event_written():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/life-os/tasks", json={"title": "Gov task"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "life_task_created" in actions


def test_regression_existing_endpoints():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/avatar/dashboard").status_code == 200
    assert client.get("/api/device-operator/dashboard").status_code == 200
    assert client.get("/api/training-lab/dashboard").status_code == 200
