from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Voice event kinds we are willing to record (metadata only, never audio).
EVENT_KINDS = ["listen_start", "listen_stop", "transcribe", "speak", "settings_change", "voice_error"]

DEFAULT_SETTINGS = {
    "voice_name": "",            # empty => browser default voice
    "rate": 1.0,                 # 0.5 .. 2.0
    "pitch": 1.0,                # 0.0 .. 2.0
    "volume": 1.0,               # 0.0 .. 1.0
    "read_aloud": False,         # speak assistant replies aloud (opt-in)
    "transcript_enabled": True,  # show a local transcript while listening
    "store_transcripts": False,  # persist transcript text server-side (explicit opt-in)
}


def _clamp(value, low: float, high: float, fallback: float) -> float:
    try:
        return max(low, min(high, float(value)))
    except (TypeError, ValueError):
        return fallback


class VoiceConsoleService:
    """Phase 4 Voice Console — settings + privacy-safe audit for browser voice I/O.

    Voice is handled entirely in the browser (Web Speech API: push-to-talk
    recognition + speech synthesis). This service only stores **preferences**
    (which voice, rate, pitch, volume, read-aloud, transcript) and a **metadata**
    audit trail of voice activity. Hard privacy guarantees enforced here and
    reported by :meth:`status`:

    * ``push_to_talk_only`` is always True — there is no always-on recording.
    * ``always_on_recording`` and ``stores_audio`` are always False — no audio is
      ever uploaded or persisted; recognition/synthesis stay in the browser.
    * Transcript **text** is only persisted when the user explicitly opts in via
      ``store_transcripts``; otherwise events keep counts/durations only.

    All mutations are governance-logged. Everything is local-first and reversible
    (the user can clear the audit trail at any time).
    """

    settings_file = "voice_console_settings.json"
    events_file = "voice_console_events.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="voice_console",
                agent_name="Voice Console",
                action_type=action_type,
                tool_used="VoiceConsoleService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    # -- privacy status ------------------------------------------------------
    def status(self) -> dict:
        return {
            "available": True,
            "engine": "browser_web_speech_api",
            "push_to_talk_only": True,
            "always_on_recording": False,
            "stores_audio": False,
            "wake_word": False,
            "processing": "on_device_browser",
            "privacy_note": "Voice stays in your browser. Nothing is recorded, uploaded, or stored as audio.",
        }

    # -- settings ------------------------------------------------------------
    def _all_settings(self) -> list[dict]:
        return self.storage.read_list(self.settings_file)

    def get_settings(self, workspace_id: str = "global") -> dict:
        workspace_id = str(workspace_id or "global")[:80]
        for row in self._all_settings():
            if row.get("workspace_id") == workspace_id:
                return {**DEFAULT_SETTINGS, **{k: row[k] for k in DEFAULT_SETTINGS if k in row}, "workspace_id": workspace_id}
        return {**DEFAULT_SETTINGS, "workspace_id": workspace_id}

    def update_settings(self, patch: dict, workspace_id: str = "global") -> dict:
        workspace_id = str(workspace_id or "global")[:80]
        patch = patch or {}
        current = self.get_settings(workspace_id)
        merged = {
            "workspace_id": workspace_id,
            "voice_name": str(patch.get("voice_name", current["voice_name"]) or "")[:120],
            "rate": _clamp(patch.get("rate", current["rate"]), 0.5, 2.0, 1.0),
            "pitch": _clamp(patch.get("pitch", current["pitch"]), 0.0, 2.0, 1.0),
            "volume": _clamp(patch.get("volume", current["volume"]), 0.0, 1.0, 1.0),
            "read_aloud": bool(patch.get("read_aloud", current["read_aloud"])),
            "transcript_enabled": bool(patch.get("transcript_enabled", current["transcript_enabled"])),
            "store_transcripts": bool(patch.get("store_transcripts", current["store_transcripts"])),
            "updated_at": self._now(),
        }
        rows = [r for r in self._all_settings() if r.get("workspace_id") != workspace_id]
        rows.append(merged)
        self.storage.write_list(self.settings_file, rows)
        self._log("voice_settings_updated", f"Voice settings updated for workspace {workspace_id}")
        return merged

    # -- audit events (metadata only) ---------------------------------------
    def log_activity(self, kind: str, workspace_id: str = "global", text: str = "", meta: dict | None = None) -> dict:
        if kind not in EVENT_KINDS:
            raise ValueError(f"Unknown voice event kind: {kind}")
        workspace_id = str(workspace_id or "global")[:80]
        settings = self.get_settings(workspace_id)
        text = str(text or "")
        event = {
            "id": str(uuid4()),
            "workspace_id": workspace_id,
            "kind": kind,
            "char_count": len(text),
            "meta": {str(k)[:40]: str(v)[:120] for k, v in list((meta or {}).items())[:10]},
            "created_at": self._now(),
        }
        # Transcript text is persisted ONLY with explicit opt-in, and always capped.
        if settings["store_transcripts"] and text:
            event["transcript"] = text[:2000]
        self.storage.append(self.events_file, event)
        self._log("voice_activity", f"Voice activity '{kind}' ({event['char_count']} chars) in {workspace_id}")
        return event

    def events(self, workspace_id: str = "global", limit: int = 50) -> dict:
        workspace_id = str(workspace_id or "global")[:80]
        rows = [e for e in self.storage.read_list(self.events_file) if e.get("workspace_id") == workspace_id]
        rows.sort(key=lambda e: e.get("created_at", ""), reverse=True)
        try:
            limit = max(1, min(500, int(limit)))
        except (TypeError, ValueError):
            limit = 50
        return {"events": rows[:limit], "count": len(rows), "workspace_id": workspace_id}

    def clear_events(self, workspace_id: str = "global") -> dict:
        workspace_id = str(workspace_id or "global")[:80]
        kept = [e for e in self.storage.read_list(self.events_file) if e.get("workspace_id") != workspace_id]
        removed = len(self.storage.read_list(self.events_file)) - len(kept)
        self.storage.write_list(self.events_file, kept)
        self._log("voice_events_cleared", f"Cleared {removed} voice events for {workspace_id}")
        return {"cleared": removed, "workspace_id": workspace_id}

    # -- analytics -----------------------------------------------------------
    def analytics_summary(self) -> dict:
        events = self.storage.read_list(self.events_file)
        by_kind: dict[str, int] = {}
        for e in events:
            k = e.get("kind", "unknown")
            by_kind[k] = by_kind.get(k, 0) + 1
        return {
            "voice_console_settings": len(self._all_settings()),
            "voice_console_events": len(events),
            "voice_console_events_by_kind": by_kind,
        }

    def summary(self) -> dict:
        return {**self.status(), **self.analytics_summary(), "default_settings": DEFAULT_SETTINGS}
