from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api import routes
from app.config import settings
from app.main import app
from app.models.response_models import CommandResult
from app.services.codex_job_service import CodexJobService
from app.services.codex_worker_service import CodexWorkerService, CodexWorkerError
from app.services.git_service import GitService
from app.services.linear_link_service import LinearLinkService
from app.services.storage_service import StorageService

client = TestClient(app)


@pytest.fixture
def codex_env(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "codex_worker_enabled", True)
    monkeypatch.setattr(settings, "codex_cli_command", "codex")
    monkeypatch.setattr(settings, "codex_max_files_changed", 8)
    monkeypatch.setattr(settings, "auto_git_push", False)
    monkeypatch.setattr(settings, "linear_api_key", "test-key")
    monkeypatch.setattr(settings, "linear_team_id", "team-1")

    storage = StorageService(data_dir=str(tmp_path))
    jobs = CodexJobService(storage)
    links = LinearLinkService(storage)
    handoff_dir = tmp_path / "docs" / "linear-handoffs"
    handoff_dir.mkdir(parents=True)
    handoff_path = handoff_dir / "evo-170.md"
    handoff_path.write_text("# EVO-170 handoff\nImplement feature.", encoding="utf-8")

    links.create_or_update_link(
        {
            "linear_issue_id": "issue-170",
            "linear_identifier": "EVO-170",
            "branch_name": "linear/evo-170",
            "cursor_brief_path": str(handoff_path),
            "status": "selected",
        }
    )

    git = MagicMock(spec=GitService)
    git.project_root = tmp_path
    git.checkout_branch.return_value = {"success": True, "branch": "linear/evo-170", "message": "ok"}
    git.current_branch.return_value = "linear/evo-170"
    git.list_changed_files.return_value = ["backend/app/main.py"]
    git.add_safe_files.return_value = {"success": True, "staged_files": ["backend/app/main.py"], "excluded_files": []}
    git.commit.return_value = {"success": True, "commit_hash": "abc1234", "message": "committed"}
    git.push.return_value = {"success": False, "skipped": True, "message": "Push skipped"}
    git._run.return_value = MagicMock(returncode=0, stdout="", stderr="")

    runner = MagicMock()
    runner.run.side_effect = lambda command: CommandResult(
        command=command,
        exit_code=0,
        stdout="ok",
        stderr="",
        success=True,
    )

    orchestration = MagicMock()
    orchestration.links = links
    orchestration.linear.get_linear_issue.return_value = {
        "id": "issue-170",
        "identifier": "EVO-170",
        "title": "Bridge",
    }
    orchestration.verify_cursor_work.return_value = {
        "verified": True,
        "linear_completion": {"completed": True, "identifier": "EVO-170"},
    }
    orchestration._log = MagicMock()

    def mock_codex_runner(cli_command, project_root, prompt):
        return subprocess.CompletedProcess(args=[cli_command], returncode=0, stdout="codex done", stderr="")

    worker = CodexWorkerService(
        job_service=jobs,
        git_service=git,
        command_runner=runner,
        linear_orchestration=orchestration,
        codex_runner=mock_codex_runner,
    )
    return {
        "storage": storage,
        "jobs": jobs,
        "links": links,
        "git": git,
        "runner": runner,
        "orchestration": orchestration,
        "worker": worker,
        "handoff_path": handoff_path,
    }


