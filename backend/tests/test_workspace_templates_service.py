from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_template(**overrides) -> dict:
    payload = {
        "name": overrides.get("name", "Engineering workspace"),
        "description": overrides.get("description", "Preset for engineering work."),
        "default_tags": overrides.get("default_tags", ["eng", "code"]),
        "preset": overrides.get("preset", {"theme": "dark", "mode": "developer"}),
    }
    response = client.post("/api/workspace-templates", json=payload)
    assert response.status_code == 200
    return response.json()


def test_create_and_list_template():
    template = _create_template()
    assert template["template_id"]
    assert template["default_tags"] == ["eng", "code"]
    assert template["preset"]["theme"] == "dark"
    listed = client.get("/api/workspace-templates").json()
    assert any(t["template_id"] == template["template_id"] for t in listed["templates"])


def test_instantiate_creates_real_workspace():
    template = _create_template()
    before = len(client.get("/api/workspaces").json())
    result = client.post(f"/api/workspace-templates/{template['template_id']}/instantiate", json={"name": "My eng ws"}).json()
    assert result["workspace_id"]
    assert result["workspace_name"] == "My eng ws"
    assert "local record only" in result["note"].lower()
    after = len(client.get("/api/workspaces").json())
    assert after == before + 1  # a real workspace was created


def test_instantiation_count_increments():
    template = _create_template()
    client.post(f"/api/workspace-templates/{template['template_id']}/instantiate", json={})
    client.post(f"/api/workspace-templates/{template['template_id']}/instantiate", json={})
    fetched = next(t for t in client.get("/api/workspace-templates").json()["templates"] if t["template_id"] == template["template_id"])
    assert fetched["instantiation_count"] >= 2


def test_instantiate_missing_template_404():
    assert client.post("/api/workspace-templates/missing/instantiate", json={}).status_code == 404


def test_summary_and_analytics():
    _create_template()
    s = client.get("/api/workspace-templates/summary").json()
    for key in ("template_count", "total_instantiations", "note"):
        assert key in s
    assert "no production provisioning" in s["note"].lower()
    analytics = client.get("/api/analytics").json()
    for key in ("workspace_templates", "workspace_template_instantiations"):
        assert key in analytics


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    template = _create_template()
    client.post(f"/api/workspace-templates/{template['template_id']}/instantiate", json={})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "workspace_template_created" in actions or "workspace_template_instantiated" in actions


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/notifications/summary").status_code == 200
    assert client.get("/api/operating-layer-2/dashboard").status_code == 200
