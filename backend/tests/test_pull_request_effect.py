"""v150 task 2 — Autonomous Software Team: a durable-workflow step with
action_type="open_pull_request" is a WHITELISTED effect, SEPARATE from
write_code_change (its own approval gate for the escalation from "local
commit" to "visible to others"). It pushes a branch (real git push to a local
bare repo standing in for origin — zero network access in tests) and, only if
the push succeeds, opens a real (mocked HTTP) GitHub pull request. Any missing
collaborator or disabled opt-in degrades to a safe recorded refusal."""

import subprocess

from app.services.code_writer_service import CodeWriterService
from app.services.durable_workflow_service import DurableWorkflowService
from app.services.github_connector_service import GitHubConnectorService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


def _init_repo_with_bare_origin(tmp_path):
    bare = str(tmp_path / "origin.git")
    subprocess.run(["git", "init", "-q", "--bare", bare], check=True)
    repo = str(tmp_path / "repo")
    subprocess.run(["git", "init", "-q", repo], check=True)
    subprocess.run(["git", "-C", repo, "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", repo, "config", "user.name", "Test"], check=True)
    (tmp_path / "repo" / "README.md").write_text("init\n")
    subprocess.run(["git", "-C", repo, "add", "."], check=True)
    subprocess.run(["git", "-C", repo, "commit", "-q", "-m", "initial"], check=True)
    subprocess.run(["git", "-C", repo, "remote", "add", "origin", bare], check=True)
    subprocess.run(["git", "-C", repo, "checkout", "-q", "-b", "feature/x"], check=True)
    return repo, bare


def _step():
    return {"name": "open a PR", "action_type": "open_pull_request",
            "action_params": {"repo_path": "REPO", "branch_name": "feature/x", "github_repo": "owner/repo",
                               "title": "Add helper", "body": "details", "base": "main"}}


def _fill_repo(step, repo):
    step["action_params"]["repo_path"] = repo
    return step


