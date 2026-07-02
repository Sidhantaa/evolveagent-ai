from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_playbook(**overrides) -> dict:
    payload = {
        "name": overrides.get("name", "Release playbook"),
        "steps": overrides.get("steps", [
            {"title": "Draft changelog", "step_type": "plan", "detail": "Summarize changes."},
            {"title": "Note reviewers", "step_type": "note", "detail": "Ping the team."},
            {"title": "Publish release", "step_type": "approval_required", "detail": "Risky — needs approval."},
        ]),
    }
    response = client.post("/api/playbooks", json=payload)
    assert response.status_code == 200
    return response.json()


def test_create_and_list_playbook():
    pb = _create_playbook()
    assert pb["playbook_id"]
    assert pb["step_count"] == 3
    listed = client.get("/api/playbooks").json()
    assert any(p["playbook_id"] == pb["playbook_id"] for p in listed["playbooks"])


def test_run_is_planning_first_and_holds_risky_steps():
    pb = _create_playbook()
    run = client.post(f"/api/playbooks/{pb['playbook_id']}/run").json()
    assert run["run_id"]
    assert run["executed"] is False
    assert run["planned_count"] == 1
    assert run["approval_required_count"] == 1
    statuses = {s["status"] for s in run["steps"]}
    assert "planned" in statuses
    assert "approval_required" in statuses
    assert "noted" in statuses
    assert "nothing is executed" in run["note"].lower()
    assert client.post("/api/playbooks/missing/run").status_code == 404


def test_run_deterministic_step_mapping():
    pb = _create_playbook(name="single", steps=[{"title": "risky", "step_type": "approval_required"}])
    run = client.post(f"/api/playbooks/{pb['playbook_id']}/run").json()
    assert run["steps"][0]["status"] == "approval_required"
    assert run["approval_required_count"] == 1
    assert run["planned_count"] == 0


def test_list_runs_filtered():
    pb = _create_playbook()
    client.post(f"/api/playbooks/{pb['playbook_id']}/run")
    runs = client.get(f"/api/playbooks/runs?playbook_id={pb['playbook_id']}").json()
    assert all(r["playbook_id"] == pb["playbook_id"] for r in runs["runs"])
    assert runs["count"] >= 1


def test_summary_and_analytics():
    _create_playbook()
    s = client.get("/api/playbooks/summary").json()
    for key in ("playbook_count", "run_count", "note"):
        assert key in s
    assert "nothing is executed" in s["note"].lower()
    analytics = client.get("/api/analytics").json()
    for key in ("playbooks_total", "playbook_runs"):
        assert key in analytics


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    pb = _create_playbook()
    client.post(f"/api/playbooks/{pb['playbook_id']}/run")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "playbook_created" in actions or "playbook_run" in actions


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/eval-harness/summary").status_code == 200
    assert client.get("/api/operating-layer/dashboard").status_code == 200
