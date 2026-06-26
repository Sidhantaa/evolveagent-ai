from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.permission_service import PermissionService
from app.services.storage_service import StorageService


class AutopilotService:
    runs_file = "autopilot_runs.json"
    actions_file = "autopilot_actions.json"
    settings_file = "autopilot_settings.json"
    checkpoints_file = "autopilot_checkpoints.json"

    def __init__(
        self,
        storage: StorageService,
        permissions: PermissionService,
        governance: GovernanceService,
    ):
        self.storage = storage
        self.permissions = permissions
        self.governance = governance

    def get_settings(self) -> dict[str, Any]:
        settings = self.storage.read_list(self.settings_file)
        if settings:
            return settings[-1]
        default = {
            "settings_id": "default",
            "kill_switch_enabled": False,
            "permission_mode": "supervised",
            "default_permission_level": "plan_only",
            "updated_at": self._now(),
            "notes": "Supervised autopilot is enabled with approval gates for risky actions.",
        }
        self.storage.write_list(self.settings_file, [default])
        return default

    def update_settings(self, updates: dict[str, Any]) -> dict[str, Any]:
        current = self.get_settings()
        allowed_keys = {"kill_switch_enabled", "permission_mode", "default_permission_level", "notes"}
        next_settings = {
            **current,
            **{key: value for key, value in updates.items() if key in allowed_keys and value is not None},
            "updated_at": self._now(),
        }
        self.storage.write_list(self.settings_file, [next_settings])
        self.governance.log_event(
            GovernanceEvent(
                workspace_id=None,
                task_type="autopilot",
                agent_name="Autopilot Service",
                action_type="autopilot_settings_updated",
                tool_used="AutopilotService",
                permission_level="plan_only",
                approved=True,
                blocked=False,
                risk_score=15,
                reason="Autopilot settings were updated.",
            )
        )
        return next_settings

    def create_run(
        self,
        *,
        prompt: str,
        workspace_id: str | None = None,
        mode: str = "supervised",
        actions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        now = self._now()
        run_id = str(uuid4())
        planned_actions = actions or self._infer_actions(prompt)
        settings = self.get_settings()
        run = {
            "run_id": run_id,
            "workspace_id": workspace_id,
            "prompt": prompt,
            "mode": mode,
            "status": "planned",
            "kill_switch_active": bool(settings.get("kill_switch_enabled")),
            "actions_count": 0,
            "pending_checkpoints_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        runs = self.storage.read_list(self.runs_file)
        runs.append(run)
        self.storage.write_list(self.runs_file, runs)

        created_actions = [self._create_action(run_id, workspace_id, action) for action in planned_actions[:12]]
        pending = [item for item in created_actions if item.get("status") == "waiting_approval"]
        run["actions_count"] = len(created_actions)
        run["pending_checkpoints_count"] = len(pending)
        run["status"] = "waiting_approval" if pending else "planned"
        self._replace_run(run)
        self.governance.log_event(
            GovernanceEvent(
                run_id=run_id,
                workspace_id=workspace_id,
                task_type="autopilot",
                agent_name="Autopilot Service",
                action_type="autopilot_run_created",
                tool_used="AutopilotService",
                permission_level="plan_only",
                approved=True,
                blocked=False,
                risk_score=max((self._risk_score(item.get("risk_level", "low")) for item in created_actions), default=10),
                reason=f"Created supervised autopilot run with {len(created_actions)} action(s).",
            )
        )
        return {**run, "actions": created_actions}

    def list_runs(self, workspace_id: str | None = None) -> list[dict[str, Any]]:
        runs = self.storage.read_list(self.runs_file)
        if workspace_id:
            runs = [item for item in runs if item.get("workspace_id") == workspace_id]
        return sorted(runs, key=lambda item: item.get("updated_at", ""), reverse=True)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        run = next((item for item in self.storage.read_list(self.runs_file) if item.get("run_id") == run_id), None)
        if not run:
            return None
        return {
            **run,
            "actions": self.list_actions(run_id=run_id),
            "checkpoints": self.list_checkpoints(run_id=run_id),
        }

    def start_run(self, run_id: str, reason: str | None = None) -> dict[str, Any]:
        run = self.get_run(run_id)
        if not run:
            raise ValueError("Autopilot run not found.")
        if self.get_settings().get("kill_switch_enabled"):
            blocked = self._update_run_status(run_id, "blocked")
            self._update_actions_for_run(run_id, "blocked", only_unfinished=True)
            self.governance.log_event(
                GovernanceEvent(
                    run_id=run_id,
                    workspace_id=run.get("workspace_id"),
                    task_type="autopilot",
                    agent_name="Autopilot Service",
                    action_type="autopilot_blocked_by_kill_switch",
                    tool_used="AutopilotService",
                    permission_level="blocked",
                    approved=False,
                    blocked=True,
                    risk_score=75,
                    reason=reason or "Autopilot kill switch is enabled.",
                )
            )
            return blocked

        actions = self.list_actions(run_id=run_id)
        if any(action.get("status") == "waiting_approval" for action in actions):
            return self._update_run_status(run_id, "waiting_approval")
        for action in actions:
            if action.get("status") in {"planned", "approved"}:
                self._replace_action({**action, "status": "completed", "updated_at": self._now()})
        return self._update_run_status(run_id, "completed")

    def stop_run(self, run_id: str, reason: str | None = None) -> dict[str, Any]:
        run = self.get_run(run_id)
        if not run:
            raise ValueError("Autopilot run not found.")
        stopped = self._update_run_status(run_id, "stopped")
        self._update_actions_for_run(run_id, "blocked", only_unfinished=True)
        self.governance.log_event(
            GovernanceEvent(
                run_id=run_id,
                workspace_id=run.get("workspace_id"),
                task_type="autopilot",
                agent_name="Autopilot Service",
                action_type="autopilot_stopped",
                tool_used="AutopilotService",
                permission_level="plan_only",
                approved=False,
                blocked=True,
                risk_score=40,
                reason=reason or "Autopilot run was manually stopped.",
            )
        )
        return stopped

    def list_actions(
        self,
        *,
        run_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        actions = self.storage.read_list(self.actions_file)
        if run_id:
            actions = [item for item in actions if item.get("run_id") == run_id]
        if workspace_id:
            actions = [item for item in actions if item.get("workspace_id") == workspace_id]
        if status:
            actions = [item for item in actions if item.get("status") == status]
        return sorted(actions, key=lambda item: item.get("updated_at", ""), reverse=True)

    def list_checkpoints(
        self,
        *,
        run_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        checkpoints = self.storage.read_list(self.checkpoints_file)
        if run_id:
            checkpoints = [item for item in checkpoints if item.get("run_id") == run_id]
        if workspace_id:
            checkpoints = [item for item in checkpoints if item.get("workspace_id") == workspace_id]
        if status:
            checkpoints = [item for item in checkpoints if item.get("status") == status]
        return sorted(checkpoints, key=lambda item: item.get("updated_at", ""), reverse=True)

    def decide_checkpoint(self, checkpoint_id: str, decision: str, comment: str | None = None) -> dict[str, Any]:
        checkpoints = self.storage.read_list(self.checkpoints_file)
        checkpoint = next((item for item in checkpoints if item.get("checkpoint_id") == checkpoint_id), None)
        if not checkpoint:
            raise ValueError("Autopilot checkpoint not found.")
        if checkpoint.get("status") != "pending":
            return checkpoint
        if decision not in {"approve", "reject"}:
            raise ValueError("Decision must be approve or reject.")

        now = self._now()
        checkpoint["status"] = "approved" if decision == "approve" else "rejected"
        checkpoint["decision"] = decision
        checkpoint["comment"] = comment
        checkpoint["updated_at"] = now
        self.storage.write_list(self.checkpoints_file, checkpoints)

        action = self._get_action(checkpoint.get("action_id"))
        if action:
            action["status"] = "approved" if decision == "approve" else "rejected"
            action["updated_at"] = now
            self._replace_action(action)

        self.governance.log_event(
            GovernanceEvent(
                run_id=checkpoint.get("run_id"),
                workspace_id=checkpoint.get("workspace_id"),
                task_type="autopilot",
                agent_name="Autopilot Service",
                action_type="autopilot_checkpoint_decision",
                tool_used="AutopilotService",
                permission_level=checkpoint.get("permission_level", "approve_to_edit"),
                approved=decision == "approve",
                blocked=decision != "approve",
                risk_score=self._risk_score(checkpoint.get("risk_level", "medium")),
                reason=comment or f"Autopilot checkpoint {decision}d.",
            )
        )
        self._refresh_run_counts(checkpoint.get("run_id"))
        return checkpoint

    def summary(self, workspace_id: str | None = None) -> dict[str, Any]:
        runs = self.list_runs(workspace_id=workspace_id)
        actions = self.list_actions(workspace_id=workspace_id)
        checkpoints = self.list_checkpoints(workspace_id=workspace_id)
        return {
            "autopilot_runs": len(runs),
            "autopilot_actions": len(actions),
            "autopilot_pending_checkpoints": sum(1 for item in checkpoints if item.get("status") == "pending"),
            "autopilot_blocked_actions": sum(1 for item in actions if item.get("status") == "blocked"),
            "autopilot_kill_switch_enabled": bool(self.get_settings().get("kill_switch_enabled")),
        }

    def _create_action(self, run_id: str, workspace_id: str | None, action: dict[str, Any]) -> dict[str, Any]:
        now = self._now()
        action_type = str(action.get("action_type", "plan")).strip()
        files = [str(path) for path in action.get("files_targeted", [])]
        command = action.get("command_requested")
        permission = self._classify_permission(action_type, files, command)
        status = "blocked" if permission == "blocked" else "planned"
        approval_required = permission in {"approve_to_edit", "approve_to_run"}
        if approval_required:
            status = "waiting_approval"

        record = {
            "action_id": str(uuid4()),
            "run_id": run_id,
            "workspace_id": workspace_id,
            "action_type": action_type,
            "summary": str(action.get("summary") or action_type),
            "permission_level": permission,
            "status": status,
            "files_targeted": files,
            "command_requested": command,
            "risk_level": action.get("risk_level", "medium"),
            "approval_required": approval_required,
            "created_at": now,
            "updated_at": now,
        }
        actions = self.storage.read_list(self.actions_file)
        actions.append(record)
        self.storage.write_list(self.actions_file, actions)
        if approval_required:
            self._create_checkpoint(record)
        self.governance.log_event(
            GovernanceEvent(
                run_id=run_id,
                workspace_id=workspace_id,
                task_type="autopilot",
                agent_name="Autopilot Service",
                action_type="autopilot_action_planned",
                tool_used="AutopilotService",
                files_accessed=files,
                command_requested=command,
                permission_level=permission,
                approved=not approval_required and permission != "blocked",
                blocked=permission == "blocked",
                risk_score=self._risk_score(record["risk_level"]),
                reason=record["summary"],
            )
        )
        return record

    def _create_checkpoint(self, action: dict[str, Any]) -> dict[str, Any]:
        now = self._now()
        checkpoint = {
            "checkpoint_id": str(uuid4()),
            "run_id": action.get("run_id"),
            "action_id": action.get("action_id"),
            "workspace_id": action.get("workspace_id"),
            "action_type": action.get("action_type"),
            "summary": action.get("summary"),
            "permission_level": action.get("permission_level"),
            "risk_level": action.get("risk_level"),
            "status": "pending",
            "decision": None,
            "comment": None,
            "created_at": now,
            "updated_at": now,
        }
        checkpoints = self.storage.read_list(self.checkpoints_file)
        checkpoints.append(checkpoint)
        self.storage.write_list(self.checkpoints_file, checkpoints)
        self.governance.log_event(
            GovernanceEvent(
                run_id=action.get("run_id"),
                workspace_id=action.get("workspace_id"),
                task_type="autopilot",
                agent_name="Autopilot Service",
                action_type="autopilot_checkpoint_created",
                tool_used="AutopilotService",
                permission_level=action.get("permission_level", "approve_to_edit"),
                approved=False,
                blocked=True,
                risk_score=self._risk_score(action.get("risk_level", "medium")),
                reason=action.get("summary") or "Autopilot action requires approval.",
            )
        )
        return checkpoint

    def _classify_permission(self, action_type: str, files: list[str], command: str | None) -> str:
        normalized = action_type.lower().strip()
        if command:
            return self.permissions.permission_for_action("command_run", command=command)
        if normalized in {"command_run", "test_run", "build_run"}:
            return self.permissions.permission_for_action("command_run", command=command or "")
        if normalized in {"file_edit", "apply_patch", "edit", "write_file"}:
            if any(self.permissions.is_unsafe_path(path) for path in files):
                return "blocked"
            return "approve_to_edit"
        if normalized in {"plan", "automation_plan", "prompt_planning"}:
            return "plan_only"
        if normalized in {"file_scan", "file_analysis", "research", "read"}:
            return "read_only"
        return self.permissions.permission_for_action(normalized, command=command, path=files[0] if files else None)

    def _infer_actions(self, prompt: str) -> list[dict[str, Any]]:
        lowered = prompt.lower()
        actions: list[dict[str, Any]] = [
            {
                "action_type": "automation_plan",
                "summary": "Create a supervised plan for the requested work.",
                "risk_level": "low",
            }
        ]
        if any(token in lowered for token in ("edit", "change", "modify", "implement", "add ", "fix ")):
            actions.append(
                {
                    "action_type": "file_edit",
                    "summary": "Prepare file changes for user approval before applying them.",
                    "files_targeted": [],
                    "risk_level": "medium",
                }
            )
        if any(token in lowered for token in ("test", "build", "verify", "run")):
            actions.append(
                {
                    "action_type": "command_run",
                    "summary": "Run an allowlisted verification command after approval.",
                    "command_requested": "pytest" if "test" in lowered else "npm run build",
                    "risk_level": "medium",
                }
            )
        return actions

    def _update_run_status(self, run_id: str, status: str) -> dict[str, Any]:
        run = self.get_run(run_id)
        if not run:
            raise ValueError("Autopilot run not found.")
        clean = {key: value for key, value in run.items() if key not in {"actions", "checkpoints"}}
        clean["status"] = status
        clean["updated_at"] = self._now()
        self._replace_run(clean)
        return self.get_run(run_id) or clean

    def _replace_run(self, run: dict[str, Any]) -> None:
        runs = self.storage.read_list(self.runs_file)
        self.storage.write_list(self.runs_file, [run if item.get("run_id") == run.get("run_id") else item for item in runs])

    def _replace_action(self, action: dict[str, Any]) -> None:
        actions = self.storage.read_list(self.actions_file)
        self.storage.write_list(
            self.actions_file,
            [action if item.get("action_id") == action.get("action_id") else item for item in actions],
        )

    def _get_action(self, action_id: str | None) -> dict[str, Any] | None:
        if not action_id:
            return None
        return next((item for item in self.storage.read_list(self.actions_file) if item.get("action_id") == action_id), None)

    def _update_actions_for_run(self, run_id: str, status: str, *, only_unfinished: bool = False) -> None:
        actions = self.storage.read_list(self.actions_file)
        finished = {"completed", "rejected", "blocked"}
        next_actions = []
        for action in actions:
            if action.get("run_id") == run_id and (not only_unfinished or action.get("status") not in finished):
                action = {**action, "status": status, "updated_at": self._now()}
            next_actions.append(action)
        self.storage.write_list(self.actions_file, next_actions)

    def _refresh_run_counts(self, run_id: str | None) -> None:
        if not run_id:
            return
        run = next((item for item in self.storage.read_list(self.runs_file) if item.get("run_id") == run_id), None)
        if not run:
            return
        actions = self.list_actions(run_id=run_id)
        checkpoints = self.list_checkpoints(run_id=run_id)
        run["actions_count"] = len(actions)
        run["pending_checkpoints_count"] = sum(1 for item in checkpoints if item.get("status") == "pending")
        if run["pending_checkpoints_count"] == 0 and run.get("status") == "waiting_approval":
            run["status"] = "planned"
        run["updated_at"] = self._now()
        self._replace_run(run)

    @staticmethod
    def _risk_score(risk_level: str) -> int:
        return {"low": 20, "medium": 50, "high": 80}.get(risk_level, 50)

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()
