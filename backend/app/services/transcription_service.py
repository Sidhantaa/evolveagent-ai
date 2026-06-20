from pathlib import Path
from time import perf_counter

from app.config import settings


class TranscriptionService:
    def status(self) -> dict:
        mode = settings.transcription_mode.lower()
        openai_ready = mode == "openai" and bool(settings.openai_api_key)
        active_provider = "openai" if openai_ready else "mock"
        active_model = settings.openai_transcription_model if openai_ready else "mock-transcription"
        if openai_ready:
            status_message = "OpenAI transcription is configured. Recording uploads can use the real transcription API."
        elif mode == "openai":
            status_message = "OpenAI transcription mode is enabled, but OPENAI_API_KEY is missing. Mock fallback will be used."
        else:
            status_message = "Transcription is running in mock mode. Set TRANSCRIPTION_MODE=openai and OPENAI_API_KEY to use real transcription."

        return {
            "transcription_mode": mode,
            "openai_configured": bool(settings.openai_api_key),
            "real_transcription_ready": openai_ready,
            "active_provider": active_provider,
            "active_model": active_model,
            "fallback_provider": "mock",
            "status_message": status_message,
        }

    def smoke_test(self, live: bool = False) -> dict:
        status = self.status()
        if not live:
            return {
                "success": status["real_transcription_ready"] or status["active_provider"] == "mock",
                "live": False,
                "provider": status["active_provider"],
                "model": status["active_model"],
                "fallback_provider": status["fallback_provider"],
                "message": status["status_message"],
            }

        if not status["real_transcription_ready"]:
            return {
                "success": False,
                "live": True,
                "provider": status["active_provider"],
                "model": status["active_model"],
                "fallback_provider": status["fallback_provider"],
                "message": status["status_message"],
            }

        return {
            "success": False,
            "live": True,
            "provider": "openai",
            "model": settings.openai_transcription_model,
            "fallback_provider": "mock",
            "message": "Live transcription checks require an uploaded audio file. Use the recording upload flow to run a real transcription call.",
        }

    def transcribe(self, path: Path, filename: str) -> dict:
        if settings.transcription_mode.lower() != "openai" or not settings.openai_api_key:
            return self.mock_transcript(filename)

        start = perf_counter()
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            with path.open("rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model=settings.openai_transcription_model,
                    file=audio_file,
                )
            text = getattr(result, "text", "") or str(result)
            return {
                "provider": "openai",
                "model": settings.openai_transcription_model,
                "transcript": text,
                "latency_ms": int((perf_counter() - start) * 1000),
                "fallback_used": False,
                "error": None,
            }
        except Exception as exc:
            fallback = self.mock_transcript(filename)
            fallback["fallback_used"] = True
            fallback["error"] = f"OpenAI transcription failed: {exc}"
            return fallback

    @staticmethod
    def mock_transcript(filename: str) -> dict:
        transcript = (
            f"Mock transcript for {filename}. The speaker discusses project goals, current progress, "
            "important decisions, action items, and follow-up tasks. Decision: keep the MVP scope focused. "
            "Action item: summarize the key points, identify next steps, and prepare clean notes for review. "
            "Follow-up task: verify the implementation and update documentation."
        )
        return {
            "provider": "mock",
            "model": "mock-transcription",
            "transcript": transcript,
            "latency_ms": 0,
            "fallback_used": False,
            "error": None,
        }
