from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_seed_default_modes():
    body = client.post("/api/industry-modes/seed").json()
    assert body["seeded_count"] + body["skipped_existing"] == 8
    names = {mode["name"] for mode in client.get("/api/industry-modes").json()["modes"]}
    for expected in ("Pharmacy", "Construction", "Student", "Software", "Business", "Healthcare Admin", "Legal Document", "Finance"):
        assert expected in names
    # Idempotent reseed.
    second = client.post("/api/industry-modes/seed").json()
    assert second["seeded_count"] == 0


def test_get_and_update_mode():
    client.post("/api/industry-modes/seed")
    modes = client.get("/api/industry-modes").json()["modes"]
    target = next(mode for mode in modes if mode["name"] == "Software")
    fetched = client.get(f"/api/industry-modes/{target['mode_id']}").json()
    assert fetched["mode_id"] == target["mode_id"]
    assert fetched["recommended_agents"]
    assert fetched["risk_rules"]

    updated = client.patch(
        f"/api/industry-modes/{target['mode_id']}",
        json={"description": "Updated software mode", "enabled": False},
    ).json()
    assert updated["description"] == "Updated software mode"
    assert updated["enabled"] is False


def test_mode_not_found():
    assert client.get("/api/industry-modes/missing").status_code == 404
    assert client.patch("/api/industry-modes/missing", json={"description": "x"}).status_code == 404
    assert client.post("/api/industry-modes/missing/run", json={"prompt": "hi"}).status_code == 404


def test_run_mode_creates_mode_run():
    client.post("/api/industry-modes/seed")
    mode = next(m for m in client.get("/api/industry-modes").json()["modes"] if m["name"] == "Pharmacy")
    run = client.post(f"/api/industry-modes/{mode['mode_id']}/run", json={"prompt": "Draft a PA justification"}).json()
    assert run["run_id"]
    assert run["mode_id"] == mode["mode_id"]
    assert run["mode_name"] == "Pharmacy"
    assert run["recommended_agents"]
    assert run["requires_approval"] is True
    assert run["status"] == "planned"

    runs = client.get("/api/industry-modes/runs").json()
    assert any(item["run_id"] == run["run_id"] for item in runs["runs"])


def test_dashboard_response_shape():
    client.post("/api/industry-modes/seed")
    body = client.get("/api/industry-modes/dashboard").json()
    for key in ("total_modes", "enabled_modes", "total_runs", "available_mode_names", "recent_runs"):
        assert key in body
    assert body["total_modes"] >= 8


def test_governance_event_written():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/industry-modes/seed")
    mode = client.get("/api/industry-modes").json()["modes"][0]
    client.post(f"/api/industry-modes/{mode['mode_id']}/run", json={"prompt": "test"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "industry_mode_run" in actions or "industry_mode_seeded" in actions


def test_existing_workflows_still_pass():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/multimodal/dashboard").status_code == 200
    assert client.get("/api/business/dashboard").status_code == 200
    assert client.get("/api/departments").status_code == 200
