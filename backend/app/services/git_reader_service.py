from __future__ import annotations

import os
import re
import subprocess
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService

# Only these read-only git subcommands may ever run. No mutating verbs
# (commit/push/checkout/reset/…) are permitted, and commands are always passed
# as an argv list — never through a shell — so nothing can be injected.
_ALLOWED = {"log", "branch", "show", "rev-parse", "diff"}
_SHA_RE = re.compile(r"^[0-9a-fA-F]{4,40}$")
_UNIT = "\x1f"   # field separator
_TIMEOUT = 10
_MAX_OUTPUT = 200_000


class GitReaderService:
    """Real, read-only git reads on an opt-in local repo path.

    Complements :class:`GitDiscoveryService` (which only reads ``.git`` metadata)
    by surfacing the actual commit log, branch list, and per-commit diff stats.

    Safety: this is the **only** place we shell out, and it is tightly boxed —
    read-only subcommands from a fixed allow-list, always invoked as an **argv
    list (never a shell string)**, on a path first verified to be inside a git
    work tree, with any commit ref validated against a hex-sha pattern, plus
    output-size and timeout caps. It cannot mutate the repo, and it is not
    general shell access. Every read is governance-logged.
    """

    def __init__(self, governance_service: GovernanceService):
        self.governance = governance_service

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="git_reader",
                agent_name="Git Reader",
                action_type=action_type,
                tool_used="GitReaderService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    # -- guarded execution ---------------------------------------------------
    @staticmethod
    def _resolve(path: str) -> str:
        p = os.path.realpath(os.path.expanduser(str(path or "")))
        if not os.path.isdir(p):
            raise ValueError("path is not a directory")
        return p

    def _run(self, repo: str, args: list[str]) -> str:
        if not args or args[0] not in _ALLOWED:
            raise ValueError("git subcommand not allowed")
        try:
            result = subprocess.run(
                ["git", "-C", repo, *args],
                capture_output=True, text=True, timeout=_TIMEOUT, check=False, shell=False,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            raise ValueError(f"git read failed: {type(exc).__name__}")
        if result.returncode != 0:
            raise ValueError((result.stderr or "git read failed").strip()[:200])
        return result.stdout[:_MAX_OUTPUT]

    def _assert_repo(self, repo: str) -> None:
        out = self._run(repo, ["rev-parse", "--is-inside-work-tree"]).strip()
        if out != "true":
            raise ValueError("not a git work tree")

    @staticmethod
    def _valid_ref(ref: str) -> str:
        ref = str(ref or "HEAD").strip()
        if ref == "HEAD" or _SHA_RE.match(ref):
            return ref
        raise ValueError("invalid commit ref (expected HEAD or a hex sha)")

    def status(self) -> dict:
        available = False
        try:
            subprocess.run(["git", "--version"], capture_output=True, timeout=5, check=True, shell=False)
            available = True
        except Exception:  # noqa: BLE001
            available = False
        return {"available": available, "allowed_subcommands": sorted(_ALLOWED), "read_only": True}

    # -- reads ---------------------------------------------------------------
    def log(self, path: str, limit: int = 20) -> dict:
        repo = self._resolve(path)
        self._assert_repo(repo)
        try:
            limit = max(1, min(200, int(limit)))
        except (TypeError, ValueError):
            limit = 20
        fmt = _UNIT.join(["%H", "%h", "%an", "%ae", "%aI", "%s"])
        out = self._run(repo, ["log", f"--max-count={limit}", f"--pretty=format:{fmt}"])
        commits = []
        for line in out.splitlines():
            parts = line.split(_UNIT)
            if len(parts) == 6:
                commits.append({
                    "sha": parts[0], "short": parts[1], "author": parts[2],
                    "email_domain": parts[3].split("@")[-1] if "@" in parts[3] else "",
                    "date": parts[4], "subject": parts[5],
                })
        self._log("git_log_read", f"Read {len(commits)} commits from {os.path.basename(repo)}")
        return {"commits": commits, "count": len(commits)}

    def branches(self, path: str) -> dict:
        repo = self._resolve(path)
        self._assert_repo(repo)
        current = self._run(repo, ["rev-parse", "--abbrev-ref", "HEAD"]).strip()
        fmt = _UNIT.join(["%(refname:short)", "%(objectname:short)", "%(committerdate:iso8601)"])
        out = self._run(repo, ["branch", "--format=" + fmt])
        branches = []
        for line in out.splitlines():
            parts = line.split(_UNIT)
            if len(parts) >= 2:
                branches.append({"name": parts[0], "head": parts[1],
                                 "last_commit": parts[2] if len(parts) > 2 else "",
                                 "current": parts[0] == current})
        self._log("git_branches_read", f"Read {len(branches)} branches from {os.path.basename(repo)}")
        return {"branches": branches, "current": current, "count": len(branches)}

    def commit_stat(self, path: str, ref: str = "HEAD") -> dict:
        repo = self._resolve(path)
        self._assert_repo(repo)
        ref = self._valid_ref(ref)
        fmt = _UNIT.join(["%H", "%an", "%aI", "%s"])
        out = self._run(repo, ["show", "--stat", "--no-color", f"--pretty=format:{fmt}", ref])
        lines = out.splitlines()
        header = lines[0].split(_UNIT) if lines and _UNIT in lines[0] else ["", "", "", ""]
        files, summary = [], ""
        for line in lines[1:]:
            s = line.strip()
            if not s:
                continue
            if re.search(r"\d+ file", s) and "changed" in s:
                summary = s
            elif "|" in s:
                name, _, meta = s.partition("|")
                files.append({"file": name.strip(), "changes": meta.strip()})
        self._log("git_commit_stat_read", f"Read commit stat {ref[:8]} from {os.path.basename(repo)}")
        return {
            "sha": header[0], "author": header[1] if len(header) > 1 else "",
            "date": header[2] if len(header) > 2 else "", "subject": header[3] if len(header) > 3 else "",
            "files": files[:200], "summary": summary,
        }

    def analytics_summary(self) -> dict:
        return {"git_reader_available": self.status()["available"]}
