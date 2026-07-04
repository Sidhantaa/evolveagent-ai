from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_demo_script_and_walkthrough():
    script = client.get("/api/demo/script").json()
    assert script["step_count"] >= 5
    assert all("route" in s and "action" in s for s in script["script"])
    walk = client.get("/api/demo/walkthrough").json()
    assert walk["step_count"] >= 3


def test_feature_sequence_and_resume_bullets():
    seq = client.get("/api/demo/feature-sequence").json()
    assert seq["count"] >= 5
    assert all("route" in s for s in seq["open_sequence"])
    bullets = client.get("/api/demo/resume-bullets").json()
    assert bullets["count"] >= 3


def test_case_study_export_is_markdown():
    cs = client.get("/api/demo/case-study").json()
    assert cs["format"] == "markdown"
    assert "EvolveAgent AI" in cs["content"]
    assert "Safety" in cs["content"]


def test_seed_then_reset_is_scoped():
    goals_before = len(client.get("/api/goals").json())
    seeded = client.post("/api/demo/seed").json()
    assert seeded["seeded_count"] >= 3
    goals_after = len(client.get("/api/goals").json())
    assert goals_after > goals_before  # seeding added demo goals
    reset = client.post("/api/demo/reset").json()
    assert reset["removed_count"] >= seeded["seeded_count"]
    goals_final = client.get("/api/goals").json()
    # Only demo-tagged records removed; no demo goals remain.
    assert not any(g.get("demo_seed") for g in goals_final)


def test_reset_preserves_non_demo_goals():
    created = client.post("/api/goals", json={"title": "Real goal v66", "description": "keep me"}).json()
    real_goal = created.get("goal", created)
    real_id = real_goal.get("goal_id") or real_goal.get("id")
    client.post("/api/demo/seed")
    client.post("/api/demo/reset")
    goals = client.get("/api/goals").json()
    assert any((g.get("goal_id") or g.get("id")) == real_id for g in goals)  # user data untouched


def test_summary_and_analytics():
    summary = client.get("/api/demo/summary").json()
    for key in ("demo_script_steps", "active_demo_batches"):
        assert key in summary
    analytics = client.get("/api/analytics").json()
    assert "demo_batches_active" in analytics


def test_seed_is_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/demo/seed")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {e.get("action_type") for e in after["recent_events"]}
    assert "demo_seeded" in actions
    client.post("/api/demo/reset")


def test_existing_endpoints_still_work():
    assert client.get("/api/features/summary").status_code == 200
    assert client.get("/api/home").status_code == 200
