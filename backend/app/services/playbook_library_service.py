from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

STEP_TYPES = ["plan", "note", "approval_required"]


class PlaybookLibraryService:
    """v53.0 Playbook Library.

    Reusable, governed multi-step **playbooks** — saved sequences of planned
    actions users can re-run. Running a playbook is **planning-first**: each step
    is drafted, informational, or (for risky steps) held for explicit approval —
    nothing is executed. A run produces a per-step outcome record. Playbook
    creation and runs are governance-logged.
    """

    playbooks_file = "playbooks.json"
    runs_file = "playbook_runs.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _enum(self, value, allowed: list[str], default: str) -> str:
        candidate = str(value or "").strip().lower()
        return candidate if candidate in allowed else default

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="playbook_library",
                agent_name="Playbook Library",
                action_type=action_type,
                tool_used="PlaybookLibraryService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=4,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Playbooks
    # ------------------------------------------------------------------
    def create_playbook(self, data: dict) -> dict:
        data = data or {}
        steps = []
        for i, step in enumerate((data.get("steps") or [])[:50]):
            steps.append({
                "step_index": i,
                "title": self._clean(step.get("title"), 200) or f"Step {i + 1}",
                "step_type": self._enum(step.get("step_type"), STEP_TYPES, "plan"),
                "detail": self._clean(step.get("detail"), 2000),
            })
        playbook = {
            "playbook_id": str(uuid4()),
            "name": self._clean(data.get("name"), 160) or "Playbook",
            "description": self._clean(data.get("description"), 1000),
            "steps": steps,
            "step_count": len(steps),
            "created_at": self._now(),
        }
        self.storage.append(self.playbooks_file, playbook)
        self._log("playbook_created", f"Created playbook '{playbook['name']}' ({len(steps)} step(s)).")
        return playbook

    def list_playbooks(self) -> list[dict]:
        return self.storage.read_list(self.playbooks_file)

    def get_playbook(self, playbook_id: str) -> dict | None:
        return next((p for p in self.list_playbooks() if p.get("playbook_id") == playbook_id), None)

    # ------------------------------------------------------------------
    # Runs (planning-first — nothing is executed)
    # ------------------------------------------------------------------
    def run_playbook(self, playbook_id: str) -> dict:
        playbook = self.get_playbook(playbook_id)
        if playbook is None:
            raise ValueError("Playbook not found")
        step_results = []
        for step in playbook.get("steps", []):
            step_type = step.get("step_type")
            if step_type == "approval_required":
                status = "approval_required"
                note = "Risky step — held for explicit human approval; not executed."
            elif step_type == "note":
                status = "noted"
                note = "Informational step."
            else:  # plan
                status = "planned"
                note = "Planned (mock) — no real action performed."
            step_results.append({
                "step_index": step.get("step_index"),
                "title": step.get("title"),
                "step_type": step_type,
                "status": status,
                "note": note,
            })
        run = {
            "run_id": str(uuid4()),
            "playbook_id": playbook_id,
            "playbook_name": playbook.get("name"),
            "steps": step_results,
            "step_count": len(step_results),
            "approval_required_count": sum(1 for s in step_results if s["status"] == "approval_required"),
            "planned_count": sum(1 for s in step_results if s["status"] == "planned"),
            "executed": False,
            "note": "Planning-first run — steps are planned or held for approval; nothing is executed.",
            "created_at": self._now(),
        }
        self.storage.append(self.runs_file, run)
        self._log("playbook_run", f"Ran (planning-first) playbook {playbook_id}: {run['planned_count']} planned, {run['approval_required_count']} need approval.")
        return run

    def list_runs(self, playbook_id: str | None = None, limit: int = 50) -> list[dict]:
        runs = self.storage.read_list(self.runs_file)
        if playbook_id:
            runs = [r for r in runs if r.get("playbook_id") == playbook_id]
        return list(reversed(runs[-limit:]))

    # ------------------------------------------------------------------
    # Summary + analytics
    # ------------------------------------------------------------------
    def summary(self) -> dict:
        return {
            "playbook_count": len(self.list_playbooks()),
            "run_count": len(self.storage.read_list(self.runs_file)),
            "note": "Playbooks run planning-first — nothing is executed; risky steps require approval.",
        }

    def analytics_summary(self) -> dict:
        return {
            "playbooks_total": len(self.list_playbooks()),
            "playbook_runs": len(self.storage.read_list(self.runs_file)),
        }
