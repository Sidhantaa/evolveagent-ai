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
    assert job["manual_review_required"] is False
    assert job["failure_stage"] is None
    assert job["test_result"]["command"] == "pytest"
    assert job["build_result"]["command"] == "npm run build"
    assert job["verification_summary"] == "pytest: passed; npm run build: passed"
    assert "EVO-170 completed" in job["summary"]


# ------------------------------------------------------------------
# Round 32: update_job() had the same lost-update shape rounds 25-31 fixed
# elsewhere -- read_list() + write_list() as two separate lock acquisitions.
# run_for_issue() calls update_job() ~15 times over a multi-second run
# (subprocess Codex CLI + git commit/push/verify); the background Linear
# poll worker can run one issue's job inline while a foreground request runs
# a different issue's job, racing on this same file. Independently confirmed
# via a standalone repro against the true unmodified code before writing any
# fix: a concurrent update_job() for a DIFFERENT job silently lost its status
# update.
# ------------------------------------------------------------------
def test_update_job_does_not_lose_a_concurrent_update_of_a_different_job(tmp_path):
    import threading
    import time

    storage = StorageService(data_dir=str(tmp_path))
    service = CodexJobService(storage)
    job_x = service.create_job({"issue_id": "X"})
    job_y = service.create_job({"issue_id": "Y"})

    entered = threading.Event()
    original_update_list = storage.update_list

    def _slow_update_list(filename, mutator):
        def _slow_mutator(items):
            entered.set()
            time.sleep(0.2)
            return mutator(items)
        return original_update_list(filename, _slow_mutator)

    storage.update_list = _slow_update_list

    def _update_x():
        service.update_job(job_x["job_id"], {"status": "running"})

    thread = threading.Thread(target=_update_x)
    thread.start()
    entered.wait(timeout=2)
    service.update_job(job_y["job_id"], {"commit_hash": "abc123"})  # concurrent update of a DIFFERENT job
    thread.join(timeout=2)

    assert service.get_job(job_x["job_id"])["status"] == "running"  # must not be lost -- failed before the fix
    assert service.get_job(job_y["job_id"])["commit_hash"] == "abc123"  # must not be lost -- failed before the fix


# ------------------------------------------------------------------
# Round 34 (error-path lens): run_for_issue()'s try block only caught
# (CodexWorkerError, LinearServiceError) -- any OTHER real exception (e.g.
# subprocess.TimeoutExpired from the Codex CLI overrunning its 600s timeout)
# escaped uncaught, leaving the job stuck "running" forever. Worse: the
# "already running" guard then permanently blocked every future
# run_for_issue() call for that issue (background poll AND manual route)
# until a human hand-edited codex_jobs.json. Independently confirmed via a
# standalone repro against the true unmodified code before writing any fix.
# ------------------------------------------------------------------
def test_unexpected_exception_terminates_the_job_instead_of_wedging_it(codex_env, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")

    def _timeout_codex_runner(cli_command, project_root, prompt):
        raise subprocess.TimeoutExpired(cmd="codex", timeout=600)

    codex_env["worker"]._codex_runner = _timeout_codex_runner

    result = codex_env["worker"].run_for_issue("issue-170")
    job = result["job"]
    assert job["status"] == "failed"  # terminal, not stuck "running"
    assert job["manual_review_required"] is True
    assert "TimeoutExpired" in job["error"]
    assert job["failure_stage"] == "codex_execution"

    # The issue must not be permanently wedged -- a second attempt is allowed
    # (it will hit the same timeout again in this test, but it must be able
    # to TRY, not be blocked by "already running" against a job that will
    # never terminate on its own).
    second = codex_env["worker"].run_for_issue("issue-170")
    assert second["job"]["status"] == "failed"


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
    assert result["job"]["failure_stage"] == "handoff_validation"
    assert result["job"]["manual_review_required"] is True
    assert "Handoff file missing" in result["error"]


def test_unsafe_changed_files_block_commit(codex_env, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")
    codex_env["git"].list_changed_files.return_value = ["backend/.env"]
    result = codex_env["worker"].run_for_issue("issue-170")
    assert result["job"]["status"] == "blocked"
    assert result["job"]["failure_stage"] == "change_safety_check"
    assert result["job"]["status_detail"] == "Blocked by worker safety rules"
    assert result["job"]["manual_review_required"] is True
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
    assert result["job"]["status"] == "needs_manual_review"
    assert result["job"]["failure_stage"] == "verification"
    assert result["job"]["linear_done"] is False
    assert result["job"]["manual_review_required"] is True
    assert result["job"]["verification_summary"] == "pytest: failed; npm run build: passed"
    codex_env["git"].commit.assert_not_called()
    codex_env["orchestration"].verify_cursor_work.assert_not_called()


def test_successful_mocked_codex_run_commits_and_verifies(codex_env, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")
    result = codex_env["worker"].run_for_issue("issue-170")
    codex_env["git"].commit.assert_called_once()
    codex_env["orchestration"].verify_cursor_work.assert_called_once()
    assert result["job"]["status"] == "passed"
    assert result["verify_result"]["verified"] is True


def test_failure_comment_includes_stage_and_verification(codex_env, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")
    codex_env["runner"].run.side_effect = lambda command: CommandResult(
        command=command,
        exit_code=1 if command == "pytest" else 0,
        stdout="",
        stderr="fail" if command == "pytest" else "",
        success=command != "pytest",
    )
    result = codex_env["worker"].run_for_issue("issue-170")
    assert result["job"]["status"] == "needs_manual_review"
    codex_env["orchestration"].linear.add_linear_comment.assert_called_once()
    comment = codex_env["orchestration"].linear.add_linear_comment.call_args.args[1]
    assert "needs manual review" in comment
    assert "Stage: `verification`" in comment
    assert "pytest: failed; npm run build: passed" in comment


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
