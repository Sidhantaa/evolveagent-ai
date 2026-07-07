"""Event Bus (v120) — the "Event system" from the workflow-automation plan.

A local, append-only **event log** plus **subscriptions** that let one occurrence
chain into another action — e.g. "when workflow X completes, start workflow Y",
or "when a schedule fires, notify me". This is real wiring, but it introduces
**no new execution surface**: every dispatched action calls straight into an
already-governed engine (``DurableWorkflowService.start_run`` — still
approval-gated internally; ``ScheduledTasksService.trigger`` — same invariant
from v120 task 1; or a log-only ``notify``, never a real send).

Producers (``DurableWorkflowService``, ``ScheduledTasksService``) hold an
*optional* reference to this bus and call ``emit()`` on their own state
transitions — they don't know or care whether anything is subscribed. With zero
subscriptions configured (the default), events are simply recorded; nothing
downstream ever fires on its own.

**Cycle safety:** dispatching a subscription can itself cause another emit (e.g.
workflow A's completion starts workflow B, which completes and could try to
start A again). A single reentrancy-depth counter on this instance caps the
whole chain at ``MAX_DISPATCH_DEPTH`` — once hit, further dispatch in that chain
is skipped and governance-logged as blocked, rather than recursing forever.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

ACTION_TYPES = ["start_workflow", "trigger_task", "notify"]
MAX_DISPATCH_DEPTH = 3


class EventBusService:
    events_file = "system_events.json"
    subscriptions_file = "event_subscriptions.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, workflows=None, scheduled_tasks=None):
        self.storage = storage
        self.governance = governance_service
        # Optional collaborators used only to DISPATCH subscription actions —
        # both are already-governed engines; nothing new is executed here.
        self.workflows = workflows              # DurableWorkflowService
        self.scheduled_tasks = scheduled_tasks  # ScheduledTasksService
        self._active_depth = 0

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _log(self, action_type: str, reason: str, blocked: bool = False) -> None:
        self.governance.log_event(GovernanceEvent(
            task_type="event_bus", agent_name="Event Bus", action_type=action_type,
            tool_used="EventBusService", permission_level="read_only", approved=not blocked,
            blocked=blocked, risk_score=2, reason=reason,
        ))

    # -- emit / dispatch ---------------------------------------------------------
    def emit(self, event_type: str, payload: dict | None = None, source: str = "system") -> dict:
        event = {
            "event_id": str(uuid4()),
            "event_type": self._clean(event_type, 80),
            "source": self._clean(source, 60) or "system",
            "payload": {str(k)[:40]: str(v)[:200] for k, v in list((payload or {}).items())[:20]},
            "created_at": self._now(),
        }
        self.storage.append(self.events_file, event)
        self._log("event_emitted", f"Emitted '{event['event_type']}' from {event['source']}")

        if self._active_depth >= MAX_DISPATCH_DEPTH:
            self._log("event_dispatch_depth_limit",
                       f"Skipped dispatch for '{event['event_type']}' — max chain depth ({MAX_DISPATCH_DEPTH}) reached",
                       blocked=True)
            return {**event, "dispatched": [], "depth_limited": True}

        dispatched = []
        self._active_depth += 1
        try:
            for sub in self._matching_subscriptions(event["event_type"], event["payload"]):
                dispatched.append(self._dispatch(sub, event))
        finally:
            self._active_depth -= 1
        return {**event, "dispatched": dispatched, "depth_limited": False}

    def _matching_subscriptions(self, event_type: str, payload: dict) -> list[dict]:
        matches = []
        for sub in self.list_subscriptions():
            if not sub.get("enabled", True):
                continue
            if sub.get("event_type") not in (event_type, "*"):
                continue
            filt = sub.get("filter") or {}
            if filt and not all(str(payload.get(k)) == str(v) for k, v in filt.items()):
                continue
            matches.append(sub)
        return matches

    def _dispatch(self, sub: dict, event: dict) -> dict:
        action_type = sub.get("action_type")
        params = sub.get("action_params") or {}
        base = {"subscription_id": sub.get("subscription_id"), "action_type": action_type}
        try:
            if action_type == "start_workflow" and self.workflows is not None:
                result = self.workflows.start_run({"definition_id": params.get("workflow_definition_id")})
                outcome = {**base, "ok": True, "run_id": result.get("run_id"), "status": result.get("status")}
            elif action_type == "trigger_task" and self.scheduled_tasks is not None:
                result = self.scheduled_tasks.trigger(params.get("task_id"))
                outcome = {**base, "ok": True, "run_id": result.get("run_id"), "status": result.get("status")}
            elif action_type == "notify":
                message = self._clean(params.get("message"), 300) or f"Event '{event['event_type']}' occurred"
                self._log("event_notify", message)
                outcome = {**base, "ok": True, "message": message}
            else:
                outcome = {**base, "ok": False, "error": "Unsupported action or collaborator not configured."}
        except Exception as exc:  # noqa: BLE001 — isolate one bad subscription from the rest
            outcome = {**base, "ok": False, "error": str(exc)}
        return outcome

    # -- subscriptions (CRUD) -----------------------------------------------------
    def list_subscriptions(self) -> list[dict]:
        return self.storage.read_list(self.subscriptions_file)

    def get_subscription(self, subscription_id: str) -> dict | None:
        return next((s for s in self.list_subscriptions() if s.get("subscription_id") == subscription_id), None)

    def create_subscription(self, data: dict) -> dict:
        data = data or {}
        action_type = data.get("action_type") if data.get("action_type") in ACTION_TYPES else None
        if not action_type:
            raise ValueError(f"action_type must be one of {ACTION_TYPES}")
        params = data.get("action_params") or {}
        sub = {
            "subscription_id": str(uuid4()),
            "name": self._clean(data.get("name"), 120) or "Subscription",
            "event_type": self._clean(data.get("event_type"), 80) or "*",
            "filter": {str(k)[:40]: str(v)[:120] for k, v in list((data.get("filter") or {}).items())[:10]},
            "action_type": action_type,
            "action_params": {str(k)[:40]: str(v)[:200] for k, v in list(params.items())[:10]},
            "enabled": bool(data.get("enabled", True)),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.subscriptions_file, sub)
        self._log("event_subscription_created", f"Created subscription '{sub['name']}' on '{sub['event_type']}' -> {action_type}")
        return sub

    def update_subscription(self, subscription_id: str, data: dict) -> dict:
        subs = self.list_subscriptions()
        sub = next((s for s in subs if s.get("subscription_id") == subscription_id), None)
        if sub is None:
            raise ValueError("Subscription not found")
        data = data or {}
        if data.get("name") is not None:
            sub["name"] = self._clean(data["name"], 120) or sub["name"]
        if data.get("event_type") is not None:
            sub["event_type"] = self._clean(data["event_type"], 80) or "*"
        if data.get("filter") is not None:
            sub["filter"] = {str(k)[:40]: str(v)[:120] for k, v in list(data["filter"].items())[:10]}
        if data.get("action_type") is not None:
            if data["action_type"] not in ACTION_TYPES:
                raise ValueError(f"action_type must be one of {ACTION_TYPES}")
            sub["action_type"] = data["action_type"]
        if data.get("action_params") is not None:
            sub["action_params"] = {str(k)[:40]: str(v)[:200] for k, v in list(data["action_params"].items())[:10]}
        if data.get("enabled") is not None:
            sub["enabled"] = bool(data["enabled"])
        sub["updated_at"] = self._now()
        self.storage.write_list(self.subscriptions_file, subs)
        self._log("event_subscription_updated", f"Updated subscription {subscription_id} (enabled={sub['enabled']}).")
        return sub

    # -- events (read) -------------------------------------------------------------
    def list_events(self, event_type: str | None = None, limit: int = 50) -> dict:
        rows = self.storage.read_list(self.events_file)
        if event_type:
            rows = [r for r in rows if r.get("event_type") == event_type]
        rows = sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)
        try:
            limit = max(1, min(500, int(limit)))
        except (TypeError, ValueError):
            limit = 50
        return {"events": rows[:limit], "count": len(rows)}

    # -- analytics -------------------------------------------------------------------
    def analytics_summary(self) -> dict:
        return {
            "system_events": len(self.storage.read_list(self.events_file)),
            "event_subscriptions": len(self.list_subscriptions()),
            "event_subscriptions_active": sum(1 for s in self.list_subscriptions() if s.get("enabled", True)),
        }

    def summary(self) -> dict:
        return {
            **self.analytics_summary(),
            "action_types": list(ACTION_TYPES),
            "max_dispatch_depth": MAX_DISPATCH_DEPTH,
            "note": "Zero subscriptions means events are only recorded, never dispatched. Dispatched actions always "
                    "route through the same already-governed engines (workflows/scheduled tasks) — no new execution surface.",
        }
