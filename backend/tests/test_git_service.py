from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from app.config import settings
from app.services.git_service import GitService


def test_git_service_blocks_unsafe_paths():
    service = GitService()

    assert service.is_safe_path("README.md") is True
    assert service.is_safe_path("backend/app/main.py") is True
    assert service.is_safe_path(".env") is False
    assert service.is_safe_path("backend/.env") is False
    assert service.is_safe_path("node_modules/react/index.js") is False
    assert service.is_safe_path("backend/app/data/tasks.json") is False
    assert service.is_safe_path("../outside.txt") is False


def test_git_push_skips_when_auto_push_disabled(monkeypatch):
    monkeypatch.setattr(settings, "auto_git_push", False)
    service = GitService()
    service._run = MagicMock()

    result = service.push()

    assert result["success"] is False
    assert result["skipped"] is True
    assert "AUTO_GIT_PUSH=false" in result["message"]
    service._run.assert_not_called()


# ------------------------------------------------------------------
# Round 35 (error-path lens): _run() previously called subprocess.run()
# with NO timeout at all -- meaning it could never even raise
# TimeoutExpired, it would just block the calling thread forever on any
# real hang (a stale .git/index.lock, `push` stalling on a credential
# prompt or an unreachable remote). Every caller (including
# CodexWorkerService.run_for_issue(), which drives real git commands per
# Linear issue) only checks result.returncode == 0, so a real hang now
# degrades to a synthetic failed CompletedProcess instead of hanging the
# request/thread indefinitely.
# ------------------------------------------------------------------
def test_run_passes_a_real_timeout_to_subprocess():
    service = GitService(project_root="/tmp")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(["git", "status"], 0, "", "")
        service._run("status")
    assert mock_run.call_args.kwargs.get("timeout") == 60


def test_run_degrades_gracefully_on_a_real_timeout():
    service = GitService(project_root="/tmp")

    def _hang(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs.get("timeout", 60))

    with patch("subprocess.run", side_effect=_hang):
        result = service.commit("test commit")

    assert result["success"] is False  # must not raise or hang -- failed before the fix
    assert "timed out" in result["message"]


def test_git_create_branch_normalizes_name():
    service = GitService()
    service._run = MagicMock(return_value=MagicMock(returncode=0, stdout="created", stderr=""))

    result = service.create_branch("Linear EVO 171")

    assert result["success"] is True
    assert result["branch"] == "linear-evo-171"
    service._run.assert_called_once_with("checkout", "-b", "linear-evo-171")


def test_git_create_branch_rejects_unsafe_name():
    service = GitService()
    service._run = MagicMock()

    result = service.create_branch("../main")

    assert result["success"] is False
    assert result["branch"] == ""
    assert "Unsafe branch name" in result["message"]
    service._run.assert_not_called()


def test_git_checkout_branch_rejects_unsafe_name():
    service = GitService()
    service._run = MagicMock()

    result = service.checkout_branch("-bad-branch")

    assert result["success"] is False
    assert result["branch"] == ""
    assert "Unsafe branch name" in result["message"]
    service._run.assert_not_called()


def test_git_add_safe_files_excludes_unsafe_paths():
    service = GitService()

    def fake_run(*args):
        if args == ("status", "--porcelain"):
            return MagicMock(
                returncode=0,
                stdout=" M README.md\n M backend/.env\n?? backend/app/services/git_service.py\n?? backend/app/data/local.json\n",
                stderr="",
            )
        if args[0] == "add":
            return MagicMock(returncode=0, stdout="", stderr="")
        raise AssertionError(f"unexpected git command: {args}")

    service._run = MagicMock(side_effect=fake_run)

    result = service.add_safe_files()

    assert result["success"] is True
    assert result["staged_files"] == ["README.md", "backend/app/services/git_service.py"]
    assert result["excluded_files"] == ["backend/.env", "backend/app/data/local.json"]
