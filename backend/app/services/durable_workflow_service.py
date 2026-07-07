from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Words that mark a step as risky — it can never auto-run; the workflow halts for approval.
RISKY_ACTIONS = ["send", "email", "pay", "purchase", "delete", "deploy", "post", "publish", "transfer", "charge", "refund"]

# Whitelisted INTERNAL, LOCAL, reversible effects a step may actually perform
# (once approved). These write only to the app's own effect store — never any
# external service. Anything not in this set is simulated, not executed.
WHITELISTED_ACTIONS = {"create_task", "create_note", "notify"}

TERMINAL = {"completed", "cancelled", "failed"}

# v120: which run statuses are interesting enough to emit as system events
# (chaining points for the event bus). Transitional states ("running", "paused")
# are not emitted -- they're reversible/in-progress, not occurrences.
_EMITTABLE_STATUSES = {"completed", "waiting_approval", "cancelled"}

# Starter durable workflows. Each step: name + optional action verb; risk is derived.
STARTER_TEMPLATES = [
    {"key": "weekly_report", "name": "Weekly Status Report",
     "steps": [
         {"name": "Collect this week's activity"},
         {"name": "Summarize progress and blockers"},
         {"name": "Draft the report"},
         {"name": "Send report to stakeholders", "action": "send"},
     ]},
    {"key": "inbox_triage", "name": "Inbox Triage",
     "steps": [
         {"name": "Scan unread messages"},
         {"name": "Classify by priority"},
         {"name": "Draft suggested replies"},
         {"name": "Send approved replies", "action": "send"},
     ]},
    {"key": "research_brief", "name": "Research Brief",
     "steps": [
         {"name": "Gather sources"},
         {"name": "Compare and synthesize findings"},
         {"name": "Write the brief"},
     ]},
    {"key": "daily_capture", "name": "Daily Capture",
     "steps": [
         {"name": "Review today's notes"},
         {"name": "Create a follow-up task", "action_type": "create_task",
          "action_params": {"title": "Follow up from Daily Capture"}},
         {"name": "Notify me it's done", "action_type": "notify",
          "action_params": {"message": "Daily Capture complete"}},
     ]},
    {"key": "release_checklist", "name": "Release Checklist",
     "steps": [
         {"name": "Run the test suite"},
         {"name": "Assemble the changelog"},
         {"name": "Deploy to production", "action": "deploy"},
         {"name": "Announce the release", "action": "publish"},
     ]},
]


def _is_risky(step: dict) -> bool:
    text = f"{step.get('action', '')} {step.get('name', '')}".lower()
    return any(v in text for v in RISKY_ACTIONS)