def test_without_collaborators_wired_step_degrades_safely_but_run_completes(tmp_path):
    repo, _ = _init_repo_with_bare_origin(tmp_path)
    s = StorageService(data_dir=str(tmp_path / "data"))
    g = GovernanceService(s)
    workflows = DurableWorkflowService(s, g)  # no code_writer, no github
    definition = workflows.create_definition({"name": "NoCollaborators", "steps": [_fill_repo(_step(), repo)]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run["status"] == "waiting_approval"
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"
    assert "declined" in finished["steps"][0]["output"]
    effects = workflows.effects(run["run_id"])["effects"]
    assert effects[0]["result"]["wrote"] is False


def test_push_disabled_declines_and_never_calls_github(tmp_path, monkeypatch):
    repo, _ = _init_repo_with_bare_origin(tmp_path)
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.delenv("CODE_WRITER_PUSH_ENABLED", raising=False)  # push itself still off
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    monkeypatch.setenv("GITHUB_WRITES_ENABLED", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fail_if_called(self, path, body):
        raise AssertionError("create_pull_request must never be called if the push declined")

    monkeypatch.setattr(GitHubConnectorService, "_http_post", fail_if_called)
    s = StorageService(data_dir=str(tmp_path / "data"))
    g = GovernanceService(s)
    code_writer = CodeWriterService(g)
    github = GitHubConnectorService(s, g)
    workflows = DurableWorkflowService(s, g, code_writer=code_writer, github=github)
    definition = workflows.create_definition({"name": "PushOff", "steps": [_fill_repo(_step(), repo)]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"
    assert "declined" in finished["steps"][0]["output"]


def test_push_succeeds_but_github_writes_disabled_still_declines_the_pr(tmp_path, monkeypatch):
    repo, bare = _init_repo_with_bare_origin(tmp_path)
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_PUSH_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    monkeypatch.delenv("GITHUB_WRITES_ENABLED", raising=False)  # PR creation itself still off
    s = StorageService(data_dir=str(tmp_path / "data"))
    g = GovernanceService(s)
    code_writer = CodeWriterService(g)
    github = GitHubConnectorService(s, g)
    workflows = DurableWorkflowService(s, g, code_writer=code_writer, github=github)
    definition = workflows.create_definition({"name": "PrOff", "steps": [_fill_repo(_step(), repo)]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"
    assert "declined" in finished["steps"][0]["output"]
    effects = workflows.effects(run["run_id"])["effects"]
    assert effects[0]["result"]["pushed"] is True  # the push itself really happened
    branches = subprocess.run(["git", "-C", bare, "branch"], capture_output=True, text=True, check=True).stdout
    assert "feature/x" in branches


def test_approved_step_pushes_and_opens_a_real_pr_when_fully_opted_in(tmp_path, monkeypatch):
    repo, bare = _init_repo_with_bare_origin(tmp_path)
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_PUSH_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    monkeypatch.setenv("GITHUB_WRITES_ENABLED", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_post(self, path, body):
        return {"id": 1, "number": 9, "title": body["title"], "state": "open", "draft": False,
                "user": {"login": "eva-bot"}, "head": {"ref": body["head"]}, "base": {"ref": body["base"]},
                "html_url": "https://github.com/owner/repo/pull/9",
                "created_at": "2026-07-08T00:00:00Z", "updated_at": "2026-07-08T00:00:00Z"}

    monkeypatch.setattr(GitHubConnectorService, "_http_post", fake_post)
    s = StorageService(data_dir=str(tmp_path / "data"))
    g = GovernanceService(s)
    code_writer = CodeWriterService(g)
    github = GitHubConnectorService(s, g)
    workflows = DurableWorkflowService(s, g, code_writer=code_writer, github=github)
    definition = workflows.create_definition({"name": "FullyOn", "steps": [_fill_repo(_step(), repo)]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run["status"] == "waiting_approval"  # never auto-runs
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"
    assert "executed" in finished["steps"][0]["output"]
    assert "pull/9" in finished["steps"][0]["output"]
    effects = workflows.effects(run["run_id"])["effects"]
    assert effects[0]["result"]["pull_request"]["number"] == 9
    branches = subprocess.run(["git", "-C", bare, "branch"], capture_output=True, text=True, check=True).stdout
    assert "feature/x" in branches


def test_rejected_step_never_pushes_or_opens_a_pr(tmp_path, monkeypatch):
    repo, bare = _init_repo_with_bare_origin(tmp_path)
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_PUSH_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    monkeypatch.setenv("GITHUB_WRITES_ENABLED", "true")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fail_if_called(self, path, body):
        raise AssertionError("create_pull_request must never be called for a rejected step")

    monkeypatch.setattr(GitHubConnectorService, "_http_post", fail_if_called)
    s = StorageService(data_dir=str(tmp_path / "data"))
    g = GovernanceService(s)
    code_writer = CodeWriterService(g)
    github = GitHubConnectorService(s, g)
    workflows = DurableWorkflowService(s, g, code_writer=code_writer, github=github)
    definition = workflows.create_definition({"name": "Rejected", "steps": [_fill_repo(_step(), repo)]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    rejected = workflows.approve_step(run["run_id"], approved=False)
    assert rejected["status"] == "completed"
    assert rejected["steps"][0]["status"] == "skipped"
    branches = subprocess.run(["git", "-C", bare, "branch"], capture_output=True, text=True, check=True).stdout
    assert "feature/x" not in branches  # never pushed


def test_end_to_end_via_api(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.delenv("CODE_WRITER_PUSH_ENABLED", raising=False)
    repo, _ = _init_repo_with_bare_origin(tmp_path)
    client = TestClient(app)
    d = client.post("/api/durable-workflows/definitions", json={
        "name": "E2E-Open-PR", "steps": [_fill_repo(_step(), repo)],
    }).json()
    run = client.post("/api/durable-workflows/runs", json={"definition_id": d["definition_id"]}).json()
    assert run["status"] == "waiting_approval"
    finished = client.post(f"/api/durable-workflows/runs/{run['run_id']}/approve", json={"approved": True}).json()
    assert finished["status"] == "completed"
    assert "declined" in finished["steps"][0]["output"]  # pushing disabled by default in the live app
