from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

DEVICE_TYPES = ["phone", "laptop", "desktop", "speaker", "wearable", "other"]
# Companion modes — all require explicit user activation. No background listening.
COMPANION_MODES = ["disabled", "push_to_talk_ready", "local_only_ready"]

SAFETY_RULES = [
    "No microphone audio is recorded.",
    "No wake-word listener runs.",
    "No hardware is accessed — this is a readiness/planning layer only.",
    "The companion always requires explicit user activation; there is no background listening.",
]


class HardwareCompanionService:
    """v39.0 AI Hardware / Always-On Companion (readiness + planning only).

    A device-readiness and session-planning layer. It does NOT record microphone
    audio, run a wake-word listener, or access any hardware. It stores local
    device profiles, companion-mode settings (disabled / push_to_talk_ready /
    local_only_ready), readiness checklists, and session notes. Safety mode always
    requires explicit user activation — no background listening. Stateful actions
    are audited and governance-logged.
    """

    devices_file = "hardware_devices.json"
    sessions_file = "companion_sessions.json"
    settings_file = "wake_mode_settings.json"
    readiness_file = "companion_readiness_checks.json"
    audit_file = "companion_audit.json"

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

    def _audit(self, event: str, ref_id: str, detail: str) -> None:
        self.storage.append(
            self.audit_file,
            {"audit_id": str(uuid4()), "event": event, "ref_id": ref_id, "detail": detail, "created_at": self._now()},
        )

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="hardware_companion",
                agent_name="Hardware Companion",
                action_type=action_type,
                tool_used="HardwareCompanionService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Devices
    # ------------------------------------------------------------------
    def list_devices(self) -> list[dict]:
        return self.storage.read_list(self.devices_file)

    def create_device(self, data: dict) -> dict:
        device = {
            "device_id": str(uuid4()),
            "name": self._clean(data.get("name"), 160) or "Local device",
            "device_type": self._enum(data.get("device_type"), DEVICE_TYPES, "other"),
            "has_mic": bool(data.get("has_mic", False)),
            "has_speaker": bool(data.get("has_speaker", False)),
            "local_processing": bool(data.get("local_processing", False)),
            "registered": True,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.devices_file, device)
        self._audit("device_registered", device["device_id"], f"Registered device profile {device['name']}.")
        self._log("companion_device_created", f"Registered local device profile {device['device_id']}.")
        return device

    def update_device(self, device_id: str, updates: dict) -> dict:
        devices = self.storage.read_list(self.devices_file)
        device = next((d for d in devices if d.get("device_id") == device_id), None)
        if device is None:
            raise ValueError("Device not found")
        if updates.get("name") is not None:
            device["name"] = self._clean(updates["name"], 160) or device["name"]
        if updates.get("device_type") is not None:
            device["device_type"] = self._enum(updates["device_type"], DEVICE_TYPES, device["device_type"])
        for flag in ("has_mic", "has_speaker", "local_processing"):
            if updates.get(flag) is not None:
                device[flag] = bool(updates[flag])
        device["updated_at"] = self._now()
        self.storage.write_list(self.devices_file, devices)
        self._audit("device_updated", device_id, f"Updated device {device_id}.")
        self._log("companion_device_updated", f"Updated device {device_id}.")
        return device

    # ------------------------------------------------------------------
    # Settings (single active)
    # ------------------------------------------------------------------
    def _default_settings(self) -> dict:
        return {
            "companion_mode": "disabled",
            "requires_user_activation": True,
            "background_listening": False,
            "wake_word_listener": False,
            "microphone_recording": False,
            "safety_rules": SAFETY_RULES,
            "created_at": self._now(),
            "updated_at": self._now(),
        }

    def get_settings(self) -> dict:
        settings = self.storage.read_list(self.settings_file)
        if settings:
            return settings[-1]
        default = self._default_settings()
        self.storage.append(self.settings_file, default)
        return default

    def update_settings(self, updates: dict) -> dict:
        settings = self.storage.read_list(self.settings_file)
        record = settings[-1] if settings else self._default_settings()
        if updates.get("companion_mode") is not None:
            record["companion_mode"] = self._enum(updates["companion_mode"], COMPANION_MODES, record.get("companion_mode", "disabled"))
        # Safety invariants can never be enabled via this API.
        record["requires_user_activation"] = True
        record["background_listening"] = False
        record["wake_word_listener"] = False
        record["microphone_recording"] = False
        record["safety_rules"] = SAFETY_RULES
        record["updated_at"] = self._now()
        if settings:
            settings[-1] = record
            self.storage.write_list(self.settings_file, settings)
        else:
            self.storage.append(self.settings_file, record)
        self._audit("settings_updated", "companion", f"Companion mode set to {record['companion_mode']}.")
        self._log("companion_settings_updated", f"Updated companion settings → {record['companion_mode']}.")
        return record

    # ------------------------------------------------------------------
    # Readiness checks
    # ------------------------------------------------------------------
    def create_readiness_check(self, device_id: str | None = None) -> dict:
        device = next((d for d in self.list_devices() if d.get("device_id") == device_id), None) if device_id else None
        checklist = [
            {"item": "Microphone present (user-activated only)", "ready": bool(device and device.get("has_mic"))},
            {"item": "Speaker present", "ready": bool(device and device.get("has_speaker"))},
            {"item": "Local processing available", "ready": bool(device and device.get("local_processing"))},
            {"item": "Explicit user activation required", "ready": True},
            {"item": "No background listening / no wake-word", "ready": True},
        ]
        ready_count = sum(1 for c in checklist if c["ready"])
        check = {
            "check_id": str(uuid4()),
            "device_id": device_id,
            "checklist": checklist,
            "ready_count": ready_count,
            "total": len(checklist),
            "readiness": "ready" if ready_count >= 4 else "partial" if ready_count >= 2 else "not_ready",
            "note": "Readiness planning only — no hardware is accessed.",
            "created_at": self._now(),
        }
        self.storage.append(self.readiness_file, check)
        self._audit("readiness_check", check["check_id"], f"Readiness {check['readiness']} for device {device_id}.")
        self._log("companion_readiness_check", f"Ran readiness check {check['check_id']}.")
        return check

    def list_readiness_checks(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.readiness_file)[-limit:]))

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------
    def create_session(self, data: dict) -> dict:
        session = {
            "session_id": str(uuid4()),
            "device_id": self._clean(data.get("device_id"), 120) or None,
            "title": self._clean(data.get("title"), 200) or "Companion session",
            "notes": self._clean(data.get("notes"), 4000),
            "activation": "user_activated",
            "background_listening": False,
            "created_at": self._now(),
        }
        self.storage.append(self.sessions_file, session)
        self._audit("session_created", session["session_id"], "Created user-activated companion session.")
        self._log("companion_session_created", f"Created companion session {session['session_id']} (user-activated).")
        return session

    def list_sessions(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.sessions_file)[-limit:]))

    # ------------------------------------------------------------------
    # Audit + dashboard
    # ------------------------------------------------------------------
    def audit_log(self, limit: int = 50) -> list[dict]:
        return list(reversed(self.storage.read_list(self.audit_file)[-limit:]))

    def dashboard(self) -> dict:
        settings = self.get_settings()
        return {
            "device_count": len(self.list_devices()),
            "session_count": len(self.storage.read_list(self.sessions_file)),
            "readiness_check_count": len(self.storage.read_list(self.readiness_file)),
            "companion_mode": settings.get("companion_mode"),
            "background_listening": False,
            "microphone_recording": False,
            "wake_word_listener": False,
            "available_modes": COMPANION_MODES,
            "safety_rules": SAFETY_RULES,
            "note": "Readiness + session-planning layer only — no mic recording, no wake-word, no hardware access.",
        }
