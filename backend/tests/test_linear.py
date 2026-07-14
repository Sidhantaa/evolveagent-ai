from unittest.mock import MagicMock
from pathlib import Path

import pytest

from app.config import settings
from app.services.git_service import GitService
from app.services.goal_service import GoalService
from app.services.linear_link_service import LinearLinkService
from app.services.linear_service import LinearService, LinearServiceError
from app.services.secret_scanner import SecretScanner
from app.services.storage_service import StorageService
from app.config import DATA_DIR


@pytest.fixture
def storage():
    return StorageService(DATA_DIR)


@pytest.fixture
def linear_service(monkeypatch):
    monkeypatch.setattr(settings, "linear_api_key", "test-linear-key")
    monkeypatch.setattr(settings, "linear_team_id", "team-1")
    monkeypatch.setattr(settings, "linear_project_id", "project-1")
    monkeypatch.setattr(settings, "linear_sync_enabled", True)
    return LinearService(SecretScanner())


def test_linear_status_when_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "linear_api_key", None)
    monkeypatch.setattr(settings, "linear_team_id", None)
    service = LinearService()
    status = service.get_linear_config()
    assert status["configured"] is False
    assert status["sync_enabled"] is settings.linear_sync_enabled


def test_linear_status_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "linear_api_key", "test-key")
    monkeypatch.setattr(settings, "linear_team_id", "team-1")
    monkeypatch.setattr(settings, "auto_git_push", False)
    service = LinearService()
    status = service.get_linear_config()
    assert status["configured"] is True
    assert status["team_id_set"] is True
    assert status["auto_git_push"] is False


def test_list_issues_uses_mocked_linear_response(linear_service, monkeypatch):
    sample = {
        "team": {
            "issues": {
                "nodes": [
                    {
                        "id": "issue-1",
                        "identifier": "EVO-1",
                        "title": "Build Linear bridge",
                        "description": "Sync issues",
                        "priority": 2,
                        "url": "https://linear.app/issue/EVO-1",
                        "updatedAt": "2026-06-11T00:00:00.000Z",
                        "state": {"name": "Backlog", "type": "backlog"},
                        "assignee": {"name": "Dev"},
                    }
                ]
            }
        }
    }
    monkeypatch.setattr(linear_service, "linear_graphql", lambda query, variables=None: sample)
    issues = linear_service.list_linear_issues()
    assert len(issues) == 1
    assert issues[0]["identifier"] == "EVO-1"
    assert issues[0]["status"] == "Backlog"


def test_map_issue_to_goal(linear_service):
    issue = {
        "identifier": "EVO-20",
        "title": "Build Linear integration",
        "description": "Add sync and run bridge",
        "priority": 2,
    }
    goal = linear_service.map_issue_to_goal(issue)
    assert goal["goal_title"] == "Build Linear integration"
    assert len(goal["tasks"]) == 1
    assert goal["tasks"][0]["title"] == "Build Linear integration"


def test_linear_link_service_create_and_update(storage):
    service = LinearLinkService(storage)
    link = service.create_or_update_link(
        {
            "linear_issue_id": "issue-1",
            "linear_identifier": "EVO-1",
            "linear_url": "https://linear.app/EVO-1",
            "goal_id": "goal-1",
            "workspace_id": "ws-1",
            "status": "synced",
        }
    )
    assert link["linear_identifier"] == "EVO-1"
    updated = service.update_status("issue-1", "selected", note="ready")
    assert updated["status"] == "selected"
    service.append_commit("issue-1", {"hash": "abc123", "message": "Linear EVO-1: task"})
    refreshed = service.get_link_by_issue("issue-1")
    assert refreshed["commits"][0]["hash"] == "abc123"


