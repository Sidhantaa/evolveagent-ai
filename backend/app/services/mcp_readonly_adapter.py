from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

# ----------------------------------------------------------------------
# v43.0 MCP Read-Only Adapter
#
# Turns the v42 mock executor into a REAL adapter for a tiny allow-list of
# strictly read-only actions — but ONLY when explicitly opted in. It uses the
# Python standard library only: NO shell/subprocess, NO network, NO writes, NO
# deletes, NO secrets returned. Every real path is sandboxed to a project root
# with traversal + absolute-path blocking and a sensitive-name denylist. When
# opt-in is off (default) or an action is not on the allow-list, the adapter
# declines and the caller falls back to the mock executor.
# ----------------------------------------------------------------------

# Opt-in flag — real read-only execution is OFF unless this env var is truthy.
OPT_IN_ENV = "MCP_REAL_READONLY"

# The only actions the adapter will ever execute for real. Everything else -> mock.
REAL_READONLY_ACTIONS = [
    "git_current_branch",
    "git_list_branches",
    "fs_list_directory",
    "fs_file_metadata",
]

# Sensitive path components that are always refused (never listed, read, or stat-ed).
_DENYLIST_SUBSTRINGS = (
    ".env",
    "id_rsa",
    "id_ed25519",
    ".pem",
    ".key",
    ".p12",
    ".keystore",
    "credentials",
    "secret",
    ".git/config",
    ".npmrc",
    ".netrc",
    ".aws",
    ".ssh",
)

_MAX_ENTRIES = 200


