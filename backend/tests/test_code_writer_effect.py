"""v150 task 1 — Autonomous Software Team: a durable-workflow step with
action_type="write_code_change" is a WHITELISTED effect (always approval-gated,
like create_task/create_note/create_github_issue), and — only after approval —
performs a real (opt-in, allow-listed-repo) local git commit via
CodeWriterService. Without a code_writer collaborator wired, with writes
disabled, or against a non-allow-listed repo, it degrades to a safe recorded
refusal, never a silent no-op and never a crash."""

import subprocess

from app.services.code_writer_service import CodeWriterService
from app.services.durable_workflow_service import DurableWorkflowService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


def _init_repo(path) -> str:
    repo = str(path)
    subprocess.run(["git", "init", "-q", repo], check=True)
    subprocess.run(["git", "-C", repo, "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", repo, "config", "user.name", "Test"], check=True)
    (path / "README.md").write_text("init\n")
    subprocess.run(["git", "-C", repo, "add", "."], check=True)
    subprocess.run(["git", "-C", repo, "commit", "-q", "-m", "initial"], check=True)
    return repo


def _step(repo: str):
    return {"name": "add a helper", "action_type": "write_code_change",
            "action_params": {"repo_path": repo, "file_path": "src/helper.py",
                               "content": "def helper():\n    return 1\n", "commit_message": "add helper"}}