# ------------------------------------------------------------------
# Round 31: create_or_update_link/update_status/append_commit/append_push had
# the same lost-update shape rounds 25-30 fixed elsewhere. Real concurrent
# writers: the background Linear poll worker updates links every tick,
# racing foreground routes (issue select/run/complete, git-webhook commit/
# push events) for a DIFFERENT link. Independently confirmed via a standalone
# repro against the true unmodified code before writing any fix: updating a
# DIFFERENT link's status while another's update was in flight silently lost
# the first (earlier-writing) update.
# ------------------------------------------------------------------
def test_update_status_does_not_lose_a_concurrent_update_of_a_different_link(storage):
    import threading
    import time

    service = LinearLinkService(storage)
    service.create_or_update_link({"linear_issue_id": "LIN-31-1", "linear_identifier": "LIN-31-1"})
    service.create_or_update_link({"linear_issue_id": "LIN-31-2", "linear_identifier": "LIN-31-2"})

    entered = threading.Event()
    original_update_list = storage.update_list

    def _slow_update_list(filename, mutator):
        def _slow_mutator(items):
            entered.set()
            time.sleep(0.2)
            return mutator(items)
        return original_update_list(filename, _slow_mutator)

    storage.update_list = _slow_update_list

    def _update_lin1():
        service.update_status("LIN-31-1", "running")

    thread = threading.Thread(target=_update_lin1)
    thread.start()
    entered.wait(timeout=2)
    service.update_status("LIN-31-2", "selected")  # concurrent update of a DIFFERENT link
    thread.join(timeout=2)

    lin1 = service.get_link_by_issue("LIN-31-1")
    lin2 = service.get_link_by_issue("LIN-31-2")
    assert lin1["status"] == "running"  # must not be lost -- failed before the fix
    assert lin2["status"] == "selected"  # must not be lost -- failed before the fix


def test_git_service_excludes_unsafe_files():
    service = GitService()
    assert service.is_safe_path("backend/app/main.py") is True
    assert service.is_safe_path("backend/.env") is False
    assert service.is_safe_path("backend/app/data/goals.json") is False
    assert service.is_safe_path("node_modules/react/index.js") is False


def test_git_commit_message_format():
    message = "Linear EVO-123: complete backend route for goal sync"
    assert message.startswith("Linear EVO-123:")


def test_secret_scanner_redacts_linear_key():
    scanner = SecretScanner()
    text = "Authorization: lin_api_abc123secretvalue"
    redacted, result = scanner.redact(text)
    assert result.secrets_detected is True
    assert "lin_api_" not in redacted


def test_linear_graphql_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "linear_api_key", None)
    service = LinearService()
    with pytest.raises(LinearServiceError, match="Linear is not configured"):
        service.linear_graphql("{ viewer { id } }")


def test_poll_worker_detects_in_progress_issues(monkeypatch):
    from app.services.linear_poll_worker import LinearPollWorker

    monkeypatch.setattr(settings, "linear_sync_enabled", True)
    monkeypatch.setattr(settings, "linear_api_key", "test-key")
    monkeypatch.setattr(settings, "linear_team_id", "team-1")

    linear = MagicMock()
    linear.list_in_progress_issues.return_value = [
        {"id": "issue-1", "identifier": "EVO-1", "status": "In Progress", "status_type": "started"},
    ]
    orchestration = MagicMock()
    orchestration.links.get_link_by_issue.return_value = None
    orchestration.prepare_in_progress_issue.return_value = {
        "branch": {"branch": "linear/evo-1"},
    }

    worker = LinearPollWorker(linear, orchestration)
    processed = worker.poll_once()

    assert len(processed) == 1
    assert processed[0]["identifier"] == "EVO-1"
    orchestration.prepare_in_progress_issue.assert_called_once_with("issue-1")


def test_poll_worker_skips_already_prepared(monkeypatch):
    from app.services.linear_poll_worker import LinearPollWorker

    monkeypatch.setattr(settings, "linear_sync_enabled", True)
    monkeypatch.setattr(settings, "linear_api_key", "test-key")
    monkeypatch.setattr(settings, "linear_team_id", "team-1")

    linear = MagicMock()
    linear.list_in_progress_issues.return_value = [
        {"id": "issue-1", "identifier": "EVO-1", "status": "In Progress", "status_type": "started"},
    ]
    orchestration = MagicMock()
    orchestration.links.get_link_by_issue.return_value = {
        "linear_status": "In Progress",
        "branch_name": "linear/evo-1",
    }

    worker = LinearPollWorker(linear, orchestration)
    processed = worker.poll_once()

    assert processed == []
    orchestration.prepare_in_progress_issue.assert_not_called()


def test_poll_worker_status_when_disabled(monkeypatch):
    from app.services.linear_poll_worker import LinearPollWorker

    monkeypatch.setattr(settings, "linear_sync_enabled", False)
    worker = LinearPollWorker(MagicMock(), MagicMock())
    status = worker.status()
    assert status["enabled"] is False
    assert status["running"] is False


