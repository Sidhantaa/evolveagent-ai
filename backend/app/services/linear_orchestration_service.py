from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.agents.master_agent import MasterOrchestratorAgent
from app.config import settings
from app.models.request_models import RunRequest
from app.models.response_models import GovernanceEvent
from app.services.git_service import GitService
from app.services.goal_service import GoalService
from app.services.governance_service import GovernanceService
from app.services.linear_link_service import LinearLinkService
from app.services.linear_service import LinearService, LinearServiceError
from app.services.safe_command_runner import SafeCommandRunner
from app.services.storage_service import StorageService
from app.services.workspace_service import WorkspaceService


class LinearOrchestrationService:
    def __init__(
        self,
        storage: StorageService,
        linear_service: LinearService,
        link_service: LinearLinkService,
        goal_service: GoalService,
        governance_service: GovernanceService,
        master_agent: MasterOrchestratorAgent,
        workspace_service: WorkspaceService,
        git_service: GitService | None = None,
        command_runner: SafeCommandRunner | None = None,
    ):
        self.storage = storage
        self.linear = linear_service
        self.links = link_service
        self.goals = goal_service
        self.governance = governance_service
        self.master_agent = master_agent
        self.workspace_service = workspace_service
        self.git = git_service or GitService()
        self.command_runner = command_runner or SafeCommandRunner()

    def _log(self, action_type: str, reason: str, **kwargs: Any) -> None:
        self.governance.log_event(
            GovernanceEvent(
                agent_name="Linear Integration",
                action_type=action_type,
                tool_used="LinearOrchestrationService",
                permission_level="plan_only",
                approved=False,
                blocked=False,
                reason=reason,
                **kwargs,
            )
        )

    def sync_issue(self, issue_id: str, workspace_id: str | None = None) -> dict[str, Any]:
        resolved_workspace = self.workspace_service.resolve_workspace_id(workspace_id)
        issue = self.linear.get_linear_issue(issue_id)
        self._log("linear_issue_fetched", f"Fetched Linear issue {issue.get('identifier')}", workspace_id=resolved_workspace)

        planner = self.linear.map_issue_to_goal(issue)
        existing = self.links.get_link_by_issue(issue_id)
        if existing and existing.get("goal_id"):
            goal_record = self.goals.get_goal(existing["goal_id"])
            if goal_record:
                goal, task_graph = goal_record
                link = self.links.create_or_update_link(
                    {
                        **existing,
                        "linear_identifier": issue.get("identifier"),
                        "linear_url": issue.get("url"),
                        "workspace_id": resolved_workspace,
                        "status": "synced",
                    }
                )
                self._log("linear_issue_synced", f"Updated sync for {issue.get('identifier')}", workspace_id=resolved_workspace)
                return {"issue": issue, "goal": goal, "task_graph": task_graph, "link": link}

        goal, task_graph = self.goals.create_from_plan(
            planner,
            tags=planner.get("tags"),
            workspace_id=resolved_workspace,
        )
        first_task = (task_graph.tasks[0].model_dump() if task_graph.tasks else None)
        branch_name = f"linear/{issue.get('identifier', issue_id).lower()}"
        link = self.links.create_or_update_link(
            {
                "linear_issue_id": issue_id,
                "linear_identifier": issue.get("identifier"),
                "linear_url": issue.get("url"),
                "goal_id": goal.goal_id,
                "task_id": first_task.get("task_id") if first_task else None,
                "workspace_id": resolved_workspace,
                "status": "synced",
                "branch_name": branch_name,
            }
        )
        self._log("linear_issue_synced", f"Synced {issue.get('identifier')} to Mission Control", workspace_id=resolved_workspace)
        return {
            "issue": issue,
            "goal": goal.model_dump(),
            "task_graph": task_graph.model_dump(),
            "link": link,
        }

    def select_issue(self, issue_id: str, workspace_id: str | None = None) -> dict[str, Any]:
        sync_result = self.sync_issue(issue_id, workspace_id=workspace_id)
        link = self.links.update_status(issue_id, "selected", note="Selected for backend work")
        self._log("linear_issue_selected", f"Selected {sync_result['issue'].get('identifier')} for work")
        return {**sync_result, "link": link or sync_result.get("link")}

    def prepare_in_progress_issue(self, issue_id: str, workspace_id: str | None = None) -> dict[str, Any]:
        """Detect In Progress in Linear: sync, select, create branch, notify Linear. No agent run."""
        select_result = self.select_issue(issue_id, workspace_id=workspace_id)
        link = select_result.get("link") or {}
        issue = select_result.get("issue") or {}
        branch_name = link.get("branch_name") or f"linear/{(issue.get('identifier') or issue_id).lower()}"
        branch_result = self.git.create_branch(branch_name)
        if branch_result["success"]:
            link = self.links.create_or_update_link(
                {
                    **link,
                    "branch_name": branch_result["branch"],
                    "linear_status": issue.get("status"),
                    "last_run_at": datetime.now(UTC).isoformat(),
                }
            )
        self.links.update_status(issue_id, "selected", note="Detected In Progress via Linear poll")
        self._log(
            "linear_in_progress_detected",
            f"Prepared branch for {issue.get('identifier')}",
            workspace_id=link.get("workspace_id"),
        )
        comment_body = (
            f"**EvolveAgent detected In Progress**\n\n"
            f"- Mission Control goal synced\n"
            f"- Local branch: `{branch_result.get('branch', branch_name)}`\n"
            f"- Ready for Cursor/Codex work on this issue\n\n"
            f"Run `/api/linear/issues/{issue_id}/run` when a subtask is ready for agent verification, tests, commit, and push."
        )
        try:
            comment = self.linear.add_linear_comment(issue_id, comment_body)
        except LinearServiceError:
            comment = {}
        return {
            **select_result,
            "link": link,
            "branch": branch_result,
            "linear_comment": comment,
            "prepared_for_cursor": True,
        }

    def run_issue(self, issue_id: str, workspace_id: str | None = None) -> dict[str, Any]:
        resolved_workspace = self.workspace_service.resolve_workspace_id(workspace_id)
        select_result = self.select_issue(issue_id, workspace_id=resolved_workspace)
        link = select_result["link"]
        goal_id = link.get("goal_id")
        if not goal_id:
            raise LinearServiceError("Linear issue is not linked to a goal")

        self.links.update_status(issue_id, "running")
        self._log("linear_issue_run_started", f"Started run for {link.get('linear_identifier')}", workspace_id=resolved_workspace)

        branch_name = link.get("branch_name") or f"linear/{link.get('linear_identifier', issue_id).lower()}"
        branch_result = self.git.create_branch(branch_name)
        if branch_result["success"]:
            link = self.links.create_or_update_link({**link, "branch_name": branch_result["branch"]})

        goal_record, graph = self.goals.get_goal(goal_id) or ({}, {"tasks": []})
        next_task = self._next_pending_task(graph.get("tasks", []))
        if next_task is None:
            completion = self.complete_linear_issue(issue_id, goal_id=goal_id)
            return {**select_result, "run": None, "message": "No pending subtasks", "linear_completion": completion}

        self.goals.update_task(goal_id, next_task["task_id"], {"status": "running"})
        request = RunRequest(
            user_input=f"{next_task.get('title')}\n\n{next_task.get('description', '')}".strip(),
            task_type="auto",
            workspace_id=goal_record.get("workspace_id") or resolved_workspace,
            goal_id=goal_id,
            task_id=next_task["task_id"],
        )
        response = self.master_agent.run(request)
        final_status = "needs_approval" if response.requires_approval else "done"
        self.goals.update_task(
            goal_id,
            next_task["task_id"],
            {
                "status": final_status,
                "last_run_id": response.run_id,
                "last_result_summary": response.final_output[:240],
            },
        )

        test_results = self._run_verification_commands()
        git_stage = self.git.add_safe_files()
        if git_stage.get("excluded_files"):
            self._log(
                "unsafe_file_excluded_from_commit",
                f"Excluded unsafe files: {', '.join(git_stage['excluded_files'][:5])}",
            )

        identifier = link.get("linear_identifier") or issue_id
        commit_message = f"Linear {identifier}: {next_task.get('title')}"
        commit_result = {"success": False, "commit_hash": "", "message": "No safe changes to commit"}
        if git_stage.get("staged_files"):
            commit_result = self.git.commit(commit_message)
            if commit_result.get("success"):
                self._log("git_commit_created", f"Created commit for {identifier}")
                self.links.append_commit(
                    issue_id,
                    {
                        "hash": commit_result.get("commit_hash"),
                        "message": commit_message,
                        "at": datetime.now(UTC).isoformat(),
                        "subtask": next_task.get("title"),
                    },
                )

        push_result = self.git.push()
        if push_result.get("skipped"):
            pass
        elif push_result.get("success"):
            self._log("git_push_completed", f"Pushed branch for {identifier}")
            self.links.append_push(
                issue_id,
                {"at": datetime.now(UTC).isoformat(), "branch": push_result.get("branch"), "remote": push_result.get("remote")},
            )
        else:
            self._log("git_push_failed", push_result.get("message", "Push failed"))

        comment_body = self._build_comment(
            subtask=next_task,
            response_summary=response.final_output[:500],
            test_results=test_results,
            commit_result=commit_result,
            push_result=push_result,
            next_task=self._next_pending_task(
                (self.goals.get_goal(goal_id) or ({}, {"tasks": []}))[1].get("tasks", [])
            ),
        )
        comment = {}
        try:
            comment = self.linear.add_linear_comment(issue_id, comment_body)
            self._log("linear_comment_created", f"Updated Linear issue {identifier}")
        except LinearServiceError as error:
            self._log("linear_comment_failed", str(error))

        updated_tasks = (self.goals.get_goal(goal_id) or ({}, {"tasks": []}))[1].get("tasks", [])
        all_complete = self._all_tasks_complete(updated_tasks)
        status = "completed" if all_complete else "selected"
        self.links.update_status(issue_id, status, note=f"Completed subtask: {next_task.get('title')}")

        linear_completion = None
        if all_complete:
            linear_completion = self.complete_linear_issue(issue_id, goal_id=goal_id)

        self.storage.append(
            "agent_analytics.json",
            {
                "run_id": response.run_id,
                "workspace_id": response.workspace_id,
                "task_type": "linear_task",
                "linear_issue_id": issue_id,
                "linear_identifier": identifier,
                "goal_id": goal_id,
                "goal_task_id": next_task["task_id"],
                "overall_judge_score": response.judge_result.overall_score if response.judge_result else 0,
                "per_agent_scores": [score.model_dump() for score in (response.judge_result.per_agent_scores or [])] if response.judge_result else [],
                "agents_used": response.agents_used,
                "latency_ms": response.latency_ms,
                "created_at": datetime.now(UTC).isoformat(),
            },
        )

        return {
            **select_result,
            "run": response.model_dump(),
            "subtask": next_task,
            "verification": test_results,
            "git": {
                "branch": self.git.current_branch(),
                "stage": git_stage,
                "commit": commit_result,
                "push": push_result,
                "status": self.git.git_status(),
            },
            "linear_comment": comment,
            "linear_completion": linear_completion,
        }

    def complete_linear_issue(
        self,
        issue_id: str,
        goal_id: str | None = None,
        *,
        skip_task_check: bool = False,
    ) -> dict[str, Any]:
        link = self.links.get_link_by_issue(issue_id)
        if link is None and goal_id:
            link = self.links.get_link_by_goal_task(goal_id)
        if link is None:
            raise LinearServiceError("Linear issue link not found")

        resolved_goal_id = goal_id or link.get("goal_id")
        if resolved_goal_id and not skip_task_check:
            _, graph = self.goals.get_goal(resolved_goal_id) or ({}, {"tasks": []})
            if graph.get("tasks") and not self._all_tasks_complete(graph.get("tasks", [])):
                return {"completed": False, "reason": "Goal tasks are not all done yet"}

        identifier = link.get("linear_identifier") or issue_id
        if link.get("status") == "completed" and link.get("linear_status", "").lower() in {"done", "completed", "complete"}:
            return {"completed": True, "already_completed": True, "identifier": identifier}

        status_update: dict[str, Any] = {}
        try:
            status_update = self.linear.update_linear_issue_status(issue_id, prefer_completed=True)
            self._log("linear_status_updated", f"Marked {identifier} as Done in Linear")
        except LinearServiceError as error:
            self._log("linear_status_update_failed", str(error))

        commits = link.get("commits") or []
        latest_commit = commits[-1]["hash"] if commits else "none"
        pushes = link.get("pushes") or []
        comment_body = (
            f"**EvolveAgent task completed**\n\n"
            f"- Issue: `{identifier}`\n"
            f"- All Mission Control subtasks are done\n"
            f"- Branch: `{link.get('branch_name') or 'n/a'}`\n"
            f"- Latest commit: `{latest_commit}`\n"
            f"- Push status: {'completed' if pushes else 'not pushed yet'}\n"
        )
        if status_update.get("status"):
            comment_body += f"- Linear status: **{status_update['status']}**\n"

        comment: dict[str, Any] = {}
        try:
            comment = self.linear.add_linear_comment(issue_id, comment_body)
            self._log("linear_comment_created", f"Posted completion comment for {identifier}")
        except LinearServiceError as error:
            self._log("linear_comment_failed", str(error))

        updated_link = self.links.create_or_update_link(
            {
                **link,
                "status": "completed",
                "linear_status": status_update.get("status") or "Done",
                "last_run_at": datetime.now(UTC).isoformat(),
            }
        )
        self._log("linear_issue_completed", f"Completed Linear issue {identifier}")

        return {
            "completed": True,
            "identifier": identifier,
            "linear_status": status_update,
            "linear_comment": comment,
            "link": updated_link,
        }

    def on_goal_task_updated(self, goal_id: str, task_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        if updates.get("status") not in {"done", "completed"}:
            return None
        link = self.links.get_link_by_goal_task(goal_id, task_id)
        if link is None:
            link = self.links.get_link_by_goal_task(goal_id)
        if link is None:
            return None

        issue_id = link["linear_issue_id"]
        _, graph = self.goals.get_goal(goal_id) or ({}, {"tasks": []})
        tasks = graph.get("tasks", [])
        marked_task = next((task for task in tasks if task.get("task_id") == task_id), None)

        if self._all_tasks_complete(tasks):
            return self.complete_linear_issue(issue_id, goal_id=goal_id)

        if link.get("task_id") == task_id:
            return self.complete_linear_issue(issue_id, goal_id=goal_id, skip_task_check=True)

        if marked_task:
            remaining = [task.get("title") for task in tasks if task.get("status") not in {"done", "completed"}]
            comment_body = (
                f"**EvolveAgent subtask completed:** {marked_task.get('title')}\n\n"
                f"Remaining Mission Control subtasks: {len(remaining)}\n"
            )
            if remaining:
                comment_body += "\n".join(f"- {title}" for title in remaining[:5])
            try:
                comment = self.linear.add_linear_comment(issue_id, comment_body)
                self._log("linear_comment_created", f"Posted subtask progress for {link.get('linear_identifier')}")
                return {"completed": False, "progress_comment": comment}
            except LinearServiceError as error:
                self._log("linear_comment_failed", str(error))
        return None

    def sync_pending_completions(self) -> list[dict[str, Any]]:
        """Auto-close Linear issues when linked goals are fully done."""
        synced: list[dict[str, Any]] = []
        for link in self.links.list_links():
            if link.get("status") == "completed":
                continue
            goal_id = link.get("goal_id")
            issue_id = link.get("linear_issue_id")
            if not goal_id or not issue_id:
                continue
            _, graph = self.goals.get_goal(goal_id) or ({}, {"tasks": []})
            tasks = graph.get("tasks", [])
            if not tasks:
                continue
            if not self._all_tasks_complete(tasks):
                linked_task = next((task for task in tasks if task.get("task_id") == link.get("task_id")), None)
                if not linked_task or linked_task.get("status") not in {"done", "completed"}:
                    continue
                result = self.complete_linear_issue(issue_id, goal_id=goal_id, skip_task_check=True)
            else:
                result = self.complete_linear_issue(issue_id, goal_id=goal_id)
            if result.get("completed"):
                synced.append(
                    {
                        "issue_id": issue_id,
                        "identifier": link.get("linear_identifier"),
                        "action": "completed",
                    }
                )
        return synced

    def add_comment(self, issue_id: str, body: str) -> dict[str, Any]:
        comment = self.linear.add_linear_comment(issue_id, body)
        self._log("linear_comment_created", f"Manual comment added to {issue_id}")
        return comment

    @staticmethod
    def _next_pending_task(tasks: list[dict[str, Any]]) -> dict[str, Any] | None:
        for task in tasks:
            if task.get("status") in {None, "pending", "blocked"}:
                return task
        return None

    @staticmethod
    def _all_tasks_complete(tasks: list[dict[str, Any]]) -> bool:
        if not tasks:
            return False
        return all(task.get("status") in {"done", "completed"} for task in tasks)

    def _run_verification_commands(self) -> list[dict[str, Any]]:
        results = []
        for command in ("pytest", "npm run build"):
            result = self.command_runner.run(command)
            results.append(
                {
                    "command": command,
                    "success": result.success,
                    "exit_code": result.exit_code,
                    "stdout_tail": result.stdout[-500:],
                    "stderr_tail": result.stderr[-500:],
                }
            )
        return results

    @staticmethod
    def _build_comment(
        subtask: dict[str, Any],
        response_summary: str,
        test_results: list[dict[str, Any]],
        commit_result: dict[str, Any],
        push_result: dict[str, Any],
        next_task: dict[str, Any] | None,
    ) -> str:
        lines = [
            f"**EvolveAgent subtask completed:** {subtask.get('title')}",
            "",
            response_summary,
            "",
            "**Verification**",
        ]
        for item in test_results:
            status = "passed" if item["success"] else "failed"
            lines.append(f"- `{item['command']}`: {status}")
        lines.extend(
            [
                "",
                "**Git**",
                f"- Commit: `{commit_result.get('commit_hash') or 'none'}`",
                f"- Push: {'skipped (AUTO_GIT_PUSH=false)' if push_result.get('skipped') else ('ok' if push_result.get('success') else 'failed')}",
            ]
        )
        if next_task:
            lines.extend(["", f"**Next subtask:** {next_task.get('title')}"])
        return "\n".join(lines)
