from fastapi.testclient import TestClient

from app.main import app
from app.api import routes


client = TestClient(app)


def _reset_settings() -> None:
    routes.autopilot_service.update_settings(
        {"kill_switch_enabled": False, "permission_mode": "supervised"}
    )


def test_create_autopilot_run_and_permission_tier_classification():
    _reset_settings()
    response = client.post(
        "/api/autopilot/runs",
        json={
            "prompt": "Refactor the billing summary helper and run the unit tests",
            "actions": [
                {"action_type": "file_scan", "summary": "Read the billing helper"},
                {
                    "action_type": "file_edit",
                    "summary": "Edit billing helper",
                    "files_targeted": ["app/services/billing.py"],
                },
                {"action_type": "command_run", "summary": "Run unit tests", "command_requested": "pytest -q"},
            ],
        },
    )
    assert response.status_code == 200
    run = response.json()
    assert run["actions_count"] == 3

    actions = {action["action_type"]: action for action in run["actions"]}
    assert actions["file_scan"]["permission_level"] == "read_only"
    assert actions["file_edit"]["permission_level"] == "approve_to_edit"
    assert actions["command_run"]["permission_level"] == "approve_to_run"
    # Read-only proceeds; risky actions wait for approval. No silent execution.
    assert actions["file_scan"]["status"] == "planned"
    assert actions["file_edit"]["status"] == "waiting_approval"
    assert actions["command_run"]["status"] == "waiting_approval"
    assert run["status"] == "waiting_approval"


def test_checkpoint_created_for_edit_and_run_actions():
    _reset_settings()
    run = client.post(
        "/api/autopilot/runs",
        json={
            "prompt": "Apply a patch and run the build",
            "actions": [
                {"action_type": "file_edit", "summary": "Patch module", "files_targeted": ["app/services/x.py"]},
                {"action_type": "build_run", "summary": "Build", "command_requested": "npm run build"},
            ],
        },
    ).json()
    checkpoints = client.get(f"/api/autopilot/checkpoints?run_id={run['run_id']}").json()
    assert len(checkpoints) == 2
    assert all(cp["status"] == "pending" for cp in checkpoints)
    assert {cp["permission_level"] for cp in checkpoints} == {"approve_to_edit", "approve_to_run"}


def test_read_only_run_completes_without_checkpoint():
    _reset_settings()
    create = client.post(
        "/api/autopilot/runs",
        json={
            "prompt": "Scan the project",
            "actions": [{"action_type": "project_scan", "summary": "Scan repo layout"}],
        },
    ).json()
    assert client.get(f"/api/autopilot/checkpoints?run_id={create['run_id']}").json() == []

    started = client.post(f"/api/autopilot/runs/{create['run_id']}/start").json()
    assert started["status"] == "completed"
    assert started["actions"][0]["status"] == "completed"


def test_kill_switch_blocks_execution():
    _reset_settings()
    settings = client.patch("/api/autopilot/settings", json={"kill_switch_enabled": True}).json()
    assert settings["kill_switch_enabled"] is True

    create = client.post(
        "/api/autopilot/runs",
        json={
            "prompt": "Edit a file while kill switch is on",
            "actions": [{"action_type": "file_edit", "summary": "Edit", "files_targeted": ["app/services/y.py"]}],
        },
    ).json()
    started = client.post(f"/api/autopilot/runs/{create['run_id']}/start").json()
    assert started["status"] == "blocked"
    run = client.get(f"/api/autopilot/runs/{create['run_id']}").json()
    assert all(action["status"] == "blocked" for action in run["actions"])

    governance = client.get("/api/governance").json()
    assert any(
        event.get("run_id") == create["run_id"]
        and event.get("action_type") == "autopilot_blocked_by_kill_switch"
        for event in governance["recent_events"]
    )
    _reset_settings()


