from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_installer_returns_readiness_and_setup_commands():
    body = client.get("/api/os/installer").json()
    assert body["platform"] == "EvolveAgent OS"
    assert body["version"] == "v15.0"
    assert isinstance(body["backend_steps"], list) and body["backend_steps"]
    assert isinstance(body["frontend_steps"], list) and body["frontend_steps"]
    assert isinstance(body["verification_commands"], list) and body["verification_commands"]
    readiness = body["readiness"]
    assert readiness["backend_requirements_present"] is True
    assert readiness["frontend_package_present"] is True
    assert readiness["env_example_present"] is True
    assert isinstance(readiness["missing_recommended_config"], list)
    assert isinstance(body["safety_notes"], list) and body["safety_notes"]


def test_plugin_sdk_returns_schema_and_example_manifest():
    body = client.get("/api/os/plugin-sdk").json()
    assert "manifest_schema" in body
    assert body["permission_levels"] == [
        "read_only",
        "plan_only",
        "approve_to_edit",
        "approve_to_run",
        "blocked",
    ]
    example = body["example_manifest"]
    assert example["name"]
    assert isinstance(example["tools"], list) and example["tools"]
    assert all(tool["permission_level"] in body["permission_levels"] for tool in example["tools"])


def test_plugin_validation_passes_valid_manifest():
    manifest = {
        "name": "demo-plugin",
        "version": "1.0.0",
        "description": "A demo plugin.",
        "tools": [
            {"name": "lookup", "description": "Look something up.", "permission_level": "read_only"},
        ],
    }
    body = client.post("/api/os/plugin-sdk/validate", json={"manifest": manifest}).json()
    assert body["valid"] is True
    assert body["errors"] == []
    assert body["normalized_manifest"]["name"] == "demo-plugin"
    assert body["normalized_manifest"]["tools"][0]["permission_level"] == "read_only"


def test_plugin_validation_rejects_missing_fields():
    body = client.post("/api/os/plugin-sdk/validate", json={"manifest": {"name": "incomplete"}}).json()
    assert body["valid"] is False
    assert any("version is required" in error for error in body["errors"])
    assert any("description is required" in error for error in body["errors"])
    assert any("tools" in error for error in body["errors"])
    assert body["normalized_manifest"] == {}


def test_plugin_validation_rejects_invalid_permission_level():
    manifest = {
        "name": "bad-perm",
        "version": "1.0.0",
        "description": "Bad permission level.",
        "tools": [
            {"name": "danger", "description": "Do a thing.", "permission_level": "root"},
        ],
    }
    body = client.post("/api/os/plugin-sdk/validate", json={"manifest": manifest}).json()
    assert body["valid"] is False
    assert any("permission_level" in error for error in body["errors"])


def test_sla_endpoint_returns_score_and_rating():
    body = client.get("/api/os/sla").json()
    assert 0 <= body["uptime_proxy_score"] <= 100
    assert body["sla_rating"] in {"excellent", "good", "watch", "at_risk"}
    assert 0 <= body["success_rate"] <= 100
    assert 0 <= body["fallback_rate"] <= 100
    assert isinstance(body["recent_incidents"], list)
    assert isinstance(body["recommendations"], list) and body["recommendations"]


def test_scheduler_endpoint_returns_health():
    body = client.get("/api/os/scheduler").json()
    assert body["scheduler_health"] in {"healthy", "watch", "blocked"}
    for key in ("queued_jobs", "running_jobs", "paused_jobs", "failed_jobs", "pending_approvals"):
        assert isinstance(body[key], int)
    assert isinstance(body["bottlenecks"], list)
    assert isinstance(body["recommendations"], list) and body["recommendations"]


def test_os_summary_combines_sections():
    body = client.get("/api/os/summary").json()
    assert body["platform"] == "EvolveAgent OS"
    assert body["version"] == "v15.0"
    assert "local-first" in body["positioning"]
    assert "backend_requirements_present" in body["installer_readiness"]
    assert "permission_levels" in body["plugin_sdk"]
    assert body["sla_rating"] in {"excellent", "good", "watch", "at_risk"}
    assert body["scheduler_health"] in {"healthy", "watch", "blocked"}
    assert isinstance(body["safety_notes"], list) and body["safety_notes"]
