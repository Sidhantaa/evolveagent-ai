from __future__ import annotations

from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# User-editable preferences, grouped by category. Each key maps to its default and
# an allow-list of accepted values (None => free-ish string capped in length).
# NOTE: no secret/key/token value is ever stored here — those live only in the
# environment and are reported elsewhere as booleans.
EDITABLE_SETTINGS = {
    "provider": {
        "default_model": {"default": "claude-opus-4-8", "allowed": None},
        "prefer_mock": {"default": True, "allowed": [True, False]},
    },
    "modes": {
        "developer_mode_default": {"default": False, "allowed": [True, False]},
        "deep_mode_default": {"default": False, "allowed": [True, False]},
    },
    "features": {
        "show_master_agent_panel": {"default": True, "allowed": [True, False]},
        "show_activity_timeline": {"default": True, "allowed": [True, False]},
        "show_global_search": {"default": True, "allowed": [True, False]},
    },
    "safety": {
        # A preference that can only ever *tighten* — it cannot disable the enforced boundaries below.
        "always_confirm_risky": {"default": True, "allowed": [True, False]},
    },
    "workspace_defaults": {
        "default_task_type": {"default": "auto", "allowed": None},
    },
    "voice": {
        "spoken_answers_default": {"default": False, "allowed": [True, False]},
        "push_to_talk": {"default": True, "allowed": [True, False]},
    },
    "theme": {
        "mode": {"default": "dark", "allowed": ["dark", "light"]},
    },
}

# Hard safety boundaries — always enforced, shown read-only, never editable via settings.
ENFORCED_SAFETY = [
    "No unrestricted shell execution.",
    "No destructive autonomous file operations.",
    "No real sending/payment/deploy without explicit approval.",
    "Risky actions (send/pay/delete/deploy) are always approval-gated.",
    "Secret key readiness is reported as booleans only — values are never stored or shown.",
    "No production auth; organization records are local only.",
    "No microphone recording or wake-word listening.",
    "No base-model self-training.",
]

# Any incoming key containing one of these is rejected outright (defense in depth).
_FORBIDDEN_SUBSTRINGS = ("key", "token", "secret", "password", "credential", "api_key")


class SettingsService:
    """v67.0 Settings Center — one central place for local configuration.

    Stores user preferences (provider defaults, mode toggles, feature toggles, a
    safety preference, workspace defaults, voice, theme) as a single local settings
    document. It validates every update against an allow-list, **never stores secret
    values** (keys containing key/token/secret/etc. are rejected), and surfaces the
    hard safety boundaries as read-only/enforced. Supports export/import (secrets
    excluded) and reset-to-defaults. Changes are governance-logged.
    """

    settings_file = "settings_center.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _defaults(self) -> dict:
        return {cat: {k: spec["default"] for k, spec in keys.items()} for cat, keys in EDITABLE_SETTINGS.items()}

    def _stored(self) -> dict:
        records = self.storage.read_list(self.settings_file)
        return records[-1]["settings"] if records and isinstance(records[-1], dict) and records[-1].get("settings") else {}

    def _effective(self) -> dict:
        merged = self._defaults()
        stored = self._stored()
        for cat, keys in merged.items():
            for key in keys:
                if isinstance(stored.get(cat), dict) and key in stored[cat]:
                    keys[key] = stored[cat][key]
        return merged

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="settings_center",
                agent_name="Settings Center",
                action_type=action_type,
                tool_used="SettingsService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def get_settings(self) -> dict:
        return {
            "settings": self._effective(),
            "enforced_safety": ENFORCED_SAFETY,
            "editable_categories": list(EDITABLE_SETTINGS.keys()),
            "note": "User preferences only — no secret values are stored here; hard safety boundaries are enforced and read-only.",
        }

    def _validate_patch(self, patch: dict) -> tuple[dict, list[str]]:
        clean: dict = {}
        rejected: list[str] = []
        for cat, keys in (patch or {}).items():
            if cat not in EDITABLE_SETTINGS or not isinstance(keys, dict):
                rejected.append(str(cat))
                continue
            for key, value in keys.items():
                if any(bad in key.lower() for bad in _FORBIDDEN_SUBSTRINGS):
                    rejected.append(f"{cat}.{key} (forbidden)")
                    continue
                spec = EDITABLE_SETTINGS[cat].get(key)
                if not spec:
                    rejected.append(f"{cat}.{key}")
                    continue
                if spec["allowed"] is not None and value not in spec["allowed"]:
                    rejected.append(f"{cat}.{key} (bad value)")
                    continue
                if spec["allowed"] is None and (not isinstance(value, str) or len(value) > 120):
                    rejected.append(f"{cat}.{key} (bad value)")
                    continue
                clean.setdefault(cat, {})[key] = value
        return clean, rejected

    def update_settings(self, patch: dict) -> dict:
        clean, rejected = self._validate_patch(patch)
        stored = self._stored()
        for cat, keys in clean.items():
            stored.setdefault(cat, {}).update(keys)
        self.storage.write_list(self.settings_file, [{"settings": stored, "updated_at": self._now()}])
        self._log("settings_updated", f"Updated {sum(len(v) for v in clean.values())} setting(s); rejected {len(rejected)}.")
        return {"settings": self._effective(), "applied": clean, "rejected": rejected}

    def reset(self) -> dict:
        self.storage.write_list(self.settings_file, [])
        self._log("settings_reset", "Reset all settings to defaults.")
        return {"settings": self._effective(), "note": "All settings reset to defaults."}

    def export_settings(self) -> dict:
        self._log("settings_exported", "Exported settings (no secrets).")
        return {"version": "1.0", "settings": self._effective(), "exported_at": self._now(), "note": "Contains preferences only — no secret values."}

    def import_settings(self, doc: dict) -> dict:
        incoming = (doc or {}).get("settings")
        if not isinstance(incoming, dict):
            raise ValueError("Invalid settings document")
        return self.update_settings(incoming)

    def analytics_summary(self) -> dict:
        return {"settings_editable_keys": sum(len(v) for v in EDITABLE_SETTINGS.values())}
