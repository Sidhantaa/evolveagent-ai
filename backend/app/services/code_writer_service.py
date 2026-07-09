from __future__ import annotations

import os
import re
import subprocess
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService

WRITES_OPT_IN_ENV = "CODE_WRITES_ENABLED"
PUSH_OPT_IN_ENV = "CODE_WRITER_PUSH_ENABLED"
ALLOWED_REPOS_ENV = "CODE_WRITER_ALLOWED_REPOS"  # comma-separated absolute repo paths

# Only these git subcommands may ever run. checkout/add/commit/rev-parse back
# write_and_commit's narrow local-only sequence (read the current branch,
# create ONE new branch, stage ONE file, commit — with a best-effort checkout
# back to the original branch on any failure). push (v150 task 2) backs
# push_branch's own, separately-gated escalation: `git push origin <branch>`
# only, always to the "origin" remote the repo already has configured — never
# a remote URL supplied by a caller. No reset, no rm, no clean, no force
# anything, no arbitrary remote. Always an argv list, never a shell string —
# mirrors GitReaderService's safety architecture, applied to a deliberately
# narrow set of writes instead of reads.
_ALLOWED = {"checkout", "add", "commit", "rev-parse", "push"}
_TIMEOUT = 10
_PUSH_TIMEOUT = 30
_MAX_CONTENT_BYTES = 200_000
_MAX_FILES = 10


