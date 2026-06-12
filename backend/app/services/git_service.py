from __future__ import annotations

import subprocess
from pathlib import Path

from app.config import settings

BLOCKED_PATH_PARTS = {
    ".env",
    ".git",
    "node_modules",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "uploads",
    "dist",
    "backend/app/data/",
    "backend/app/uploads/",
    "backend/.logs/",
}


class GitService:
    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parents[3]

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=False,
        )

    def git_status(self) -> dict[str, str | bool]:
        result = self._run("status", "--porcelain")
        return {
            "clean": result.returncode == 0 and not result.stdout.strip(),
            "output": result.stdout.strip(),
            "success": result.returncode == 0,
        }

    def current_branch(self) -> str:
        result = self._run("rev-parse", "--abbrev-ref", "HEAD")
        return result.stdout.strip() if result.returncode == 0 else settings.git_default_branch

    def create_branch(self, branch_name: str) -> dict[str, str | bool]:
        safe_name = branch_name.replace(" ", "-").lower()
        checkout = self._run("checkout", "-b", safe_name)
        if checkout.returncode != 0 and "already exists" in checkout.stderr.lower():
            checkout = self._run("checkout", safe_name)
        return {
            "branch": safe_name,
            "success": checkout.returncode == 0,
            "message": checkout.stderr.strip() or checkout.stdout.strip(),
        }

    def checkout_branch(self, branch_name: str) -> dict[str, str | bool]:
        safe_name = branch_name.replace(" ", "-").lower()
        checkout = self._run("checkout", safe_name)
        return {
            "branch": safe_name,
            "success": checkout.returncode == 0,
            "message": checkout.stderr.strip() or checkout.stdout.strip(),
        }

    def list_changed_files(self) -> list[str]:
        status = self.git_status()
        changed: list[str] = []
        for line in str(status.get("output") or "").splitlines():
            if len(line) < 4:
                continue
            changed.append(line[3:].strip())
        return changed

    def is_safe_path(self, path: str) -> bool:
        normalized = path.replace("\\", "/").strip()
        if not normalized or normalized.startswith("../"):
            return False
        for blocked in BLOCKED_PATH_PARTS:
            if blocked in normalized:
                return False
        return True

    def add_safe_files(self) -> dict[str, list[str] | bool | str]:
        status = self.git_status()
        if status["clean"]:
            return {"success": True, "staged_files": [], "excluded_files": [], "message": "Nothing to stage"}

        staged: list[str] = []
        excluded: list[str] = []
        for line in str(status["output"]).splitlines():
            if len(line) < 4:
                continue
            path = line[3:].strip()
            if self.is_safe_path(path):
                add_result = self._run("add", "--", path)
                if add_result.returncode == 0:
                    staged.append(path)
            else:
                excluded.append(path)

        return {
            "success": True,
            "staged_files": staged,
            "excluded_files": excluded,
            "message": f"Staged {len(staged)} safe file(s)",
        }

    def commit(self, message: str) -> dict[str, str | bool]:
        result = self._run("commit", "-m", message)
        return {
            "success": result.returncode == 0,
            "message": result.stdout.strip() or result.stderr.strip(),
            "commit_hash": self.latest_commit_hash() if result.returncode == 0 else "",
        }

    def push(self, remote: str | None = None, branch: str | None = None) -> dict[str, str | bool]:
        if not settings.auto_git_push:
            return {
                "success": False,
                "skipped": True,
                "message": "Push skipped because AUTO_GIT_PUSH=false",
            }
        remote_name = remote or settings.git_remote_name
        branch_name = branch or self.current_branch()
        result = self._run("push", "-u", remote_name, branch_name)
        return {
            "success": result.returncode == 0,
            "skipped": False,
            "message": result.stdout.strip() or result.stderr.strip(),
            "remote": remote_name,
            "branch": branch_name,
        }

    def latest_commit_hash(self) -> str:
        result = self._run("rev-parse", "--short", "HEAD")
        return result.stdout.strip() if result.returncode == 0 else ""

    def recent_commits(self, branch: str | None = None, limit: int = 5) -> list[dict[str, str]]:
        args = ["log", f"-{max(limit, 1)}", "--pretty=format:%h|%s"]
        if branch:
            args.append(branch)
        result = self._run(*args)
        if result.returncode != 0:
            return []
        commits: list[dict[str, str]] = []
        for line in result.stdout.splitlines():
            if "|" not in line:
                continue
            commit_hash, _, message = line.partition("|")
            commits.append({"hash": commit_hash.strip(), "message": message.strip()})
        return commits

    def diff_summary(self) -> str:
        result = self._run("diff", "--stat")
        return result.stdout.strip() if result.returncode == 0 else ""
