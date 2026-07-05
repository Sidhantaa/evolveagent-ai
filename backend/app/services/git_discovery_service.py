from __future__ import annotations

import configparser
import os
import re
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

_MAX_REPOS = 40
_MAX_SCAN_DEPTH = 3
_SKIP_DIRS = {"node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".cache", "Library"}
# Strip any embedded credentials from a remote URL (user:token@host → host).
_CRED_RE = re.compile(r"(https?://)[^@/]+@")

SAMPLE_REPO = {
    "repo_id": "sample-repo",
    "name": "sample-project",
    "provider": "local",
    "workspace_id": None,
    "local_path": "(sample)",
    "remote_url_sanitized": "https://github.com/example/sample-project.git",
    "default_branch": "main",
    "branches": ["main", "develop"],
    "recent_activity": [{"message": "Sample commit — enable discovery to index real repos.", "at": None}],
    "contributors": [],
    "ci_status": {},
    "permissions": {"read_metadata": True, "read_code": False, "write": False},
    "is_sample": True,
}


class GitDiscoveryService:
    """Phase 1 Git Intelligence — read-only, opt-in, mock-safe repository discovery.

    Detects local git repositories under a **user-provided, approved** path and reads
    only their metadata directly from the ``.git`` directory using the standard library:
    current/default branch (``.git/HEAD``), sanitized remote URL (``.git/config`` — any
    embedded credentials are stripped), branch names (``refs/heads`` + ``packed-refs``),
    and recent activity (``.git/logs/HEAD`` reflog, plain text). It **never** runs git/
    shell commands, makes no network calls, reads no file *contents* or secret values, and
    performs no mutating git operations. Discovery is opt-in; without opt-in it returns a
    sample record. Everything is governance-logged.
    """

    repos_file = "git_repos.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="git_intelligence",
                agent_name="Git Intelligence",
                action_type=action_type,
                tool_used="GitDiscoveryService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=2,
                reason=reason,
            )
        )

    @staticmethod
    def _sanitize(url: str) -> str:
        return _CRED_RE.sub(r"\1", (url or "").strip())

    @staticmethod
    def _resolve_gitdir(git_path: str) -> str:
        # In a worktree, `.git` is a file: "gitdir: /path/to/real/gitdir".
        if os.path.isfile(git_path):
            try:
                with open(git_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                if content.startswith("gitdir:"):
                    resolved = content.split(":", 1)[1].strip()
                    if not os.path.isabs(resolved):
                        resolved = os.path.normpath(os.path.join(os.path.dirname(git_path), resolved))
                    return resolved
            except OSError:
                pass
        return git_path

    def _read_repo(self, git_path: str, workspace_id: str | None) -> dict | None:
        repo_root = os.path.dirname(git_path)
        git_dir = self._resolve_gitdir(git_path)
        # config/refs live in the common dir (shared across worktrees); HEAD/reflog are per-worktree.
        common_dir = git_dir
        commondir_file = os.path.join(git_dir, "commondir")
        if os.path.isfile(commondir_file):
            try:
                with open(commondir_file, "r", encoding="utf-8", errors="ignore") as f:
                    rel = f.read().strip()
                common_dir = rel if os.path.isabs(rel) else os.path.normpath(os.path.join(git_dir, rel))
            except OSError:
                common_dir = git_dir
        try:
            # current/default branch from HEAD
            default_branch = None
            head_path = os.path.join(git_dir, "HEAD")
            if os.path.isfile(head_path):
                with open(head_path, "r", encoding="utf-8", errors="ignore") as f:
                    head = f.read().strip()
                if head.startswith("ref:"):
                    default_branch = head.split("/")[-1]
            # sanitized remote url from config
            remote = None
            cfg_path = os.path.join(common_dir, "config")
            if os.path.isfile(cfg_path):
                parser = configparser.ConfigParser(strict=False)
                try:
                    parser.read(cfg_path)
                    for section in parser.sections():
                        if section.startswith('remote ') and parser.has_option(section, "url"):
                            remote = self._sanitize(parser.get(section, "url"))
                            break
                except configparser.Error:
                    remote = None
            # branches from refs/heads + packed-refs
            branches: list[str] = []
            heads_dir = os.path.join(common_dir, "refs", "heads")
            for base, _dirs, files in os.walk(heads_dir):
                for fn in files:
                    rel = os.path.relpath(os.path.join(base, fn), heads_dir)
                    branches.append(rel.replace(os.sep, "/"))
            packed = os.path.join(common_dir, "packed-refs")
            if os.path.isfile(packed):
                with open(packed, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        m = re.search(r"refs/heads/(\S+)", line)
                        if m and m.group(1) not in branches:
                            branches.append(m.group(1))
            # recent activity from reflog (plain text, no object parsing)
            activity = []
            reflog = os.path.join(git_dir, "logs", "HEAD")
            if os.path.isfile(reflog):
                with open(reflog, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-10:]
                for line in reversed(lines):
                    tab = line.find("\t")
                    msg = line[tab + 1:].strip() if tab != -1 else line.strip()
                    ts = re.search(r"\b(\d{9,})\b", line)
                    when = datetime.fromtimestamp(int(ts.group(1)), UTC).isoformat() if ts else None
                    activity.append({"message": msg[:160], "at": when})
            return {
                "repo_id": str(uuid4()),
                "name": os.path.basename(repo_root) or "repo",
                "provider": "github" if remote and "github" in remote else "gitlab" if remote and "gitlab" in remote else "local",
                "workspace_id": workspace_id,
                "local_path": repo_root,
                "remote_url_sanitized": remote,
                "default_branch": default_branch,
                "branches": sorted(set(branches))[:50],
                "recent_activity": activity,
                "contributors": [],
                "ci_status": {},
                "permissions": {"read_metadata": True, "read_code": False, "write": False},
                "last_indexed_at": self._now(),
                "is_sample": False,
            }
        except OSError:
            return None

    def _scan(self, root: str, workspace_id: str | None) -> list[dict]:
        found = []
        root = os.path.expanduser(root)
        if not os.path.isdir(root):
            return found
        base_depth = root.rstrip(os.sep).count(os.sep)
        for base, dirs, _files in os.walk(root):
            depth = base.rstrip(os.sep).count(os.sep) - base_depth
            if depth > _MAX_SCAN_DEPTH:
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
            git_entry = os.path.join(base, ".git")
            if ".git" in dirs or os.path.isfile(git_entry):
                repo = self._read_repo(git_entry, workspace_id)
                if repo:
                    found.append(repo)
                    dirs[:] = [d for d in dirs if d != ".git"]  # don't descend into .git
                if len(found) >= _MAX_REPOS:
                    break
        return found

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def status(self) -> dict:
        repos = self.storage.read_list(self.repos_file)
        real = [r for r in repos if not r.get("is_sample")]
        return {
            "enabled": len(real) > 0,
            "indexed_repos": len(real),
            "note": "Read-only git metadata discovery. Opt-in; scans an approved local path; never runs git commands, reads code, or exposes secrets.",
        }

    def discover(self, path: str | None = None, opt_in: bool = False, workspace_id: str | None = None) -> dict:
        if not opt_in or not path:
            # Not enabled → return a sample so the UI has something to show.
            existing = self.storage.read_list(self.repos_file)
            if not any(r.get("is_sample") for r in existing):
                self.storage.append(self.repos_file, {**SAMPLE_REPO})
            self._log("git_discover_sample", "Git discovery not opted-in — returned sample repo.")
            return {"discovered": 0, "opted_in": False, "note": "Provide a local path and opt_in=true to index real repositories (read-only)."}

        found = self._scan(path, workspace_id)
        # Replace prior discoveries for this path; keep others.
        existing = [r for r in self.storage.read_list(self.repos_file) if r.get("local_path") != path and not r.get("is_sample")]
        self.storage.write_list(self.repos_file, existing + found)
        self._log("git_discovered", f"Discovered {len(found)} local repo(s) under an approved path (read-only metadata).")
        return {"discovered": len(found), "opted_in": True, "note": "Read-only metadata only; no code read, no secrets, no git commands run."}

    def repositories(self, workspace_id: str | None = None) -> dict:
        repos = self.storage.read_list(self.repos_file)
        if workspace_id:
            repos = [r for r in repos if r.get("workspace_id") in (None, workspace_id) or r.get("is_sample")]
        return {"repositories": repos, "count": len(repos)}

    def repository(self, repo_id: str) -> dict:
        repo = next((r for r in self.storage.read_list(self.repos_file) if r.get("repo_id") == repo_id), None)
        if repo is None:
            raise ValueError("Repository not found")
        return repo

    def activity(self, repo_id: str) -> dict:
        repo = self.repository(repo_id)
        return {"repo_id": repo_id, "name": repo.get("name"), "activity": repo.get("recent_activity", [])}

    def context(self, repo_id: str) -> dict:
        repo = self.repository(repo_id)
        return {
            "repo_id": repo_id,
            "summary": f"{repo.get('name')} ({repo.get('provider')}) — default branch {repo.get('default_branch') or 'unknown'}, "
                       f"{len(repo.get('branches', []))} branch(es). Remote: {repo.get('remote_url_sanitized') or 'none'}.",
            "default_branch": repo.get("default_branch"),
            "branch_count": len(repo.get("branches", [])),
            "note": "Read-only metadata context for the Master Agent; no code or secrets included.",
        }

    def analytics_summary(self) -> dict:
        real = [r for r in self.storage.read_list(self.repos_file) if not r.get("is_sample")]
        return {"git_indexed_repos": len(real)}

    def summary(self) -> dict:
        return self.status()
