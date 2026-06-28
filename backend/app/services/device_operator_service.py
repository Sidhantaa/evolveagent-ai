from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

PERMISSION_LEVELS = [
    "suggest_only",
    "read_screen_only",
    "tap_type_with_confirmation",
    "auto_safe_actions",
    "blocked",
]

# Action types that ALWAYS require explicit human approval (never auto-run).
_APPROVAL_ACTIONS = {
    "send_message",
    "send_email",
    "pay",
    "delete_file",
    "share_private_data",
    "change_password",
    "call",
    "post_online",
    "submit_form",
    "tap",
    "type",
    "send",
    "delete",
    "share",
}
# Action types that are blocked by default (dangerous, irreversible, or sensitive).
_BLOCKED_ACTIONS = {
    "pay",
    "delete_file",
    "change_password",
    "share_private_data",
    "factory_reset",
    "wipe",
}
# Keyword → planned action-type mapping for command interpretation (mock/local).
_COMMAND_KEYWORDS = {
    "read": "read_screen",
    "open": "open_app",
    "search": "search",
    "scroll": "scroll",
    "tap": "tap",
    "click": "tap",
    "type": "type",
    "write": "type",
    "send": "send_message",
    "email": "send_email",
    "pay": "pay",
    "delete": "delete_file",
    "share": "share_private_data",
    "password": "change_password",
    "call": "call",
    "post": "post_online",
    "submit": "submit_form",
}


