"""v120 task 5 — write-capable GitHub connector: a durable-workflow step with
action_type="create_github_issue" is a WHITELISTED effect (always approval-gated,
like create_task/create_note/notify), and — only after approval — performs a real
(opt-in) GitHub write via GitHubConnectorService. Without a GitHub collaborator
wired, or with writes disabled, it degrades to a safe recorded refusal, never a
silent no-op and never a crash."""

from app.services.durable_workflow_service import DurableWorkflowService
from app.services.github_connector_service import GitHubConnectorService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


def _step():
    return {"name": "file the bug", "action_type": "create_github_issue",
            "action_params": {"repo": "owner/repo", "title": "Found a bug", "body": "steps to reproduce"}}


def test_without_github_wired_step_degrades_safely_but_run_completes(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    workflows = DurableWorkflowService(s, g)  # no github collaborator
    definition = workflows.create_definition({"name": "NoGithub", "steps": [_step()]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run["status"] == "waiting_approval"  # whitelisted -> always approval-gated
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"
    assert "declined" in finished["steps"][0]["output"]
    effects = workflows.effects(run["run_id"])["effects"]
    assert effects[0]["result"]["wrote"] is False


def test_writes_disabled_declines_but_run_still_completes(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_WRITES_ENABLED", raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    github = GitHubConnectorService(s, g)
    workflows = DurableWorkflowService(s, g, github=github)
    definition = workflows.create_definition({"name": "WritesOff", "steps": [_step()]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"
    assert "declined" in finished["steps"][0]["output"]


def test_approved_step_performs_a_real_github_write_when_opted_in(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_WRITES_ENABLED", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_post(self, path, body):
        return {"id": 1, "number": 5, "title": body["title"], "state": "open",
                "user": {"login": "eva-bot"}, "labels": [], "html_url": "https://github.com/owner/repo/issues/5",
                "created_at": "2026-07-08T00:00:00Z", "updated_at": "2026-07-08T00:00:00Z"}

    monkeypatch.setattr(GitHubConnectorService, "_http_post", fake_post)
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    github = GitHubConnectorService(s, g)
    workflows = DurableWorkflowService(s, g, github=github)
    definition = workflows.create_definition({"name": "RealWrite", "steps": [_step()]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run["status"] == "waiting_approval"  # never auto-runs, even though it's the only step
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"
    assert "executed" in finished["steps"][0]["output"]
    assert "issues/5" in finished["steps"][0]["output"]
    effects = workflows.effects(run["run_id"])["effects"]
    assert effects[0]["result"]["issue"]["number"] == 5


def test_rejected_step_never_calls_github(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_WRITES_ENABLED", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fail_if_called(self, path, body):
        raise AssertionError("create_issue must never be called for a rejected step")

    monkeypatch.setattr(GitHubConnectorService, "_http_post", fail_if_called)
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    github = GitHubConnectorService(s, g)
    workflows = DurableWorkflowService(s, g, github=github)
    definition = workflows.create_definition({"name": "Rejected", "steps": [_step()]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    rejected = workflows.approve_step(run["run_id"], approved=False)
    assert rejected["status"] == "completed"
    assert rejected["steps"][0]["status"] == "skipped"


def test_end_to_end_via_api(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.delenv("GITHUB_WRITES_ENABLED", raising=False)
    client = TestClient(app)
    d = client.post("/api/durable-workflows/definitions", json={
        "name": "E2E-GH-Issue", "steps": [_step()],
    }).json()
    run = client.post("/api/durable-workflows/runs", json={"definition_id": d["definition_id"]}).json()
    assert run["status"] == "waiting_approval"
    finished = client.post(f"/api/durable-workflows/runs/{run['run_id']}/approve", json={"approved": True}).json()
    assert finished["status"] == "completed"
