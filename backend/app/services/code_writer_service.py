from __future__ import annotations

import os
import re
import subprocess
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService

WRITES_OPT_IN_ENV = "CODE_WRITES_ENABLED"
ALLOWED_REPOS_ENV = "CODE_WRITER_ALLOWED_REPOS"  # comma-separated absolute repo paths

# Only these git subcommands may ever run, and only in this narrow sequence
# (read the current branch, create ONE new branch, stage ONE file, commit —
# with a best-effort checkout back to the original branch on any failure). No
# push, no reset, no rm, no clean, no force anything. Always an argv list,
# never a shell string — mirrors GitReaderService's safety architecture,
# applied to a deliberately narrow set of writes instead of reads.
_ALLOWED = {"checkout", "add", "commit", "rev-parse"}
_TIMEOUT = 10
_MAX_CONTENT_BYTES = 200_000


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
    * Writes exactly ONE file, always on a brand-new branch (never touches an
      existing branch), then makes exactly ONE commit. No push, no PR, no
      merge — a human decides whether to push the resulting local branch.
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

    def _run(self, repo: str, args: list[str]) -> str:
        if not args or args[0] not in _ALLOWED:
            raise ValueError("git subcommand not allowed")
        try:
            result = subprocess.run(
                ["git", "-C", repo, *args],
                capture_output=True, text=True, timeout=_TIMEOUT, check=False, shell=False,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            raise ValueError(f"git write failed: {type(exc).__name__}")
        if result.returncode != 0:
            raise ValueError((result.stderr or "git write failed").strip()[:300])
        return result.stdout

    def status(self) -> dict:
        writes_enabled = self.writes_enabled()
        return {
            "available": True,
            "writes_enabled": writes_enabled,
            "writes_opt_in_env": WRITES_OPT_IN_ENV,
            "allowed_repos_env": ALLOWED_REPOS_ENV,
            "allowed_repos": self._allowed_repos() if writes_enabled else [],
            "allowed_git_subcommands": sorted(_ALLOWED),
            "note": "Writes exactly one file per call, always on a brand-new branch, then makes one local "
                    "commit. Never pushes, never opens a PR — a human decides whether to push it. Off by "
                    "default; the target repo must be explicitly allow-listed.",
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
        branch_name = re.sub(r"[^a-zA-Z0-9/_.-]", "-", str(branch_name or f"eva/auto-{uuid4().hex[:10]}"))[:120]

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

    def analytics_summary(self) -> dict:
        return {"code_writer_writes_enabled": self.writes_enabled()}