class MCPReadOnlyAdapter:
    """Opt-in, sandboxed, read-only executor (stdlib only; no shell/network/writes)."""

    def __init__(self, sandbox_root: str | None = None):
        root = sandbox_root or os.environ.get("MCP_SANDBOX_ROOT") or self._default_root()
        self.root = Path(root).resolve()

    @staticmethod
    def _default_root() -> str:
        # backend/app/services/mcp_readonly_adapter.py -> parents[3] == repo root
        # (parents[2] == backend). The repo root is where .git lives.
        path = Path(__file__).resolve()
        repo_root = path.parents[3] if len(path.parents) > 3 else path.parents[2]
        return str(repo_root)

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    # ------------------------------------------------------------------
    # Capability / status
    # ------------------------------------------------------------------
    def enabled(self) -> bool:
        return str(os.environ.get(OPT_IN_ENV, "")).strip().lower() in ("1", "true", "yes", "on")

    def supports(self, action_name: str) -> bool:
        return action_name in REAL_READONLY_ACTIONS

    def status(self) -> dict:
        return {
            "real_readonly_enabled": self.enabled(),
            "opt_in_env": OPT_IN_ENV,
            "allowed_actions": list(REAL_READONLY_ACTIONS),
            "sandbox_root": str(self.root),
            "capabilities": {
                "shell": False,
                "network": False,
                "writes": False,
                "deletes": False,
                "returns_file_contents": False,
                "returns_secrets": False,
            },
            "note": "Real read-only execution is opt-in and sandboxed. It uses the standard library only — no shell, network, writes, or secrets.",
        }

    # ------------------------------------------------------------------
    # Sandbox helpers
    # ------------------------------------------------------------------
    def _is_sensitive(self, path_text: str) -> bool:
        lowered = path_text.lower()
        return any(token in lowered for token in _DENYLIST_SUBSTRINGS)

    def _safe_resolve(self, relative: str) -> Path | None:
        """Resolve a user-supplied relative path inside the sandbox, or None if unsafe."""
        candidate = str(relative or "").strip()
        if candidate.startswith("/") or candidate.startswith("~") or ".." in Path(candidate).parts:
            return None
        if self._is_sensitive(candidate):
            return None
        resolved = (self.root / candidate).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError:
            return None  # escaped the sandbox
        if self._is_sensitive(str(resolved)):
            return None
        return resolved

    # ------------------------------------------------------------------
    # Execution entry point
    # ------------------------------------------------------------------
    def try_execute(self, connector: dict, action_name: str, payload: dict | None = None) -> dict | None:
        """Return a real read-only result, or None to signal 'fall back to mock'."""
        if not self.enabled() or not self.supports(action_name):
            return None
        payload = payload or {}
        handler = {
            "git_current_branch": self._git_current_branch,
            "git_list_branches": self._git_list_branches,
            "fs_list_directory": self._fs_list_directory,
            "fs_file_metadata": self._fs_file_metadata,
        }[action_name]
        try:
            output, success, message = handler(payload)
        except Exception:  # never leak internals; degrade to a safe refusal
            output, success, message = {}, False, "Read-only action could not be completed safely."
        return {
            "execution_mode": "real_read_only",
            "success": success,
            "output": output,
            "message": message,
            "secrets_used": False,
            "real_call_made": True,
            "shell_used": False,
            "network_used": False,
            "wrote_data": False,
            "note": "Real read-only execution (sandboxed, stdlib only) — no shell, network, writes, or secrets.",
        }

    # ------------------------------------------------------------------
    # Git (pure file reads of .git metadata — no subprocess)
    # ------------------------------------------------------------------
    def _git_dir(self) -> Path | None:
        git_dir = self.root / ".git"
        if git_dir.is_dir():
            return git_dir
        if git_dir.is_file():
            try:
                text = git_dir.read_text(encoding="utf-8", errors="replace").strip()
            except OSError:
                return None
            if text.startswith("gitdir:"):
                target = text.split("gitdir:", 1)[1].strip()
                resolved = Path(target) if Path(target).is_absolute() else (self.root / target)
                resolved = resolved.resolve()
                return resolved if resolved.is_dir() else None
        return None

    @staticmethod
    def _git_common_dir(git_dir: Path) -> Path:
        common_file = git_dir / "commondir"
        if not common_file.is_file():
            return git_dir
        try:
            text = common_file.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            return git_dir
        resolved = Path(text) if Path(text).is_absolute() else (git_dir / text)
        resolved = resolved.resolve()
        return resolved if resolved.is_dir() else git_dir

    def _git_current_branch(self, payload: dict):
        git_dir = self._git_dir()
        if git_dir is None:
            return {}, False, "No .git directory found in the sandbox root."
        head = git_dir / "HEAD"
        if not head.is_file():
            return {}, False, "No .git/HEAD found."
        text = head.read_text(encoding="utf-8", errors="replace").strip()
        if text.startswith("ref:"):
            branch = text.split("refs/heads/", 1)[-1] if "refs/heads/" in text else text.replace("ref:", "").strip()
            return {"branch": branch}, True, "Current branch read from .git/HEAD."
        return {"detached_head": text[:64]}, True, "Detached HEAD."

    def _git_list_branches(self, payload: dict):
        git_dir = self._git_dir()
        if git_dir is None:
            return {}, False, "No .git directory found in the sandbox root."
        heads = self._git_common_dir(git_dir) / "refs" / "heads"
        branches: list[str] = []
        if heads.is_dir():
            for path in sorted(heads.rglob("*")):
                if path.is_file():
                    branches.append(str(path.relative_to(heads)))
                if len(branches) >= _MAX_ENTRIES:
                    break
        return {"branches": branches, "count": len(branches)}, True, "Local branch names read from .git/refs/heads."

    # ------------------------------------------------------------------
    # Filesystem (names / sizes only — never contents)
    # ------------------------------------------------------------------
    def _fs_list_directory(self, payload: dict):
        target = self._safe_resolve(payload.get("path", "."))
        if target is None:
            return {}, False, "Path is outside the sandbox or references a sensitive location."
        if not target.is_dir():
            return {}, False, "Path is not a directory."
        entries = []
        for child in sorted(target.iterdir()):
            name = child.name
            if name.startswith(".") or self._is_sensitive(name):
                continue  # hide dotfiles and sensitive names entirely
            try:
                entries.append({
                    "name": name,
                    "is_dir": child.is_dir(),
                    "size_bytes": child.stat().st_size if child.is_file() else None,
                })
            except OSError:
                continue
            if len(entries) >= _MAX_ENTRIES:
                break
        rel = str(target.relative_to(self.root)) or "."
        return {"path": rel, "entries": entries, "count": len(entries)}, True, "Directory listing (names and sizes only)."

    def _fs_file_metadata(self, payload: dict):
        target = self._safe_resolve(payload.get("path", ""))
        if target is None:
            return {}, False, "Path is outside the sandbox or references a sensitive location."
        if not target.is_file():
            return {}, False, "Path is not a file."
        stat = target.stat()
        rel = str(target.relative_to(self.root))
        return (
            {
                "path": rel,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
                "is_file": True,
            },
            True,
            "File metadata only (no contents returned).",
        )
