from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

VOICE_MODES = ["text_only", "spoken_summary_ready", "disabled"]
TONES = ["friendly", "professional", "concise", "encouraging", "neutral"]
FORMATS = ["bullets", "paragraph", "step_by_step", "summary_first"]

# Hard safety rules — surfaced everywhere and never configurable away.
SAFETY_RULES = [
    "The avatar is clearly an AI assistant and never claims to be the user.",
    "No impersonation of the user or any real person.",
    "No voice cloning — spoken output is generic TTS-ready text only, never a copy of someone's voice.",
    "Consent is recorded before persona behaviors are used in meetings.",
]


class AvatarPersonaService:
    """v28.0 Personal AI Avatar / Voice Twin (settings + shell only).

    Stores a personalized assistant persona (tone, format, avatar name, style),
    voice-response settings (text-only / spoken-summary-ready / disabled), meeting
    voice-assistant session notes, and consent records. It does NOT impersonate
    the user and does NOT clone any voice — spoken output is generic TTS-ready
    text only. Stateful actions are governance-logged.
    """

    persona_file = "avatar_personas.json"
    voice_file = "voice_response_settings.json"
    meeting_file = "meeting_voice_sessions.json"
    consent_file = "persona_consent_records.json"

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
                task_type="avatar_persona",
                agent_name="Avatar Persona Service",
                action_type=action_type,
                tool_used="AvatarPersonaService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Persona (single active persona)
    # ------------------------------------------------------------------
    def _default_persona(self) -> dict:
        return {
            "avatar_name": "Evo",
            "tone": "friendly",
            "format": "summary_first",
            "style": "calm and helpful",
            "is_ai_disclosure": "I am an AI assistant, not the user.",
            "impersonation_allowed": False,
            "voice_cloning_allowed": False,
            "created_at": self._now(),
            "updated_at": self._now(),
        }

    def get_persona(self) -> dict:
        personas = self.storage.read_list(self.persona_file)
        if personas:
            return personas[-1]
        persona = self._default_persona()
        self.storage.append(self.persona_file, persona)
        return persona

    def update_persona(self, updates: dict) -> dict:
        personas = self.storage.read_list(self.persona_file)
        persona = personas[-1] if personas else self._default_persona()
        if updates.get("avatar_name") is not None:
            persona["avatar_name"] = self._clean(updates["avatar_name"], 80) or persona.get("avatar_name", "Evo")
        if updates.get("tone") is not None:
            persona["tone"] = self._enum(updates["tone"], TONES, persona.get("tone", "friendly"))
        if updates.get("format") is not None:
            persona["format"] = self._enum(updates["format"], FORMATS, persona.get("format", "summary_first"))
        if updates.get("style") is not None:
            persona["style"] = self._clean(updates["style"], 200)
        # Safety invariants can never be turned off.
        persona["impersonation_allowed"] = False
        persona["voice_cloning_allowed"] = False
        persona["is_ai_disclosure"] = "I am an AI assistant, not the user."
        persona["updated_at"] = self._now()
        if personas:
            personas[-1] = persona
            self.storage.write_list(self.persona_file, personas)
        else:
            self.storage.append(self.persona_file, persona)
        self._log("avatar_persona_updated", f"Updated persona '{persona['avatar_name']}'.")
        return persona

    # ------------------------------------------------------------------
    # Voice settings (single active)
    # ------------------------------------------------------------------
    def _default_voice(self) -> dict:
        return {
            "voice_mode": "text_only",
            "spoken_summary_max_chars": 600,
            "voice_cloning_allowed": False,
            "note": "Spoken output is generic TTS-ready text only — never a cloned voice.",
            "created_at": self._now(),
            "updated_at": self._now(),
        }

    def get_voice_settings(self) -> dict:
        settings = self.storage.read_list(self.voice_file)
        if settings:
            return settings[-1]
        default = self._default_voice()
        self.storage.append(self.voice_file, default)
        return default

    def update_voice_settings(self, updates: dict) -> dict:
        settings = self.storage.read_list(self.voice_file)
        record = settings[-1] if settings else self._default_voice()
        if updates.get("voice_mode") is not None:
            record["voice_mode"] = self._enum(updates["voice_mode"], VOICE_MODES, record.get("voice_mode", "text_only"))
        if updates.get("spoken_summary_max_chars") is not None:
            try:
                record["spoken_summary_max_chars"] = max(100, min(2000, int(updates["spoken_summary_max_chars"])))
            except (TypeError, ValueError):
                pass
        record["voice_cloning_allowed"] = False
        record["updated_at"] = self._now()
        if settings:
            settings[-1] = record
            self.storage.write_list(self.voice_file, settings)
        else:
            self.storage.append(self.voice_file, record)
        self._log("avatar_voice_settings_updated", f"Updated voice settings → {record['voice_mode']}.")
        return record

    # ------------------------------------------------------------------
    # Meeting voice sessions
    # ------------------------------------------------------------------
    def create_meeting_session(self, data: dict) -> dict:
        session = {
            "meeting_session_id": str(uuid4()),
            "title": self._clean(data.get("title"), 200) or "Meeting assistant session",
            "context": self._clean(data.get("context"), 4000),
            "planned_notes": [
                "Listen-only by default; produce a summary the user reviews before sharing.",
                "Never speak as the user; always identify as the AI assistant if it responds.",
            ],
            "status": "planned",
            "requires_consent": True,
            "created_at": self._now(),
        }
        self.storage.append(self.meeting_file, session)
        self._log("avatar_meeting_session_created", f"Created meeting voice session {session['meeting_session_id']}.")
        return session

    def list_meeting_sessions(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.meeting_file)[-limit:]))

    # ------------------------------------------------------------------
    # Consent
    # ------------------------------------------------------------------
    def create_consent(self, data: dict) -> dict:
        consent = {
            "consent_id": str(uuid4()),
            "scope": self._clean(data.get("scope"), 120) or "persona_behavior",
            "granted": bool(data.get("granted", False)),
            "note": self._clean(data.get("note"), 1000),
            "safety_rules_acknowledged": SAFETY_RULES,
            "created_at": self._now(),
        }
        self.storage.append(self.consent_file, consent)
        self._log("avatar_consent_recorded", f"Recorded consent (granted={consent['granted']}) for {consent['scope']}.")
        return consent

    def list_consent(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.consent_file)[-limit:]))

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard(self) -> dict:
        persona = self.get_persona()
        voice = self.get_voice_settings()
        consents = self.storage.read_list(self.consent_file)
        meetings = self.storage.read_list(self.meeting_file)
        return {
            "persona": persona,
            "voice_settings": voice,
            "meeting_session_count": len(meetings),
            "consent_record_count": len(consents),
            "latest_consent_granted": consents[-1].get("granted") if consents else None,
            "safety_rules": SAFETY_RULES,
            "impersonation_allowed": False,
            "voice_cloning_allowed": False,
        }
