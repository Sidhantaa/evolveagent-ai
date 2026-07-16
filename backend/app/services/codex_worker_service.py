from __future__ import annotations

import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from app.config import settings
from app.services.codex_job_service import CodexJobService
from app.services.git_service import GitService
from app.services.linear_service import LinearServiceError
from app.services.safe_command_runner import SafeCommandRunner

UNSAFE_CHANGED_PARTS = (
    ".env",
    "backend/.env",
    "node_modules/",
    "venv/",
    ".git/",
    "backend/app/uploads/",
    "backend/app/data/",
    "__pycache__/",
    ".pytest_cache/",
)


class CodexWorkerError(Exception):
    pass


class CodexWorkerService:
    def __init__(
        self,
        job_service: CodexJobService,
        git_service: GitService,
        command_runner: SafeCommandRunner,
        linear_orchestration: Any | None = None,
        codex_runner: Callable[[str, Path, str], subprocess.CompletedProcess[str]] | None = None,
    ):
        self.jobs = job_service
        self.git = git_service
        self.command_runner = command_runner
        self.orchestration = linear_orchestration
        self._codex_runner = codex_runner or self._default_codex_runner

    def run_for_issue(self, issue_id: str) -> dict[str, Any]:
        if not settings.codex_worker_enabled:
            raise CodexWorkerError(
                "Codex worker is disabled. Set CODEX_WORKER_ENABLED=true in backend/.env to enable."
            )

        if self.orchestration is None:
            raise CodexWorkerError("Linear orchestration is not configured")

        link = self.orchestration.links.get_link_by_issue(issue_id)
        if link is None:
            raise CodexWorkerError("Linear issue is not linked. Move it to In Progress or Sync first.")

        issue = self.orchestration.linear.get_linear_issue(issue_id)
        identifier = issue.get("identifier") or link.get("linear_identifier") or issue_id
        branch_name = link.get("branch_name") or f"linear/{identifier.lower()}"
        handoff_path = self._resolve_handoff_path(link, identifier)

        existing = self.jobs.get_latest_job_for_issue(issue_id)
        if existing and existing.get("status") in {"queued", "running"}:
            raise CodexWorkerError(f"Codex job already {existing['status']} for this issue")

        job = self.jobs.create_job(
            {
                "issue_id": issue_id,
                "issue_identifier": identifier,
                "branch_name": branch_name,
                "handoff_path": handoff_path,
            }
        )
        job_id = job["job_id"]
        stage = "initializing"

        try:
            self.jobs.update_job(job_id, {"status_detail": "Validating Codex CLI, handoff, and branch"})
            self._validate_codex_installed()
            stage = "handoff_validation"
            self._validate_handoff_file(handoff_path)
            stage = "branch_validation"
            self._validate_branch_exists(branch_name)
            stage = "checkout"
            checkout = self.git.checkout_branch(branch_name)
            if not checkout.get("success"):
                raise CodexWorkerError(f"Failed to checkout branch `{branch_name}`: {checkout.get('message')}")

            current = self.git.current_branch()
            if current != branch_name:
                raise CodexWorkerError(
                    f"Branch mismatch after checkout. Expected `{branch_name}` but on `{current}`."
                )

            self.jobs.update_job(job_id, {"status": "running", "started_at": datetime.now(UTC).isoformat()})

            stage = "codex_execution"
            self.jobs.update_job(job_id, {"status_detail": "Running Codex CLI against the handoff brief"})
            prompt = Path(handoff_path).read_text(encoding="utf-8")
            codex_result = self._codex_runner(settings.codex_cli_command, self.git.project_root, prompt)
            stdout = codex_result.stdout or ""
            stderr = codex_result.stderr or ""
            self.jobs.update_job(job_id, {"codex_stdout": stdout[-8000:], "codex_stderr": stderr[-8000:]})

            if codex_result.returncode != 0:
                raise CodexWorkerError(
                    f"Codex CLI failed with exit code {codex_result.returncode}. "
                    f"Install Codex CLI or check CODEX_CLI_COMMAND. stderr: {stderr[-500:]}"
                )

            stage = "change_safety_check"
            self.jobs.update_job(job_id, {"status_detail": "Checking changed files against safety rules"})
            changed_files = self.git.list_changed_files()
            unsafe = self._unsafe_changed_files(changed_files)
            if unsafe:
                raise CodexWorkerError(f"Unsafe files changed: {', '.join(unsafe[:8])}")

            if len(changed_files) > settings.codex_max_files_changed:
                raise CodexWorkerError(
                    f"Too many files changed ({len(changed_files)} > {settings.codex_max_files_changed})"
                )

            self.jobs.update_job(job_id, {"changed_files": changed_files})

            stage = "verification"
            self.jobs.update_job(job_id, {"status_detail": "Running pytest and frontend build verification"})
            test_results = self._run_verification()
            verification_summary = self._verification_summary(test_results)
            self.jobs.update_job(
                job_id,
                {
                    "test_results": test_results,
                    "test_result": self._command_result(test_results, "pytest"),
                    "build_result": self._command_result(test_results, "npm run build"),
                    "verification_summary": verification_summary,
                },
            )
            if not all(item.get("success") for item in test_results):
                raise CodexWorkerError("Verification failed. Tests or build did not pass.")

            commit_hash = None
            if changed_files:
                stage = "staging"
                self.jobs.update_job(job_id, {"status_detail": "Staging safe changed files"})
                stage_result = self.git.add_safe_files()
                excluded = stage_result.get("excluded_files") or []
                if excluded:
                    raise CodexWorkerError(f"Unsafe files blocked from staging: {', '.join(excluded[:8])}")
                if stage_result.get("staged_files"):
                    stage = "commit"
                    self.jobs.update_job(job_id, {"status_detail": "Committing verified Codex changes"})
                    commit_message = f"Linear {identifier}: autonomous Codex implementation"
                    commit_result = self.git.commit(commit_message)
                    if not commit_result.get("success"):
                        raise CodexWorkerError(f"Commit failed: {commit_result.get('message')}")
                    commit_hash = commit_result.get("commit_hash") or ""
                    self.jobs.update_job(job_id, {"commit_hash": commit_hash})
                    self.orchestration.links.append_commit(
                        issue_id,
                        {
                            "hash": commit_hash,
                            "message": commit_message,
                            "at": datetime.now(UTC).isoformat(),
                            "subtask": "codex_worker",
                        },
                    )

            stage = "push"
            self.jobs.update_job(job_id, {"status_detail": "Optionally pushing branch if AUTO_GIT_PUSH=true"})
            push_result = self.git.push()
            if push_result.get("success"):
                self.orchestration.links.append_push(
                    issue_id,
                    {
                        "at": datetime.now(UTC).isoformat(),
                        "branch": push_result.get("branch"),
                        "remote": push_result.get("remote"),
                    },
                )

            stage = "linear_verification"
            self.jobs.update_job(job_id, {"status_detail": "Verifying work and updating Linear"})
            completion_note = (
                f"Autonomous Codex worker completed on `{branch_name}`.\n"
                f"Changed files: {len(changed_files)}\n"
                f"Commit: `{commit_hash or 'none'}`"
            )
            verify_result = self.orchestration.verify_cursor_work(
                issue_id,
                completion_note=completion_note,
                auto_commit=False,
            )
            linear_done = bool((verify_result.get("linear_completion") or {}).get("completed"))

            final_status = "passed" if verify_result.get("verified") else "failed"
            job = self.jobs.update_job(
                job_id,
                {
                    "status": final_status,
                    "status_detail": "Completed" if final_status == "passed" else "Linear verification failed",
                    "completed_at": datetime.now(UTC).isoformat(),
                    "linear_done": linear_done,
                    "error": None if linear_done else "Verification or Linear completion did not succeed",
                    "manual_review_required": not linear_done,
                    "summary": self._success_summary(identifier, branch_name, changed_files, commit_hash, linear_done),
                },
            )
            self.orchestration._log(
                "codex_worker_completed" if linear_done else "codex_worker_failed",
                f"Codex job {job_id} for {identifier}: {final_status}",
            )
            return {"job": job, "verify_result": verify_result}

        except Exception as error:  # noqa: BLE001 - any real failure must still leave the job terminal
            # Round 34 (error-path lens): this used to only catch
            # (CodexWorkerError, LinearServiceError) -- a real exception of
            # any OTHER type (subprocess.TimeoutExpired from a Codex CLI run
            # overrunning its 600s timeout, FileNotFoundError from a handoff
            # file removed after validation, etc.) escaped uncaught, leaving
            # the job stuck "running" forever. Worse: the "already running"
            # guard above then permanently blocked every future run_for_issue
            # call for that issue (background poll AND manual route) until a
            # human hand-edited codex_jobs.json. Broadened to catch any
            # exception so a real failure always degrades to a terminal,
            # inspectable job state instead of wedging the issue.
            error_message = f"{type(error).__name__}: {error}" if not isinstance(error, (CodexWorkerError, LinearServiceError)) else str(error)
            status = self._failure_status(stage, error_message)
            job = self.jobs.update_job(
                job_id,
                {
                    "status": status,
                    "status_detail": self._failure_status_detail(stage, error_message),
                    "failure_stage": stage,
                    "completed_at": datetime.now(UTC).isoformat(),
                    "error": error_message,
                    "linear_done": False,
                    "manual_review_required": True,
                    "summary": self._failure_summary(identifier, branch_name, stage, error_message),
                },
            )
            self._post_failure_comment(issue_id, identifier, error_message, job)
            return {"job": job, "error": error_message}

    def _post_failure_comment(
        self,
        issue_id: str,
        identifier: str,
        message: str,
        job: dict[str, Any] | None = None,
    ) -> None:
        if self.orchestration is None:
            return
        changed_files = job.get("changed_files") if job else []
        verification = job.get("verification_summary") if job else ""
        body = (
            f"**EvolveAgent Codex worker needs manual review for `{identifier}`**\n\n"
            f"Stage: `{(job or {}).get('failure_stage') or 'unknown'}`\n"
            f"Status: `{(job or {}).get('status') or 'failed'}`\n"
            f"Changed files: {len(changed_files or [])}\n"
            f"Verification: {verification or 'not completed'}\n\n"
            f"Error:\n{message[:1800]}"
        )
        try:
            self.orchestration.linear.add_linear_comment(issue_id, body)
        except LinearServiceError:
            pass

    def _resolve_handoff_path(self, link: dict[str, Any], identifier: str) -> str:
        if link.get("cursor_brief_path"):
            path = Path(link["cursor_brief_path"])
            if path.is_absolute():
                return str(path)
            return str(self.git.project_root / path)
        relative = f"docs/linear-handoffs/{identifier.lower()}.md"
        return str(self.git.project_root / relative)

    @staticmethod
    def _validate_codex_installed() -> None:
        command = settings.codex_cli_command.strip().split()[0]
        if not shutil.which(command):
            raise CodexWorkerError(
                f"Codex CLI not found (`{command}`). Install Codex CLI or set CODEX_CLI_COMMAND in .env."
            )

    @staticmethod
    def _validate_handoff_file(handoff_path: str) -> None:
        path = Path(handoff_path)
        if not path.exists():
            raise CodexWorkerError(f"Handoff file missing: {handoff_path}. Run poll or Sync first.")

    def _validate_branch_exists(self, branch_name: str) -> None:
        result = self.git._run("show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}")
        if result.returncode != 0:
            raise CodexWorkerError(
                f"Branch `{branch_name}` does not exist locally. Move issue to In Progress and run poll first."
            )

    @staticmethod
    def _unsafe_changed_files(changed_files: list[str]) -> list[str]:
        unsafe: list[str] = []
        for path in changed_files:
            normalized = path.replace("\\", "/")
            if any(part in normalized for part in UNSAFE_CHANGED_PARTS):
                unsafe.append(path)
        return unsafe

    def _run_verification(self) -> list[dict[str, Any]]:
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
    def _command_result(results: list[dict[str, Any]], command: str) -> dict[str, Any] | None:
        return next((item for item in results if item.get("command") == command), None)

    @staticmethod
    def _verification_summary(results: list[dict[str, Any]]) -> str:
        if not results:
            return "not run"
        parts = []
        for item in results:
            label = "passed" if item.get("success") else "failed"
            parts.append(f"{item.get('command')}: {label}")
        return "; ".join(parts)

    @staticmethod
    def _failure_status(stage: str, message: str) -> str:
        if "Unsafe" in message or stage in {"change_safety_check", "staging"}:
            return "blocked"
        if stage == "verification":
            return "needs_manual_review"
        return "failed"

    @staticmethod
    def _failure_status_detail(stage: str, message: str) -> str:
        if stage == "verification":
            return "Verification failed; manual review required"
        if "Unsafe" in message:
            return "Blocked by worker safety rules"
        return f"Failed during {stage.replace('_', ' ')}"

    @staticmethod
    def _success_summary(
        identifier: str,
        branch_name: str,
        changed_files: list[str],
        commit_hash: str | None,
        linear_done: bool,
    ) -> str:
        done = "Linear marked Done" if linear_done else "Linear completion pending"
        return (
            f"{identifier} completed on {branch_name}. "
            f"Changed files: {len(changed_files)}. "
            f"Commit: {commit_hash or 'none'}. {done}."
        )

    @staticmethod
    def _failure_summary(identifier: str, branch_name: str, stage: str, message: str) -> str:
        return (
            f"{identifier} on {branch_name} needs manual review. "
            f"Failed stage: {stage.replace('_', ' ')}. "
            f"Reason: {message[:240]}"
        )

    @staticmethod
    def _default_codex_runner(cli_command: str, project_root: Path, prompt: str) -> subprocess.CompletedProcess[str]:
        command_parts = cli_command.strip().split()
        if not command_parts:
            raise CodexWorkerError("CODEX_CLI_COMMAND is empty")

        # Try `codex exec --cd <root> <prompt>` first; fall back to stdin if needed.
        exec_args = [*command_parts, "exec", "--cd", str(project_root), prompt]
        result = subprocess.run(
            exec_args,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=600,
        )
        if result.returncode == 0:
            return result

        stdin_args = [*command_parts, "exec", "--cd", str(project_root), "-"]
        stdin_result = subprocess.run(
            stdin_args,
            cwd=project_root,
            input=prompt,
            capture_output=True,
            text=True,
            check=False,
            timeout=600,
        )
        if stdin_result.returncode == 0:
            return stdin_result

        combined = result
        combined.stderr = (result.stderr or "") + "\n" + (stdin_result.stderr or "")
        combined.stdout = (result.stdout or "") + "\n" + (stdin_result.stdout or "")
        combined.returncode = stdin_result.returncode or result.returncode
        return combined
