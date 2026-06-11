from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.services.secret_scanner import SecretScanner

LINEAR_API_URL = "https://api.linear.app/graphql"
NOT_CONFIGURED = "Linear is not configured. Add LINEAR_API_KEY and LINEAR_TEAM_ID."


class LinearServiceError(Exception):
    pass


class LinearService:
    def __init__(self, secret_scanner: SecretScanner | None = None):
        self.secret_scanner = secret_scanner or SecretScanner()

    def get_linear_config(self) -> dict[str, Any]:
        return {
            "configured": settings.linear_configured,
            "sync_enabled": settings.linear_sync_enabled,
            "team_id_set": bool(settings.linear_team_id),
            "project_id_set": bool(settings.linear_project_id),
            "workspace_name": settings.linear_workspace_name,
            "auto_git_push": settings.auto_git_push,
            "poll_interval_seconds": settings.linear_poll_interval_seconds,
        }

    def linear_graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        if not settings.linear_api_key:
            raise LinearServiceError(NOT_CONFIGURED)
        headers = {
            "Authorization": settings.linear_api_key,
            "Content-Type": "application/json",
        }
        payload = {"query": query, "variables": variables or {}}
        try:
            response = httpx.post(LINEAR_API_URL, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPError as error:
            raise LinearServiceError(f"Linear API request failed: {error}") from error

        if body.get("errors"):
            message = body["errors"][0].get("message", "Linear GraphQL error")
            raise LinearServiceError(message)
        return body.get("data") or {}

    def list_linear_issues(self, status_filter: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        if not settings.linear_team_id:
            raise LinearServiceError(NOT_CONFIGURED)

        if settings.linear_project_id:
            query = """
            query TeamIssues($teamId: String!, $first: Int!, $projectId: ID!) {
              team(id: $teamId) {
                issues(first: $first, filter: { project: { id: { eq: $projectId } } }) {
                  nodes {
                    id identifier title description priority url updatedAt
                    state { name type }
                    assignee { name }
                  }
                }
              }
            }
            """
            variables = {
                "teamId": settings.linear_team_id,
                "first": limit,
                "projectId": settings.linear_project_id,
            }
        else:
            query = """
            query TeamIssues($teamId: String!, $first: Int!) {
              team(id: $teamId) {
                issues(first: $first) {
                  nodes {
                    id identifier title description priority url updatedAt
                    state { name type }
                    assignee { name }
                  }
                }
              }
            }
            """
            variables = {"teamId": settings.linear_team_id, "first": limit}

        data = self.linear_graphql(query, variables)
        team = data.get("team") or {}
        issues = [self._normalize_issue(item) for item in team.get("issues", {}).get("nodes", [])]
        if status_filter:
            issues = [item for item in issues if (item.get("status") or "").lower() == status_filter.lower()]
        return issues

    def list_in_progress_issues(self, limit: int = 50) -> list[dict[str, Any]]:
        """Fetch issues in started workflow states (In Progress) for the poll worker."""
        if not settings.linear_team_id:
            raise LinearServiceError(NOT_CONFIGURED)

        if settings.linear_project_id:
            query = """
            query TeamIssues($teamId: String!, $first: Int!, $projectId: ID!) {
              team(id: $teamId) {
                issues(
                  first: $first,
                  filter: {
                    project: { id: { eq: $projectId } },
                    state: { type: { eq: "started" } }
                  }
                ) {
                  nodes {
                    id identifier title description priority url updatedAt
                    state { name type }
                    assignee { name }
                  }
                }
              }
            }
            """
            variables = {
                "teamId": settings.linear_team_id,
                "first": limit,
                "projectId": settings.linear_project_id,
            }
        else:
            query = """
            query TeamIssues($teamId: String!, $first: Int!) {
              team(id: $teamId) {
                issues(first: $first, filter: { state: { type: { eq: "started" } } }) {
                  nodes {
                    id identifier title description priority url updatedAt
                    state { name type }
                    assignee { name }
                  }
                }
              }
            }
            """
            variables = {"teamId": settings.linear_team_id, "first": limit}

        data = self.linear_graphql(query, variables)
        team = data.get("team") or {}
        return [self._normalize_issue(item) for item in team.get("issues", {}).get("nodes", [])]

    def get_linear_issue(self, issue_id: str) -> dict[str, Any]:
        query = """
        query Issue($id: String!) {
          issue(id: $id) {
            id
            identifier
            title
            description
            priority
            url
            updatedAt
            state { name type }
            assignee { name }
          }
        }
        """
        data = self.linear_graphql(query, {"id": issue_id})
        issue = data.get("issue")
        if not issue:
            raise LinearServiceError("Linear issue not found")
        return self._normalize_issue(issue)

    def add_linear_comment(self, issue_id: str, body: str) -> dict[str, Any]:
        safe_body, _ = self.secret_scanner.redact(body)
        mutation = """
        mutation CommentCreate($issueId: String!, $body: String!) {
          commentCreate(input: { issueId: $issueId, body: $body }) {
            success
            comment { id body createdAt }
          }
        }
        """
        data = self.linear_graphql(mutation, {"issueId": issue_id, "body": safe_body})
        result = data.get("commentCreate") or {}
        if not result.get("success"):
            raise LinearServiceError("Failed to create Linear comment")
        return result.get("comment") or {}

    COMPLETED_STATE_NAMES = ("done", "completed", "complete")

    @classmethod
    def resolve_workflow_state(
        cls,
        states: list[dict[str, Any]],
        status_name: str | None = None,
        *,
        prefer_completed: bool = False,
    ) -> dict[str, Any] | None:
        if status_name:
            target = next((item for item in states if item.get("name", "").lower() == status_name.lower()), None)
            if target is not None:
                return target
        if prefer_completed:
            for name in cls.COMPLETED_STATE_NAMES:
                target = next((item for item in states if item.get("name", "").lower() == name), None)
                if target is not None:
                    return target
            return next((item for item in states if item.get("type") == "completed"), None)
        return None

    def update_linear_issue_status(
        self,
        issue_id: str,
        status_name: str | None = None,
        *,
        prefer_completed: bool = False,
    ) -> dict[str, Any]:
        states_query = """
        query IssueTeamStates($issueId: String!) {
          issue(id: $issueId) {
            team {
              states { nodes { id name type } }
            }
          }
        }
        """
        state_data = self.linear_graphql(states_query, {"issueId": issue_id})
        states = (
            ((state_data.get("issue") or {}).get("team") or {}).get("states") or {}
        ).get("nodes", [])
        target = self.resolve_workflow_state(
            states,
            status_name,
            prefer_completed=prefer_completed or status_name is None,
        )
        if target is None:
            label = status_name or "completed"
            raise LinearServiceError(f"Linear workflow state '{label}' not found")

        mutation = """
        mutation IssueUpdate($issueId: String!, $stateId: String!) {
          issueUpdate(id: $issueId, input: { stateId: $stateId }) {
            success
            issue { id identifier state { name } }
          }
        }
        """
        data = self.linear_graphql(mutation, {"issueId": issue_id, "stateId": target["id"]})
        result = data.get("issueUpdate") or {}
        if not result.get("success"):
            raise LinearServiceError("Failed to update Linear issue status")
        return self._normalize_issue(result.get("issue") or {})

    def map_issue_to_goal(self, issue: dict[str, Any]) -> dict[str, Any]:
        description = issue.get("description") or issue.get("title") or "Linear issue"
        return {
            "goal_title": issue.get("title") or issue.get("identifier") or "Linear Issue",
            "goal_summary": description[:500],
            "tags": [f"linear:{issue.get('identifier')}", "linear-sync"],
            "risk_level": "medium" if issue.get("priority", 0) >= 2 else "low",
            "recommended_agents": ["Strategy Agent", "Writing Agent"],
            "next_best_task": issue.get("title") or "Review Linear issue",
            "tasks": self.map_issue_to_tasks(issue),
        }

    def map_issue_to_tasks(self, issue: dict[str, Any]) -> list[dict[str, Any]]:
        """One Mission Control task per Linear issue so Mark done auto-closes Linear."""
        return [
            {
                "title": issue.get("title") or "Complete Linear issue",
                "description": issue.get("description") or "",
                "phase": "Execution",
                "priority": "high" if issue.get("priority", 0) >= 2 else "medium",
                "depends_on": [],
                "recommended_agent": "Strategy Agent",
                "estimated_effort": "medium",
                "requires_approval": False,
                "automation_supported": True,
            }
        ]

    def map_issue_to_task(self, issue: dict[str, Any]) -> dict[str, Any]:
        tasks = self.map_issue_to_tasks(issue)
        return tasks[0]

    @staticmethod
    def _normalize_issue(issue: dict[str, Any]) -> dict[str, Any]:
        state = issue.get("state") or {}
        assignee = issue.get("assignee") or {}
        return {
            "id": issue.get("id"),
            "identifier": issue.get("identifier"),
            "title": issue.get("title"),
            "description": issue.get("description"),
            "status": state.get("name"),
            "status_type": state.get("type"),
            "assignee": assignee.get("name"),
            "priority": issue.get("priority"),
            "url": issue.get("url"),
            "updatedAt": issue.get("updatedAt"),
        }