class DeviceOperatorService:
    """v26.0 Personal Device Operator / Phone Autopilot (mock, planning-first).

    Produces *planned* phone/device action sequences from voice/text commands and
    mock screen input. It NEVER performs real device automation: every action is a
    plan that is either suggested, read-only, confirmation-gated, or blocked. Risky
    actions (send/pay/delete/share/password/call/post/submit) require explicit
    confirmation, and dangerous actions are blocked by default. All activity is
    audited and governance-logged.
    """

    sessions_file = "device_operator_sessions.json"
    actions_file = "device_operator_actions.json"
    audit_file = "device_operator_audit.json"

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

    def _audit(self, event_type: str, ref_id: str, detail: str, blocked: bool = False) -> None:
        self.storage.append(
            self.audit_file,
            {
                "audit_id": str(uuid4()),
                "event_type": event_type,
                "ref_id": ref_id,
                "detail": detail,
                "blocked": blocked,
                "created_at": self._now(),
            },
        )

    def _log(self, action_type: str, reason: str, blocked: bool = False) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="device_operator",
                agent_name="Device Operator",
                action_type=action_type,
                tool_used="DeviceOperatorService",
                permission_level="read_only",
                approved=not blocked,
                blocked=blocked,
                risk_score=60 if blocked else 10,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------
    def list_sessions(self) -> list[dict]:
        return self.storage.read_list(self.sessions_file)

    def get_session(self, session_id: str) -> dict | None:
        return next((s for s in self.storage.read_list(self.sessions_file) if s.get("session_id") == session_id), None)

    def create_session(self, data: dict) -> dict:
        session = {
            "session_id": str(uuid4()),
            "workspace_id": data.get("workspace_id"),
            "device_label": self._clean(data.get("device_label"), 120) or "Personal phone (mock)",
            "permission_level": self._enum(data.get("permission_level"), PERMISSION_LEVELS, "suggest_only"),
            "status": "active",
            "mock_mode": True,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.sessions_file, session)
        self._audit("session_created", session["session_id"], f"Device session '{session['device_label']}' at {session['permission_level']}.")
        self._log("device_session_created", f"Created device operator session {session['session_id']} (mock).")
        return session

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------
    def _classify(self, action_type: str, permission_level: str) -> dict:
        blocked = action_type in _BLOCKED_ACTIONS or permission_level == "blocked"
        requires_confirmation = action_type in _APPROVAL_ACTIONS
        if blocked:
            risk, status = "high", "blocked"
        elif requires_confirmation:
            # Read-only/suggest sessions can plan but not auto-run; only auto_safe_actions could
            # auto-run *safe* actions — risky ones still need confirmation.
            risk, status = "high", "needs_confirmation"
        elif action_type in {"read_screen", "search", "scroll", "open_app"}:
            risk, status = "low", ("planned" if permission_level != "suggest_only" else "suggested")
        else:
            risk, status = "medium", "needs_confirmation"
        return {"risk_level": risk, "status": status, "requires_confirmation": requires_confirmation, "blocked": blocked}

    def _interpret(self, command: str) -> str:
        lowered = command.lower()
        for keyword, action in _COMMAND_KEYWORDS.items():
            if keyword in lowered:
                return action
        return "read_screen"

    def plan(self, session_id: str, command: str = "", screen_text: str = "") -> dict:
        session = self.get_session(session_id)
        if session is None:
            raise ValueError("Session not found")
        permission_level = session.get("permission_level", "suggest_only")

        planned_actions: list[dict] = []

        # Read-screen mode: summarize provided mock screen text (no real capture).
        if screen_text:
            classification = self._classify("read_screen", permission_level)
            action = self._store_action(session_id, "read_screen", f"Read screen: {screen_text[:160]}", classification, permission_level)
            planned_actions.append(action)

        if command:
            action_type = self._interpret(command)
            classification = self._classify(action_type, permission_level)
            description = f"Planned '{action_type}' for command: {command[:160]}"
            action = self._store_action(session_id, action_type, description, classification, permission_level)
            planned_actions.append(action)

        if not planned_actions:
            classification = self._classify("read_screen", permission_level)
            planned_actions.append(self._store_action(session_id, "read_screen", "No command/screen provided — defaulting to read-screen suggestion.", classification, permission_level))

        any_blocked = any(a["blocked"] for a in planned_actions)
        self._log(
            "device_plan_created",
            f"Planned {len(planned_actions)} action(s) for session {session_id}.",
            blocked=any_blocked,
        )
        return {
            "session_id": session_id,
            "permission_level": permission_level,
            "planned_actions": planned_actions,
            "mock_mode": True,
            "note": "Planning only — no real device action is performed. Risky actions require confirmation; dangerous actions are blocked.",
        }

    def _store_action(self, session_id: str, action_type: str, description: str, classification: dict, permission_level: str) -> dict:
        action = {
            "action_id": str(uuid4()),
            "session_id": session_id,
            "action_type": action_type,
            "description": description,
            "permission_level": permission_level,
            "risk_level": classification["risk_level"],
            "requires_confirmation": classification["requires_confirmation"],
            "blocked": classification["blocked"],
            "status": classification["status"],
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.actions_file, action)
        self._audit(
            "action_planned",
            action["action_id"],
            f"{action_type} → {classification['status']} (risk {classification['risk_level']}).",
            blocked=classification["blocked"],
        )
        return action

    # ------------------------------------------------------------------
    # Confirmation
    # ------------------------------------------------------------------
    def confirm_action(self, session_id: str, action_id: str, approve: bool) -> dict:
        actions = self.storage.read_list(self.actions_file)
        action = next((a for a in actions if a.get("action_id") == action_id and a.get("session_id") == session_id), None)
        if action is None:
            raise ValueError("Action not found")
        if action.get("blocked"):
            # Blocked actions cannot be approved through this path.
            action["status"] = "blocked"
            action["updated_at"] = self._now()
            self.storage.write_list(self.actions_file, actions)
            self._audit("action_confirm_denied", action_id, "Attempt to confirm a blocked action was denied.", blocked=True)
            self._log("device_action_blocked", f"Confirmation denied for blocked action {action_id}.", blocked=True)
            return action
        action["status"] = "approved_mock" if approve else "rejected"
        action["updated_at"] = self._now()
        self.storage.write_list(self.actions_file, actions)
        self._audit(
            "action_confirmed" if approve else "action_rejected",
            action_id,
            f"Action {action.get('action_type')} {'approved (mock — not executed)' if approve else 'rejected'}.",
        )
        self._log("device_action_decided", f"Action {action_id} {'approved (mock)' if approve else 'rejected'}.")
        return action

    # ------------------------------------------------------------------
    # Audit + dashboard
    # ------------------------------------------------------------------
    def audit_log(self, limit: int = 50) -> list[dict]:
        return list(reversed(self.storage.read_list(self.audit_file)[-limit:]))

    def dashboard(self) -> dict:
        sessions = self.storage.read_list(self.sessions_file)
        actions = self.storage.read_list(self.actions_file)
        return {
            "total_sessions": len(sessions),
            "active_sessions": sum(1 for s in sessions if s.get("status") == "active"),
            "total_actions": len(actions),
            "blocked_actions": sum(1 for a in actions if a.get("blocked")),
            "actions_awaiting_confirmation": sum(1 for a in actions if a.get("status") == "needs_confirmation"),
            "approved_mock_actions": sum(1 for a in actions if a.get("status") == "approved_mock"),
            "audit_event_count": len(self.storage.read_list(self.audit_file)),
            "permission_levels": PERMISSION_LEVELS,
            "mock_mode": True,
            "safety_note": "Mock/planning-first — no real phone automation. Send/pay/delete/share/password/call/post/submit require approval; dangerous actions blocked.",
        }