def test_resolve_workflow_state_prefers_done_name():
    states = [
        {"id": "1", "name": "Backlog", "type": "backlog"},
        {"id": "2", "name": "In Progress", "type": "started"},
        {"id": "3", "name": "Done", "type": "completed"},
    ]
    target = LinearService.resolve_workflow_state(states, prefer_completed=True)
    assert target["name"] == "Done"


def test_resolve_workflow_state_falls_back_to_completed_type():
    states = [
        {"id": "1", "name": "Backlog", "type": "backlog"},
        {"id": "2", "name": "Shipped", "type": "completed"},
    ]
    target = LinearService.resolve_workflow_state(states, prefer_completed=True)
    assert target["type"] == "completed"


def test_build_completion_summary_includes_task_and_git(tmp_path, monkeypatch):
    from app.services.linear_orchestration_service import LinearOrchestrationService

    storage = StorageService(data_dir=str(tmp_path))
    linear = MagicMock()
    links = LinearLinkService(storage)
    goals = GoalService(storage)
    orchestration = LinearOrchestrationService(
        storage=storage,
        linear_service=linear,
        link_service=links,
        goal_service=goals,
        governance_service=MagicMock(),
        master_agent=MagicMock(),
        workspace_service=MagicMock(),
        git_service=MagicMock(),
    )
    orchestration.git.recent_commits.return_value = [{"hash": "abc1234", "message": "Fix poll worker"}]

    link = {
        "linear_issue_id": "issue-169",
        "linear_identifier": "EVO-169",
        "branch_name": "linear/evo-169",
        "commits": [{"hash": "def5678", "message": "Linear EVO-169: integration"}],
        "pushes": [],
        "task_id": "task-1",
    }
    tasks = [
        {
            "task_id": "task-1",
            "title": "v4.0 automation",
            "description": "Codebase automation assistant",
            "status": "done",
            "last_result_summary": "Added Linear poll fix and completion summary.",
        }
    ]

    summary = orchestration._build_completion_summary(
        link,
        tasks,
        marked_task=tasks[0],
        user_note="Verified locally with curl.",
    )

    assert "EVO-169" in summary
    assert "Added Linear poll fix" in summary
    assert "linear/evo-169" in summary
    assert "Verified locally with curl." in summary
    assert "def5678" in summary


def test_on_goal_task_updated_completes_linear_with_summary(tmp_path, monkeypatch):
    from app.services.linear_orchestration_service import LinearOrchestrationService

    storage = StorageService(data_dir=str(tmp_path))
    linear = MagicMock()
    linear.update_linear_issue_status.return_value = {"status": "Done"}
    linear.add_linear_comment.return_value = {"id": "comment-1"}

    links = LinearLinkService(storage)
    goals = GoalService(storage)
    goal, task_graph = goals.create_from_plan(
        {
            "goal_title": "Test goal",
            "goal_summary": "Summary",
            "tasks": [{"title": "Do work", "description": "Implement feature", "phase": "Execution"}],
        }
    )
    task_id = task_graph.tasks[0].task_id
    links.create_or_update_link(
        {
            "linear_issue_id": "issue-169",
            "linear_identifier": "EVO-169",
            "goal_id": goal.goal_id,
            "task_id": task_id,
            "branch_name": "linear/evo-169",
            "status": "selected",
        }
    )

    orchestration = LinearOrchestrationService(
        storage=storage,
        linear_service=linear,
        link_service=links,
        goal_service=goals,
        governance_service=MagicMock(),
        master_agent=MagicMock(),
        workspace_service=MagicMock(),
        git_service=MagicMock(),
    )
    orchestration.git.recent_commits.return_value = []

    goals.update_task(goal.goal_id, task_id, {"status": "done"})
    result = orchestration.on_goal_task_updated(
        goal.goal_id,
        task_id,
        {"status": "done"},
        completion_note="Shipped Linear auto-complete with summary notes.",
    )

    assert result is not None
    assert result["completed"] is True
    linear.update_linear_issue_status.assert_called_once()
    linear.add_linear_comment.assert_called_once()
    comment_body = linear.add_linear_comment.call_args[0][1]
    assert "Shipped Linear auto-complete" in comment_body
    assert "EVO-169" in comment_body