def test_without_code_writer_wired_step_degrades_safely_but_run_completes(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    s = StorageService(data_dir=str(tmp_path / "data"))
    g = GovernanceService(s)
    workflows = DurableWorkflowService(s, g)  # no code_writer collaborator
    definition = workflows.create_definition({"name": "NoCodeWriter", "steps": [_step(repo)]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run["status"] == "waiting_approval"  # whitelisted -> always approval-gated
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"
    assert "declined" in finished["steps"][0]["output"]
    effects = workflows.effects(run["run_id"])["effects"]
    assert effects[0]["result"]["wrote"] is False


def test_writes_disabled_declines_but_run_still_completes(tmp_path, monkeypatch):
    monkeypatch.delenv("CODE_WRITES_ENABLED", raising=False)
    repo = _init_repo(tmp_path / "repo")
    s = StorageService(data_dir=str(tmp_path / "data"))
    g = GovernanceService(s)
    code_writer = CodeWriterService(g)
    workflows = DurableWorkflowService(s, g, code_writer=code_writer)
    definition = workflows.create_definition({"name": "WritesOff", "steps": [_step(repo)]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"
    assert "declined" in finished["steps"][0]["output"]


def test_approved_step_performs_a_real_commit_when_opted_in(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "repo")
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    s = StorageService(data_dir=str(tmp_path / "data"))
    g = GovernanceService(s)
    code_writer = CodeWriterService(g)
    workflows = DurableWorkflowService(s, g, code_writer=code_writer)
    definition = workflows.create_definition({"name": "RealWrite", "steps": [_step(repo)]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run["status"] == "waiting_approval"  # never auto-runs, even though it's the only step
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"
    assert "executed" in finished["steps"][0]["output"]
    effects = workflows.effects(run["run_id"])["effects"]
    assert effects[0]["result"]["wrote"] is True
    assert (tmp_path / "repo" / "src" / "helper.py").exists()


def test_rejected_step_never_calls_code_writer(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "repo")
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)

    def fail_if_called(self, *args, **kwargs):
        raise AssertionError("write_and_commit must never be called for a rejected step")

    monkeypatch.setattr(CodeWriterService, "write_and_commit", fail_if_called)
    s = StorageService(data_dir=str(tmp_path / "data"))
    g = GovernanceService(s)
    code_writer = CodeWriterService(g)
    workflows = DurableWorkflowService(s, g, code_writer=code_writer)
    definition = workflows.create_definition({"name": "Rejected", "steps": [_step(repo)]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    rejected = workflows.approve_step(run["run_id"], approved=False)
    assert rejected["status"] == "completed"
    assert rejected["steps"][0]["status"] == "skipped"
    assert not (tmp_path / "repo" / "src" / "helper.py").exists()


def test_non_allow_listed_repo_declines_even_when_writes_enabled(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "repo")
    other_repo = _init_repo(tmp_path / "other-repo")
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", other_repo)  # repo itself is NOT allow-listed
    s = StorageService(data_dir=str(tmp_path / "data"))
    g = GovernanceService(s)
    code_writer = CodeWriterService(g)
    workflows = DurableWorkflowService(s, g, code_writer=code_writer)
    definition = workflows.create_definition({"name": "NotAllowed", "steps": [_step(repo)]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"
    assert "declined" in finished["steps"][0]["output"]
    assert not (tmp_path / "repo" / "src" / "helper.py").exists()


def test_end_to_end_via_api(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.delenv("CODE_WRITES_ENABLED", raising=False)
    repo = _init_repo(tmp_path / "repo")
    client = TestClient(app)
    d = client.post("/api/durable-workflows/definitions", json={
        "name": "E2E-Code-Write", "steps": [_step(repo)],
    }).json()
    run = client.post("/api/durable-workflows/runs", json={"definition_id": d["definition_id"]}).json()
    assert run["status"] == "waiting_approval"
    finished = client.post(f"/api/durable-workflows/runs/{run['run_id']}/approve", json={"approved": True}).json()
    assert finished["status"] == "completed"
    assert "declined" in finished["steps"][0]["output"]  # writes disabled by default in the live app


# ------------------------------------------------------------------
# v150 task 3 — a write_code_change step can propose a change spanning several
# files by passing a JSON-encoded "files" array in action_params (required,
# since action_params values are always plain strings by the time a step
# definition reaches this service).
# ------------------------------------------------------------------
def _multi_file_step(repo: str):
    import json
    files = [
        {"file_path": "src/a.py", "content": "a = 1\n"},
        {"file_path": "src/b.py", "content": "b = 2\n"},
    ]
    return {"name": "add a/b", "action_type": "write_code_change",
            "action_params": {"repo_path": repo, "files": json.dumps(files), "commit_message": "add a and b"}}


def test_multi_file_step_dispatches_to_write_files_and_commit(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "repo")
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    s = StorageService(data_dir=str(tmp_path / "data"))
    g = GovernanceService(s)
    code_writer = CodeWriterService(g)
    workflows = DurableWorkflowService(s, g, code_writer=code_writer)
    definition = workflows.create_definition({"name": "MultiFile", "steps": [_multi_file_step(repo)]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"
    assert "files=2" in finished["steps"][0]["output"]
    effects = workflows.effects(run["run_id"])["effects"]
    assert set(effects[0]["result"]["file_paths"]) == {"src/a.py", "src/b.py"}
    assert (tmp_path / "repo" / "src" / "a.py").read_text() == "a = 1\n"
    assert (tmp_path / "repo" / "src" / "b.py").read_text() == "b = 2\n"


def test_malformed_files_json_falls_back_to_single_file_path_gracefully(tmp_path, monkeypatch):
    """A malformed "files" value must never crash the workflow engine — it
    falls back to the single-file path, which then declines cleanly since
    file_path/content are absent."""
    repo = _init_repo(tmp_path / "repo")
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    s = StorageService(data_dir=str(tmp_path / "data"))
    g = GovernanceService(s)
    code_writer = CodeWriterService(g)
    workflows = DurableWorkflowService(s, g, code_writer=code_writer)
    step = {"name": "bad json", "action_type": "write_code_change",
            "action_params": {"repo_path": repo, "files": "not valid json", "commit_message": "x"}}
    definition = workflows.create_definition({"name": "BadJson", "steps": [step]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"  # never crashes
    assert "declined" in finished["steps"][0]["output"]
