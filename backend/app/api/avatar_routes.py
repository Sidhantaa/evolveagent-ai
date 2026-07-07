"""avatar routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    avatar_persona_service,
)
from app.models.request_models import (
    AvatarConsentRequest,
    AvatarImageRequest,
    AvatarMeetingSessionRequest,
    AvatarPersonaUpdateRequest,
    AvatarVoiceSettingsUpdateRequest,
)

router = APIRouter()


# NOTE: /training-lab/* routes were extracted into app/api/training_lab_routes.py (services still live here).


# ----------------------------------------------------------------------
# v28.0 Personal AI Avatar / Voice Twin (settings + shell; no impersonation/cloning)
# ----------------------------------------------------------------------
@router.get("/avatar/dashboard")
def get_avatar_dashboard() -> dict:
    return avatar_persona_service.dashboard()


@router.get("/avatar/persona")
def get_avatar_persona() -> dict:
    return avatar_persona_service.get_persona()


@router.patch("/avatar/persona")
def update_avatar_persona(request: AvatarPersonaUpdateRequest) -> dict:
    return avatar_persona_service.update_persona(request.model_dump(exclude_unset=True))


@router.get("/avatar/voice-settings")
def get_avatar_voice_settings() -> dict:
    return avatar_persona_service.get_voice_settings()


@router.patch("/avatar/voice-settings")
def update_avatar_voice_settings(request: AvatarVoiceSettingsUpdateRequest) -> dict:
    return avatar_persona_service.update_voice_settings(request.model_dump(exclude_unset=True))


@router.post("/avatar/meeting-sessions")
def create_avatar_meeting_session(request: AvatarMeetingSessionRequest) -> dict:
    return avatar_persona_service.create_meeting_session(request.model_dump())


@router.get("/avatar/meeting-sessions")
def list_avatar_meeting_sessions() -> dict:
    sessions = avatar_persona_service.list_meeting_sessions()
    return {"meeting_sessions": sessions, "count": len(sessions)}


@router.post("/avatar/consent")
def create_avatar_consent(request: AvatarConsentRequest) -> dict:
    return avatar_persona_service.create_consent(request.model_dump())


@router.post("/avatar/persona/avatar-image")
def generate_avatar_image(request: AvatarImageRequest) -> dict:
    try:
        return avatar_persona_service.generate_avatar_image(request.description, request.style)
    except ValueError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