def test_codex_job_creation(codex_env, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")
    result = codex_env["worker"].run_for_issue("issue-170")
    job = result["job"]
    assert job["issue_identifier"] == "EVO-170"
    assert job["branch_name"] == "linear/evo-170"
    assert job["status"] == "passed"
    assert job["commit_hash"] == "abc1234"
    assert job["linear_done"] is True


def test_worker_disabled_returns_safe_error(monkeypatch):
    monkeypatch.setattr(settings, "codex_worker_enabled", False)
    worker = CodexWorkerService(
        job_service=MagicMock(),
        git_service=MagicMock(),
        command_runner=MagicMock(),
        linear_orchestration=MagicMock(),
    )
    with pytest.raises(CodexWorkerError, match="Codex worker is disabled"):
        worker.run_for_issue("issue-170")


def test_missing_handoff_file_blocks_job(codex_env, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")
    codex_env["handoff_path"].unlink()
    result = codex_env["worker"].run_for_issue("issue-170")
    assert result["job"]["status"] == "failed"
    assert "Handoff file missing" in result["error"]


def test_unsafe_changed_files_block_commit(codex_env, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")
    codex_env["git"].list_changed_files.return_value = ["backend/.env"]
    result = codex_env["worker"].run_for_issue("issue-170")
    assert result["job"]["status"] == "blocked"
    assert "Unsafe files changed" in result["error"]
    codex_env["git"].commit.assert_not_called()


def test_failed_tests_do_not_mark_linear_done(codex_env, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")
    codex_env["runner"].run.side_effect = lambda command: CommandResult(
        command=command,
        exit_code=1,
        stdout="",
        stderr="fail",
        success=command != "pytest",
    )
    result = codex_env["worker"].run_for_issue("issue-170")
    assert result["job"]["status"] == "failed"
    assert result["job"]["linear_done"] is False
    codex_env["git"].commit.assert_not_called()
    codex_env["orchestration"].verify_cursor_work.assert_not_called()


def test_successful_mocked_codex_run_commits_and_verifies(codex_env, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")
    result = codex_env["worker"].run_for_issue("issue-170")
    codex_env["git"].commit.assert_called_once()
    codex_env["orchestration"].verify_cursor_work.assert_called_once()
    assert result["job"]["status"] == "passed"
    assert result["verify_result"]["verified"] is True


def test_job_list_endpoint(codex_env, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")
    codex_env["worker"].run_for_issue("issue-170")
    monkeypatch.setattr(routes, "codex_job_service", codex_env["jobs"])
    response = client.get("/api/codex/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["issue_identifier"] == "EVO-170"


def test_job_detail_endpoint(codex_env, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")
    result = codex_env["worker"].run_for_issue("issue-170")
    job_id = result["job"]["job_id"]
    monkeypatch.setattr(routes, "codex_job_service", codex_env["jobs"])
    response = client.get(f"/api/codex/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["job_id"] == job_id


def test_codex_run_endpoint_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "codex_worker_enabled", False)
    response = client.post("/api/linear/issues/issue-170/codex-run")
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"].lower()


def test_codex_run_endpoint_success(monkeypatch):
    mock_worker = MagicMock()
    mock_worker.run_for_issue.return_value = {"job": {"job_id": "j1", "status": "passed"}}
    monkeypatch.setattr(routes, "codex_worker_service", mock_worker)
    response = client.post("/api/linear/issues/issue-170/codex-run")
    assert response.status_code == 200
    assert response.json()["job"]["status"] == "passed"


def test_poll_worker_auto_codex_when_enabled(monkeypatch):
    from app.services.linear_poll_worker import LinearPollWorker

    monkeypatch.setattr(settings, "linear_sync_enabled", True)
    monkeypatch.setattr(settings, "linear_api_key", "test-key")
    monkeypatch.setattr(settings, "linear_team_id", "team-1")
    monkeypatch.setattr(settings, "linear_autonomous_codex_worker", True)
    monkeypatch.setattr(settings, "codex_worker_enabled", True)

    linear = MagicMock()
    linear.list_in_progress_issues.return_value = [
        {"id": "issue-1", "identifier": "EVO-1", "status": "In Progress", "status_type": "started"},
    ]
    orchestration = MagicMock()
    orchestration.links.get_link_by_issue.return_value = None
    orchestration.prepare_in_progress_issue.return_value = {"branch": {"branch": "linear/evo-1"}}
    orchestration.sync_pending_completions.return_value = []

    codex_worker = MagicMock()
    codex_worker.run_for_issue.return_value = {"job": {"status": "passed", "issue_identifier": "EVO-1"}}

    worker = LinearPollWorker(linear, orchestration, codex_worker=codex_worker)
    processed = worker.poll_once()

    assert processed[0]["action"] == "prepared_and_codex"
    codex_worker.run_for_issue.assert_called_once_with("issue-1")
