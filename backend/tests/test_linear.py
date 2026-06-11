from unittest.mock import MagicMock

import pytest

from app.config import settings
from app.services.git_service import GitService
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
    linear.list_linear_issues.return_value = [
        {"id": "issue-1", "identifier": "EVO-1", "status": "In Progress", "status_type": "started"},
        {"id": "issue-2", "identifier": "EVO-2", "status": "Backlog", "status_type": "backlog"},
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
    linear.list_linear_issues.return_value = [
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
