from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BLOCKED_PATH_HINTS = (
    ".env",
    "node_modules/",
    "venv/",
    "backend/app/data/",
    "backend/app/uploads/",
    "__pycache__/",
)

VERIFY_COMMANDS = (
    "cd backend && ./venv/bin/pytest",
    "cd frontend && npm run build",
)


class LinearCursorHandoffService:
    """Build Cursor/Codex handoff prompts and on-disk task briefs for Linear issues."""

    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parents[3]

    def build_handoff(
        self,
        issue: dict[str, Any],
        link: dict[str, Any],
        *,
        goal: dict[str, Any] | None = None,
        tasks: list[dict[str, Any]] | None = None,
        write_brief: bool = True,
    ) -> dict[str, Any]:
        identifier = issue.get("identifier") or "LINEAR-ISSUE"
        branch = link.get("branch_name") or f"linear/{identifier.lower()}"
        title = issue.get("title") or identifier
        description = (issue.get("description") or "").strip()
        primary_task = self._primary_task(link, tasks or [])
        task_title = primary_task.get("title") if primary_task else title
        task_description = (primary_task.get("description") if primary_task else description) or description

        cursor_prompt = self._cursor_prompt(identifier, title, task_title, task_description, branch)
        codex_prompt = self._codex_prompt(identifier, title, task_title, task_description, branch)
        brief_markdown = self._brief_markdown(
            identifier=identifier,
            title=title,
            description=description,
            branch=branch,
            issue_url=issue.get("url"),
            goal=goal,
            tasks=tasks or [],
            cursor_prompt=cursor_prompt,
            codex_prompt=codex_prompt,
        )

        brief_path: str | None = None
        if write_brief:
            brief_path = str(self._write_brief(identifier, brief_markdown))

        return {
            "identifier": identifier,
            "issue_id": issue.get("id") or link.get("linear_issue_id"),
            "branch": branch,
            "checkout_command": f"git fetch origin && git checkout {branch}",
            "cursor_prompt": cursor_prompt,
            "codex_prompt": codex_prompt,
            "brief_path": brief_path,
            "verify_commands": list(VERIFY_COMMANDS),
            "verify_api": f"/api/linear/issues/{issue.get('id') or link.get('linear_issue_id')}/cursor-verify",
            "worker_mode": "cursor_codex",
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def _primary_task(self, link: dict[str, Any], tasks: list[dict[str, Any]]) -> dict[str, Any] | None:
        task_id = link.get("task_id")
        if task_id:
            match = next((task for task in tasks if task.get("task_id") == task_id), None)
            if match:
                return match
        return tasks[0] if tasks else None

    def _cursor_prompt(
        self,
        identifier: str,
        title: str,
        task_title: str,
        task_description: str,
        branch: str,
    ) -> str:
        blocked = ", ".join(f"`{item}`" for item in BLOCKED_PATH_HINTS)
        return (
            f"You are working on Linear issue **{identifier}**: {title}\n\n"
            f"## Task\n{task_title}\n\n"
            f"{task_description}\n\n"
            f"## Repo rules\n"
            f"- Work on branch `{branch}` (checkout if needed)\n"
            f"- Match existing EvolveAgent AI conventions (FastAPI backend + React frontend)\n"
            f"- Do NOT edit {blocked}\n"
            f"- Run verification before finishing:\n"
            f"  - `cd backend && ./venv/bin/pytest`\n"
            f"  - `cd frontend && npm run build`\n"
            f"- Commit with message: `Linear {identifier}: <short summary>`\n\n"
            f"## When done\n"
            f"Summarize what changed, why, and how it was tested. "
            f"Then use EvolveAgent **Verify Cursor work** or Mission Control **Mark done** to close Linear."
        )

    def _codex_prompt(
        self,
        identifier: str,
        title: str,
        task_title: str,
        task_description: str,
        branch: str,
    ) -> str:
        return (
            f"Implement Linear {identifier} — {title}\n\n"
            f"Task: {task_title}\n"
            f"{task_description}\n\n"
            f"Checkout branch: git checkout {branch}\n"
            f"Project: EvolveAgent AI (FastAPI + React).\n"
            f"Avoid secrets, .env, node_modules, venv, and backend/app/data/.\n"
            f"Verify with pytest and npm run build before completing."
        )

    def _brief_markdown(
        self,
        *,
        identifier: str,
        title: str,
        description: str,
        branch: str,
        issue_url: str | None,
        goal: dict[str, Any] | None,
        tasks: list[dict[str, Any]],
        cursor_prompt: str,
        codex_prompt: str,
    ) -> str:
        lines = [
            f"# Linear handoff — {identifier}",
            "",
            f"**Title:** {title}",
            f"**Branch:** `{branch}`",
            f"**Linear:** {issue_url or 'n/a'}",
            "",
            "## Description",
            description or "_No description provided._",
            "",
        ]
        if goal:
            lines.extend(
                [
                    "## Mission Control goal",
                    f"- Goal: {goal.get('title')}",
                    f"- Goal ID: `{goal.get('goal_id')}`",
                    "",
                ]
            )
        if tasks:
            lines.append("## Subtasks")
            for task in tasks[:8]:
                lines.append(f"- [{task.get('status', 'pending')}] {task.get('title')}")
            lines.append("")

        lines.extend(
            [
                "## Checkout",
                "```bash",
                f"git fetch origin",
                f"git checkout {branch}",
                "```",
                "",
                "## Cursor Agent prompt",
                "```markdown",
                cursor_prompt,
                "```",
                "",
                "## Codex prompt",
                "```text",
                codex_prompt,
                "```",
                "",
                "## Verify locally",
                "```bash",
                "cd backend && ./venv/bin/pytest",
                "cd frontend && npm run build",
                "```",
                "",
                "## Close the loop",
                "- EvolveAgent UI → Linear panel → **Verify Cursor work**",
                "- Or Mission Control → **Mark done** (auto-closes Linear with summary)",
                "",
            ]
        )
        return "\n".join(lines)

    def _write_brief(self, identifier: str, markdown: str) -> Path:
        directory = self.project_root / "docs" / "linear-handoffs"
        directory.mkdir(parents=True, exist_ok=True)
        safe_name = identifier.lower().replace(" ", "-")
        path = directory / f"{safe_name}.md"
        path.write_text(markdown, encoding="utf-8")
        return path