def test_sync_issue_updates_cached_linear_status(tmp_path):
    from app.services.linear_orchestration_service import LinearOrchestrationService

    storage = StorageService(data_dir=str(tmp_path))
    linear = MagicMock()
    linear.get_linear_issue.return_value = {
        "id": "issue-277",
        "identifier": "EVO-277",
        "title": "Research Agent",
        "description": "Add governed research workflow",
        "status": "Done",
        "url": "https://linear.app/EVO-277",
    }
    linear.map_issue_to_goal.return_value = {
        "goal_title": "Research Agent",
        "goal_summary": "Add governed research workflow",
        "tasks": [{"title": "Research Agent", "description": "Build it", "phase": "Execution"}],
    }

    links = LinearLinkService(storage)
    goals = GoalService(storage)
    goal, task_graph = goals.create_from_plan(linear.map_issue_to_goal.return_value)
    links.create_or_update_link(
        {
            "linear_issue_id": "issue-277",
            "linear_identifier": "EVO-277",
            "goal_id": goal.goal_id,
            "task_id": task_graph.tasks[0].task_id,
            "branch_name": "linear/evo-277",
            "status": "selected",
            "linear_status": "In Progress",
        }
    )

    workspace_service = MagicMock()
    workspace_service.resolve_workspace_id.return_value = "workspace-1"
    orchestration = LinearOrchestrationService(
        storage=storage,
        linear_service=linear,
        link_service=links,
        goal_service=goals,
        governance_service=MagicMock(),
        master_agent=MagicMock(),
        workspace_service=workspace_service,
        git_service=MagicMock(),
    )

    result = orchestration.sync_issue("issue-277")

    assert result["link"]["linear_status"] == "Done"
    assert links.get_link_by_issue("issue-277")["linear_status"] == "Done"


def test_cursor_handoff_builds_prompts_and_brief(tmp_path):
    from app.services.linear_cursor_handoff_service import LinearCursorHandoffService

    service = LinearCursorHandoffService(project_root=tmp_path)
    handoff = service.build_handoff(
        {
            "id": "issue-170",
            "identifier": "EVO-170",
            "title": "Linear integration bridge",
            "description": "Sync issues and branches",
            "url": "https://linear.app/EVO-170",
        },
        {"branch_name": "linear/evo-170", "task_id": "t1"},
        tasks=[{"task_id": "t1", "title": "Build bridge", "description": "Wire sync", "status": "pending"}],
    )

    assert "EVO-170" in handoff["cursor_prompt"]
    assert "linear/evo-170" in handoff["codex_prompt"]
    assert handoff["brief_path"]
    assert Path(handoff["brief_path"]).exists()


def test_verify_cursor_work_marks_done_when_tests_pass(tmp_path, monkeypatch):
    from app.services.linear_orchestration_service import LinearOrchestrationService

    storage = StorageService(data_dir=str(tmp_path))
    linear = MagicMock()
    linear.get_linear_issue.return_value = {
        "id": "issue-170",
        "identifier": "EVO-170",
        "title": "Bridge",
        "status": "In Progress",
    }
    linear.update_linear_issue_status.return_value = {"status": "Done"}
    linear.add_linear_comment.return_value = {"id": "c1"}

    links = LinearLinkService(storage)
    goals = GoalService(storage)
    goal, task_graph = goals.create_from_plan(
        {"goal_title": "G", "goal_summary": "S", "tasks": [{"title": "Task", "description": "D", "phase": "Execution"}]}
    )
    task_id = task_graph.tasks[0].task_id
    links.create_or_update_link(
        {
            "linear_issue_id": "issue-170",
            "linear_identifier": "EVO-170",
            "goal_id": goal.goal_id,
            "task_id": task_id,
            "branch_name": "linear/evo-170",
            "status": "selected",
        }
    )

    orchestration = LinearOrchestrationService(
        storage=storage,
        linear_service=linear,
        link_service=links,
        goal_service=goals,
        governance_service=MagicMock(),
        master_agent=MagicMock(),
        workspace_service=MagicMock(),
        git_service=MagicMock(),
        command_runner=MagicMock(),
    )
    orchestration.git.current_branch.return_value = "linear/evo-170"
    orchestration.git.git_status.return_value = {"clean": True, "output": "", "success": True}
    orchestration.git.push.return_value = {"skipped": True, "success": False}
    orchestration._run_verification_commands = MagicMock(
        return_value=[{"command": "pytest", "success": True}, {"command": "npm run build", "success": True}]
    )

    result = orchestration.verify_cursor_work("issue-170", completion_note="Implemented in Cursor.")

    assert result["verified"] is True
    assert result["linear_completion"]["completed"] is True
    linear.update_linear_issue_status.assert_called_once()