def test_approve_checkpoint_allows_completion():
    _reset_settings()
    create = client.post(
        "/api/autopilot/runs",
        json={
            "prompt": "Edit then approve",
            "actions": [{"action_type": "file_edit", "summary": "Edit safe file", "files_targeted": ["app/services/z.py"]}],
        },
    ).json()
    checkpoint = client.get(f"/api/autopilot/checkpoints?run_id={create['run_id']}").json()[0]

    decided = client.post(
        f"/api/autopilot/checkpoints/{checkpoint['checkpoint_id']}/decision",
        json={"decision": "approve", "comment": "Looks safe"},
    ).json()
    assert decided["status"] == "approved"

    run = client.get(f"/api/autopilot/runs/{create['run_id']}").json()
    assert run["actions"][0]["status"] == "approved"

    # Only after explicit approval does the run reach completion.
    started = client.post(f"/api/autopilot/runs/{create['run_id']}/start").json()
    assert started["status"] == "completed"
    assert started["actions"][0]["status"] == "completed"


def test_reject_checkpoint_stops_action():
    _reset_settings()
    create = client.post(
        "/api/autopilot/runs",
        json={
            "prompt": "Run a command then reject",
            "actions": [{"action_type": "command_run", "summary": "Run tests", "command_requested": "pytest"}],
        },
    ).json()
    checkpoint = client.get(f"/api/autopilot/checkpoints?run_id={create['run_id']}").json()[0]

    decided = client.post(
        f"/api/autopilot/checkpoints/{checkpoint['checkpoint_id']}/decision",
        json={"decision": "reject", "comment": "Not now"},
    ).json()
    assert decided["status"] == "rejected"

    run = client.get(f"/api/autopilot/runs/{create['run_id']}").json()
    assert run["actions"][0]["status"] == "rejected"


def test_unsafe_action_blocked_at_planning():
    _reset_settings()
    create = client.post(
        "/api/autopilot/runs",
        json={
            "prompt": "Try an unsafe command and path",
            "actions": [
                {"action_type": "command_run", "summary": "Remove files", "command_requested": "rm -rf build"},
                {"action_type": "file_edit", "summary": "Touch env", "files_targeted": [".env"]},
            ],
        },
    ).json()
    levels = {action["action_type"]: action for action in create["actions"]}
    assert levels["command_run"]["permission_level"] == "blocked"
    assert levels["command_run"]["status"] == "blocked"
    assert levels["file_edit"]["permission_level"] == "blocked"
    assert levels["file_edit"]["status"] == "blocked"
    # No checkpoint is created for blocked actions.
    assert client.get(f"/api/autopilot/checkpoints?run_id={create['run_id']}").json() == []


def test_governance_log_written_for_run_lifecycle():
    _reset_settings()
    create = client.post(
        "/api/autopilot/runs",
        json={"prompt": "Plan only run", "actions": [{"action_type": "automation_plan", "summary": "Draft plan"}]},
    ).json()
    governance = client.get("/api/governance").json()
    logged = {
        event.get("action_type")
        for event in governance["recent_events"]
        if event.get("run_id") == create["run_id"]
    }
    assert "autopilot_run_created" in logged
    assert "autopilot_action_planned" in logged


def test_stop_run_blocks_pending_actions():
    _reset_settings()
    create = client.post(
        "/api/autopilot/runs",
        json={
            "prompt": "Start then stop",
            "actions": [{"action_type": "file_edit", "summary": "Edit", "files_targeted": ["app/services/q.py"]}],
        },
    ).json()
    stopped = client.post(f"/api/autopilot/runs/{create['run_id']}/stop", json={"reason": "operator halt"}).json()
    assert stopped["status"] == "stopped"
    run = client.get(f"/api/autopilot/runs/{create['run_id']}").json()
    assert run["actions"][0]["status"] == "blocked"


def test_existing_run_endpoint_still_works():
    _reset_settings()
    response = client.post(
        "/api/run",
        json={"user_input": "Give a short summary of the workspace status", "task_type": "auto"},
    )
    assert response.status_code == 200
    assert response.json()["final_output"]


def test_existing_approvals_endpoint_still_works():
    response = client.get("/api/approvals")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_existing_governance_endpoint_still_works():
    response = client.get("/api/governance")
    assert response.status_code == 200
    assert "recent_events" in response.json()