class DurableWorkflowService:
    """Phase 6 — durable, resumable, approval-gated workflows (mock-safe).

    A workflow is an ordered list of steps. A **run** executes them one at a time,
    persisting its state (a checkpoint: cursor + per-step status/output) to storage
    after every step — so a run survives restarts and can be **resumed** from where
    it left off. Execution is **deterministic and simulated**: no step performs any
    real action. Any step that looks risky (send/deploy/pay/delete/publish/…) is
    marked ``requires_approval`` and the run **halts** at ``waiting_approval`` until
    a human approves it — it can never auto-run. Governance-logged throughout.
    """

    defs_file = "durable_workflow_defs.json"
    runs_file = "durable_workflow_runs.json"
    effects_file = "durable_workflow_effects.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, event_bus=None, agent_scheduler=None):
        self.storage = storage
        self.governance = governance_service
        # v120: optional EventBusService — lets a run's completion/approval-halt/
        # cancellation chain into another action. Emitting is best-effort and must
        # never break the workflow engine itself.
        self.event_bus = event_bus
        # v120: optional AgentSchedulerService — every run started here becomes a
        # real, observable job in the (previously driver-less) job queue. This is
        # the ONLY place runs are created, so wiring it here covers every entry
        # point (direct API, a firing schedule, or an event-bus dispatch) for free.
        self.agent_scheduler = agent_scheduler

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _emit_status_event(self, run: dict) -> None:
        if self.event_bus is None or run.get("status") not in _EMITTABLE_STATUSES:
            return
        try:
            self.event_bus.emit(f"workflow.{run['status']}", {
                "run_id": run.get("run_id"), "definition_id": run.get("definition_id"), "name": run.get("name"),
            }, source="durable_workflow")
        except Exception:
            pass

    def _create_job_for_run(self, run: dict) -> None:
        """Best-effort: register this run as an observable job. Never blocks the run."""
        if self.agent_scheduler is None:
            return
        try:
            job = self.agent_scheduler.create_job({
                "job_type": "workflow",
                "title": f"Workflow run: {run['name']}"[:160],
                "payload": {"run_id": run["run_id"], "definition_id": run.get("definition_id") or ""},
            })
            run["job_id"] = job["job_id"]
            self.agent_scheduler.heartbeat(job["job_id"])  # queued -> running: we're executing it now
        except Exception:
            pass

    def _sync_job_status(self, run: dict) -> None:
        """Best-effort: reflect this run's status onto its linked job, if any."""
        job_id = run.get("job_id")
        if self.agent_scheduler is None or not job_id:
            return
        try:
            status = run.get("status")
            if status == "completed":
                self.agent_scheduler.complete(job_id, result_summary=f"Workflow '{run['name']}' completed.")
            elif status == "waiting_approval":
                self.agent_scheduler.pause(job_id, reason="Waiting for human approval on a risky step.")
            elif status == "cancelled":
                self.agent_scheduler.cancel(job_id, reason="Workflow run was cancelled.")
        except Exception:
            pass

    def _log(self, action_type: str, reason: str, risk: int = 1, approved: bool = True) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="durable_workflow",
                agent_name="Durable Workflows",
                action_type=action_type,
                tool_used="DurableWorkflowService",
                permission_level="read_only",
                approved=approved,
                blocked=False,
                risk_score=risk,
                reason=reason,
            )
        )

    # -- templates & definitions --------------------------------------------
    def templates(self) -> dict:
        return {"templates": STARTER_TEMPLATES, "count": len(STARTER_TEMPLATES)}

    @staticmethod
    def _build_steps(raw_steps: list[dict]) -> list[dict]:
        steps = []
        for i, s in enumerate(raw_steps or []):
            name = str(s.get("name") or f"Step {i + 1}")[:200]
            action = str(s.get("action") or "")[:60]
            step = {"name": name, "action": action}
            # A whitelisted internal action makes the step perform a REAL local
            # effect on approval; such steps are always approval-gated.
            action_type = str(s.get("action_type") or "")[:40]
            real = action_type in WHITELISTED_ACTIONS
            params = s.get("action_params") if isinstance(s.get("action_params"), dict) else {}
            steps.append({
                "id": str(uuid4()),
                "name": name,
                "action": action,
                "action_type": action_type if real else "",
                "action_params": {str(k)[:40]: str(v)[:200] for k, v in list(params.items())[:10]} if real else {},
                "requires_approval": _is_risky(step) or real,
                "status": "pending",
                "output": "",
                "started_at": None,
                "finished_at": None,
            })
        return steps

    def _execute_action(self, run: dict, step: dict) -> str:
        """Perform a whitelisted internal effect and record it. Local + reversible."""
        action_type = step.get("action_type") or ""
        params = step.get("action_params") or {}
        effect = {
            "effect_id": str(uuid4()),
            "run_id": run["run_id"],
            "step_id": step["id"],
            "action_type": action_type,
            "params": params,
            "created_at": self._now(),
        }
        self.storage.append(self.effects_file, effect)
        self._log("workflow_effect_executed", f"Executed internal action '{action_type}' in run '{run['name']}'", risk=3)
        label = params.get("title") or params.get("message") or action_type
        return f"[executed] {action_type}: {label}"

    def create_definition(self, data: dict) -> dict:
        data = data or {}
        raw = data.get("steps")
        template_key = data.get("template")
        name = data.get("name")
        if template_key and not raw:
            tpl = next((t for t in STARTER_TEMPLATES if t["key"] == template_key), None)
            if not tpl:
                raise ValueError(f"Unknown template: {template_key}")
            raw = tpl["steps"]
            name = name or tpl["name"]
        steps = self._build_steps(raw or [])
        if not steps:
            raise ValueError("A workflow needs at least one step")
        definition = {
            "definition_id": str(uuid4()),
            "name": str(name or "Untitled Workflow")[:120],
            "steps": steps,
            "created_at": self._now(),
        }
        self.storage.append(self.defs_file, definition)
        self._log("workflow_defined", f"Defined workflow '{definition['name']}' with {len(steps)} steps")
        return definition

    def list_definitions(self) -> dict:
        defs = self.storage.read_list(self.defs_file)
        return {"definitions": defs, "count": len(defs)}

    # -- runs ----------------------------------------------------------------
    def _get_run(self, run_id: str) -> tuple[list[dict], int, dict]:
        runs = self.storage.read_list(self.runs_file)
        for i, r in enumerate(runs):
            if r.get("run_id") == run_id:
                return runs, i, r
        raise ValueError(f"Run not found: {run_id}")

    def _save_run(self, runs: list[dict], idx: int, run: dict) -> None:
        run["updated_at"] = self._now()
        # Durable checkpoint after every state change.
        run.setdefault("checkpoints", [])
        run["checkpoints"].append({"cursor": run["cursor"], "status": run["status"], "at": run["updated_at"]})
        run["checkpoints"] = run["checkpoints"][-25:]
        runs[idx] = run
        self.storage.write_list(self.runs_file, runs)

    def start_run(self, data: dict) -> dict:
        data = data or {}
        definition_id = data.get("definition_id")
        if definition_id:
            definition = next((d for d in self.storage.read_list(self.defs_file) if d.get("definition_id") == definition_id), None)
            if not definition:
                raise ValueError(f"Definition not found: {definition_id}")
            steps = self._build_steps([
                {"name": s["name"], "action": s.get("action", ""),
                 "action_type": s.get("action_type", ""), "action_params": s.get("action_params", {})}
                for s in definition["steps"]
            ])
            name = definition["name"]
        else:
            steps = self._build_steps(data.get("steps") or [])
            name = data.get("name") or "Ad-hoc Workflow"
        if not steps:
            raise ValueError("A run needs at least one step (definition_id or steps)")
        run = {
            "run_id": str(uuid4()),
            "definition_id": definition_id,
            "name": str(name)[:120],
            "status": "running",
            "cursor": 0,
            "steps": steps,
            "inputs": {str(k)[:40]: str(v)[:200] for k, v in list((data.get("inputs") or {}).items())[:20]},
            "created_at": self._now(),
            "updated_at": self._now(),
            "checkpoints": [],
        }
        self._create_job_for_run(run)  # sets run["job_id"] if agent_scheduler is wired
        runs = self.storage.read_list(self.runs_file)
        runs.append(run)
        self.storage.write_list(self.runs_file, runs)
        self._log("workflow_started", f"Started run '{run['name']}' ({len(steps)} steps)")
        # Advance immediately up to the first approval gate.
        return self.advance_run(run["run_id"])

    def _advance_in_place(self, run: dict) -> dict:
        """Process pending steps until an approval gate, completion, or terminal state."""
        if run["status"] in TERMINAL or run["status"] == "paused":
            return run
        steps = run["steps"]
        while run["cursor"] < len(steps):
            step = steps[run["cursor"]]
            if step["status"] == "done" or step["status"] == "skipped":
                run["cursor"] += 1
                continue
            if step["requires_approval"] and step["status"] != "approved":
                step["status"] = "waiting_approval"
                step["started_at"] = step["started_at"] or self._now()
                run["status"] = "waiting_approval"
                return run
            # Safe step (or already-approved step): simulate execution.
            step["started_at"] = step["started_at"] or self._now()
            step["status"] = "done"
            step["output"] = f"[simulated] {step['name']} completed"
            step["finished_at"] = self._now()
            run["cursor"] += 1
        run["status"] = "completed"
        return run

    def advance_run(self, run_id: str) -> dict:
        runs, idx, run = self._get_run(run_id)
        if run["status"] == "waiting_approval":
            return run  # blocked until approval
        if run["status"] in TERMINAL:
            return run
        if run["status"] == "paused":
            raise ValueError("Run is paused — resume it first")
        run = self._advance_in_place(run)
        self._save_run(runs, idx, run)
        if run["status"] == "completed":
            self._log("workflow_completed", f"Run '{run['name']}' completed")
        elif run["status"] == "waiting_approval":
            self._log("workflow_awaiting_approval", f"Run '{run['name']}' halted for approval", risk=4, approved=False)
        self._emit_status_event(run)
        self._sync_job_status(run)
        return run

    def approve_step(self, run_id: str, approved: bool = True, note: str = "") -> dict:
        runs, idx, run = self._get_run(run_id)
        if run["status"] != "waiting_approval":
            raise ValueError("Run is not waiting for approval")
        step = run["steps"][run["cursor"]]
        if approved:
            # Whitelisted internal action => perform the REAL local effect.
            # Anything else stays simulated (as before).
            if step.get("action_type") in WHITELISTED_ACTIONS:
                step["output"] = self._execute_action(run, step)
            else:
                step["output"] = f"[approved] {step['name']} executed" + (f" — {note}" if note else "")
            step["finished_at"] = self._now()
            step["status"] = "done"
            run["cursor"] += 1
            run["status"] = "running"
            self._log("workflow_step_approved", f"Approved '{step['name']}' in run '{run['name']}'", risk=4)
            run = self._advance_in_place(run)
        else:
            step["status"] = "skipped"
            step["output"] = f"[rejected] {step['name']} skipped" + (f" — {note}" if note else "")
            step["finished_at"] = self._now()
            run["cursor"] += 1
            run["status"] = "running"
            self._log("workflow_step_rejected", f"Rejected '{step['name']}' in run '{run['name']}'")
            run = self._advance_in_place(run)
        self._save_run(runs, idx, run)
        self._emit_status_event(run)
        self._sync_job_status(run)
        return run

    def pause_run(self, run_id: str) -> dict:
        runs, idx, run = self._get_run(run_id)
        if run["status"] in TERMINAL:
            raise ValueError("Run has already finished")
        run["status"] = "paused"
        self._save_run(runs, idx, run)
        self._log("workflow_paused", f"Paused run '{run['name']}'")
        return run

    def resume_run(self, run_id: str) -> dict:
        runs, idx, run = self._get_run(run_id)
        if run["status"] != "paused":
            raise ValueError("Run is not paused")
        run["status"] = "running"
        self._save_run(runs, idx, run)
        self._log("workflow_resumed", f"Resumed run '{run['name']}'")
        return self.advance_run(run_id)

    def cancel_run(self, run_id: str) -> dict:
        runs, idx, run = self._get_run(run_id)
        if run["status"] in TERMINAL:
            return run
        run["status"] = "cancelled"
        self._save_run(runs, idx, run)
        self._log("workflow_cancelled", f"Cancelled run '{run['name']}'")
        self._emit_status_event(run)
        self._sync_job_status(run)
        return run

    def get_run(self, run_id: str) -> dict:
        _, _, run = self._get_run(run_id)
        return run

    def list_runs(self) -> dict:
        runs = self.storage.read_list(self.runs_file)
        runs = sorted(runs, key=lambda r: r.get("updated_at", ""), reverse=True)
        return {"runs": runs, "count": len(runs)}

    def effects(self, run_id: str | None = None, limit: int = 50) -> dict:
        rows = self.storage.read_list(self.effects_file)
        if run_id:
            rows = [e for e in rows if e.get("run_id") == run_id]
        rows = sorted(rows, key=lambda e: e.get("created_at", ""), reverse=True)
        try:
            limit = max(1, min(500, int(limit)))
        except (TypeError, ValueError):
            limit = 50
        return {"effects": rows[:limit], "count": len(rows), "whitelisted_actions": sorted(WHITELISTED_ACTIONS)}

    # -- analytics -----------------------------------------------------------
    def analytics_summary(self) -> dict:
        runs = self.storage.read_list(self.runs_file)
        by_status: dict[str, int] = {}
        for r in runs:
            s = r.get("status", "unknown")
            by_status[s] = by_status.get(s, 0) + 1
        return {
            "durable_workflow_definitions": len(self.storage.read_list(self.defs_file)),
            "durable_workflow_runs": len(runs),
            "durable_workflow_runs_by_status": by_status,
            "durable_workflow_effects": len(self.storage.read_list(self.effects_file)),
        }

    def summary(self) -> dict:
        return {**self.analytics_summary(), "templates": len(STARTER_TEMPLATES)}