class CodeWriterService:
    """v150 Autonomous Software Team — the app's first real, write-capable code
    agent. Deliberately narrow and always approval-gated: never called directly
    by an agent, only reachable via an approved DurableWorkflowService step, so
    a real commit only ever happens after explicit human sign-off.

    Safety model:
    * Off by default via CODE_WRITES_ENABLED (mirrors every other real-write
      flag in this app: GITHUB_WRITES_ENABLED, MCP_REAL_GITHUB, ...).
    * The target repo must be on an explicit allow-list
      (CODE_WRITER_ALLOWED_REPOS) — this can never be pointed at an arbitrary
      directory, and critically the app's own live source tree is never
      included unless an operator explicitly opts it in, so a code-writing
      agent can never unsupervisedly modify the app that is running it.
    * write_and_commit writes exactly ONE file, always on a brand-new branch
      (never touches an existing branch), then makes exactly ONE commit.
      write_files_and_commit (v150 task 3) is the same contract for a change
      spanning several related files (capped at _MAX_FILES) in ONE commit.
    * push_branch (v150 task 2) is a bigger escalation — a human-approved local
      commit becoming visible to others — so it is gated by its OWN opt-in flag
      (CODE_WRITER_PUSH_ENABLED) on top of writes_enabled(). It only ever pushes
      to the repo's existing "origin" remote (never a caller-supplied URL), and
      never handles or stores push credentials — whatever the repo's own git
      config already uses (SSH key, credential helper) is what applies. Even
      with push enabled, this service never opens a PR itself; that's
      GitHubConnectorService.create_pull_request's job, orchestrated by a
      separate, separately-approved workflow step (open_pull_request).
    * Any failure mid-sequence best-effort checks the repo back out onto its
      original branch, so a partial failure never leaves the repo stranded on
      a half-finished branch.
    """

    def __init__(self, governance_service: GovernanceService):
        self.governance = governance_service

    @staticmethod
    def writes_enabled() -> bool:
        return str(os.environ.get(WRITES_OPT_IN_ENV, "")).strip().lower() in ("1", "true", "yes", "on")

    @staticmethod
    def push_enabled() -> bool:
        return str(os.environ.get(PUSH_OPT_IN_ENV, "")).strip().lower() in ("1", "true", "yes", "on")

    @staticmethod
    def _allowed_repos() -> list[str]:
        raw = os.environ.get(ALLOWED_REPOS_ENV, "")
        return [os.path.realpath(os.path.expanduser(p.strip())) for p in raw.split(",") if p.strip()]

    def _log(self, action_type: str, reason: str, blocked: bool = False) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="code_writer", agent_name="Code Writer", action_type=action_type,
                tool_used="CodeWriterService", permission_level="approve_to_run",
                approved=not blocked, blocked=blocked, risk_score=20 if blocked else 40,
                reason=reason,
            )
        )

    @staticmethod
    def _safe_branch_name(branch_name: str | None) -> str:
        """Sanitize a caller-supplied branch name for argv use. Beyond the
        character allow-list, a name starting with "-" could otherwise be
        misread as a git flag (e.g. "--force") rather than a ref — strip any
        leading dashes/dots so it can never be mistaken for one."""
        cleaned = re.sub(r"[^a-zA-Z0-9/_.-]", "-", str(branch_name or "")).lstrip("-.")[:120]
        return cleaned or f"eva/auto-{uuid4().hex[:10]}"

    def _run(self, repo: str, args: list[str], timeout: int = _TIMEOUT) -> str:
        if not args or args[0] not in _ALLOWED:
            raise ValueError("git subcommand not allowed")
        try:
            result = subprocess.run(
                ["git", "-C", repo, *args],
                capture_output=True, text=True, timeout=timeout, check=False, shell=False,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            raise ValueError(f"git write failed: {type(exc).__name__}")
        if result.returncode != 0:
            raise ValueError((result.stderr or "git write failed").strip()[:300])
        return result.stdout

    def status(self) -> dict:
        writes_enabled = self.writes_enabled()
        push_enabled = self.push_enabled()
        return {
            "available": True,
            "writes_enabled": writes_enabled,
            "writes_opt_in_env": WRITES_OPT_IN_ENV,
            "push_enabled": push_enabled,
            "push_opt_in_env": PUSH_OPT_IN_ENV,
            "allowed_repos_env": ALLOWED_REPOS_ENV,
            "allowed_repos": self._allowed_repos() if writes_enabled else [],
            "allowed_git_subcommands": sorted(_ALLOWED),
            "note": "write_and_commit writes exactly one file per call, always on a brand-new branch, then "
                    "makes one local commit. push_branch (a separate opt-in on top of writes_enabled) pushes "
                    "that branch to the repo's existing origin remote only. This service never opens a PR "
                    "itself — that's a separate, separately-approved step. Off by default; the target repo "
                    "must be explicitly allow-listed.",
        }

    def write_and_commit(
        self, repo_path: str, file_path: str, content: str, commit_message: str, branch_name: str | None = None,
    ) -> dict:
        """The one real write this service performs. Never called directly by an
        agent — only reachable via an approved DurableWorkflowService step."""
        if not self.writes_enabled():
            self._log("code_write_declined", f"write_and_commit declined: {WRITES_OPT_IN_ENV} is not enabled", blocked=True)
            return {"wrote": False, "note": f"Code writes are disabled. Set {WRITES_OPT_IN_ENV}=true to enable."}

        repo = os.path.realpath(os.path.expanduser(str(repo_path or "")))
        if repo not in self._allowed_repos():
            self._log("code_write_declined", f"write_and_commit declined: {repo} is not on the allow-list", blocked=True)
            return {"wrote": False, "note": f"Repo is not on the allow-list. Add it to {ALLOWED_REPOS_ENV}."}
        if not os.path.isdir(repo):
            return {"wrote": False, "note": "Repo path is not a directory."}

        target = os.path.realpath(os.path.join(repo, str(file_path or "").lstrip("/")))
        if not target.startswith(repo + os.sep):
            self._log("code_write_declined", f"write_and_commit declined: path traversal attempt ({file_path})", blocked=True)
            return {"wrote": False, "note": "file_path must resolve inside the repo."}

        content = str(content or "")
        if len(content.encode("utf-8")) > _MAX_CONTENT_BYTES:
            return {"wrote": False, "note": f"content exceeds the {_MAX_CONTENT_BYTES}-byte limit."}
        commit_message = str(commit_message or "").strip()[:300] or "EvolveAgent: automated code change"
        branch_name = self._safe_branch_name(branch_name)

        try:
            original_branch = self._run(repo, ["rev-parse", "--abbrev-ref", "HEAD"]).strip()
        except ValueError as exc:
            self._log("code_write_failed", f"write_and_commit could not read current branch in {repo}: {exc}", blocked=True)
            return {"wrote": False, "note": str(exc)}

        try:
            self._run(repo, ["checkout", "-b", branch_name])
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            self._run(repo, ["add", os.path.relpath(target, repo)])
            self._run(repo, ["commit", "-m", commit_message])
            sha = self._run(repo, ["rev-parse", "HEAD"]).strip()
        except (ValueError, OSError) as exc:
            try:
                self._run(repo, ["checkout", original_branch])
            except ValueError:
                pass  # best-effort — the failure note below is what matters
            self._log("code_write_failed", f"write_and_commit failed for {repo}: {exc}", blocked=True)
            return {"wrote": False, "note": str(exc)}

        self._log("code_write_committed", f"Committed a code change to {branch_name} in {os.path.basename(repo)}: {commit_message}")
        return {
            "wrote": True, "repo": repo, "branch": branch_name, "commit_sha": sha,
            "file_path": os.path.relpath(target, repo), "commit_message": commit_message,
            "note": "Committed locally on a new branch. Not pushed — a human decides whether to push it.",
        }

    def write_files_and_commit(
        self, repo_path: str, files: list[dict], commit_message: str, branch_name: str | None = None,
    ) -> dict:
        """v150 task 3 — like write_and_commit, but for a change that spans
        several related files in ONE commit. `files` is a list of
        {"file_path": ..., "content": ...} dicts (up to _MAX_FILES). Same
        safety rules as write_and_commit (allow-listed repo, every path must
        resolve inside the repo, combined content is size-capped), plus a cap
        on file count. Never called directly by an agent — only reachable via
        an approved DurableWorkflowService step."""
        if not self.writes_enabled():
            self._log("code_write_declined", f"write_files_and_commit declined: {WRITES_OPT_IN_ENV} is not enabled", blocked=True)
            return {"wrote": False, "note": f"Code writes are disabled. Set {WRITES_OPT_IN_ENV}=true to enable."}

        repo = os.path.realpath(os.path.expanduser(str(repo_path or "")))
        if repo not in self._allowed_repos():
            self._log("code_write_declined", f"write_files_and_commit declined: {repo} is not on the allow-list", blocked=True)
            return {"wrote": False, "note": f"Repo is not on the allow-list. Add it to {ALLOWED_REPOS_ENV}."}
        if not os.path.isdir(repo):
            return {"wrote": False, "note": "Repo path is not a directory."}

        if not files:
            return {"wrote": False, "note": "At least one file is required."}
        if len(files) > _MAX_FILES:
            return {"wrote": False, "note": f"Too many files (max {_MAX_FILES} per commit)."}

        resolved: list[tuple[str, str]] = []
        total_bytes = 0
        for item in files:
            file_path = str((item or {}).get("file_path") or "")
            content = str((item or {}).get("content") or "")
            target = os.path.realpath(os.path.join(repo, file_path.lstrip("/")))
            if not target.startswith(repo + os.sep):
                self._log("code_write_declined", f"write_files_and_commit declined: path traversal attempt ({file_path})", blocked=True)
                return {"wrote": False, "note": "Every file_path must resolve inside the repo."}
            total_bytes += len(content.encode("utf-8"))
            resolved.append((target, content))
        if total_bytes > _MAX_CONTENT_BYTES:
            return {"wrote": False, "note": f"combined content exceeds the {_MAX_CONTENT_BYTES}-byte limit."}

        commit_message = str(commit_message or "").strip()[:300] or "EvolveAgent: automated code change"
        branch_name = self._safe_branch_name(branch_name)

        try:
            original_branch = self._run(repo, ["rev-parse", "--abbrev-ref", "HEAD"]).strip()
        except ValueError as exc:
            self._log("code_write_failed", f"write_files_and_commit could not read current branch in {repo}: {exc}", blocked=True)
            return {"wrote": False, "note": str(exc)}

        try:
            self._run(repo, ["checkout", "-b", branch_name])
            written_paths = []
            for target, content in resolved:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "w", encoding="utf-8") as f:
                    f.write(content)
                rel = os.path.relpath(target, repo)
                self._run(repo, ["add", rel])
                written_paths.append(rel)
            self._run(repo, ["commit", "-m", commit_message])
            sha = self._run(repo, ["rev-parse", "HEAD"]).strip()
        except (ValueError, OSError) as exc:
            try:
                self._run(repo, ["checkout", original_branch])
            except ValueError:
                pass  # best-effort — the failure note below is what matters
            self._log("code_write_failed", f"write_files_and_commit failed for {repo}: {exc}", blocked=True)
            return {"wrote": False, "note": str(exc)}

        self._log(
            "code_write_committed",
            f"Committed a {len(written_paths)}-file code change to {branch_name} in {os.path.basename(repo)}: {commit_message}",
        )
        return {
            "wrote": True, "repo": repo, "branch": branch_name, "commit_sha": sha,
            "file_paths": written_paths, "commit_message": commit_message,
            "note": "Committed locally on a new branch. Not pushed — a human decides whether to push it.",
        }

    def push_branch(self, repo_path: str, branch_name: str) -> dict:
        """v150 task 2 — push a branch that write_and_commit already created
        locally, to the repo's existing "origin" remote only (never a caller-
        supplied URL). A bigger escalation than a local commit, so it is gated
        by its OWN opt-in flag (CODE_WRITER_PUSH_ENABLED) on top of
        writes_enabled() and the same repo allow-list. Never called directly by
        an agent — only reachable via an approved DurableWorkflowService step.
        Whatever push credentials are configured for the repo's own git remote
        (SSH key, credential helper, ...) are what's used — this service never
        handles or stores push credentials itself."""
        if not self.writes_enabled():
            self._log("code_push_declined", f"push_branch declined: {WRITES_OPT_IN_ENV} is not enabled", blocked=True)
            return {"pushed": False, "note": f"Code writes are disabled. Set {WRITES_OPT_IN_ENV}=true to enable."}
        if not self.push_enabled():
            self._log("code_push_declined", f"push_branch declined: {PUSH_OPT_IN_ENV} is not enabled", blocked=True)
            return {"pushed": False, "note": f"Pushing is disabled. Set {PUSH_OPT_IN_ENV}=true to enable."}

        repo = os.path.realpath(os.path.expanduser(str(repo_path or "")))
        if repo not in self._allowed_repos():
            self._log("code_push_declined", f"push_branch declined: {repo} is not on the allow-list", blocked=True)
            return {"pushed": False, "note": f"Repo is not on the allow-list. Add it to {ALLOWED_REPOS_ENV}."}
        if not os.path.isdir(repo):
            return {"pushed": False, "note": "Repo path is not a directory."}

        branch_name = self._safe_branch_name(branch_name)
        try:
            self._run(repo, ["push", "origin", branch_name], timeout=_PUSH_TIMEOUT)
        except ValueError as exc:
            self._log("code_push_failed", f"push_branch failed for {branch_name} in {repo}: {exc}", blocked=True)
            return {"pushed": False, "note": str(exc)}

        self._log("code_push_succeeded", f"Pushed {branch_name} to origin in {os.path.basename(repo)}")
        return {"pushed": True, "repo": repo, "branch": branch_name, "note": "Pushed to origin."}

    def analytics_summary(self) -> dict:
        return {"code_writer_writes_enabled": self.writes_enabled(), "code_writer_push_enabled": self.push_enabled()}
