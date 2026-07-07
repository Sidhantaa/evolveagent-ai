"""real-api routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    real_api_control_service,
)
from app.models.request_models import (
    RealApiErrorDecodeRequest,
)

router = APIRouter()


@router.get("/real-api/summary")
def get_real_api_summary() -> dict:
    return real_api_control_service.summary()


@router.get("/real-api/live-warning/{capability}")
def get_real_api_live_warning(capability: str) -> dict:
    return real_api_control_service.live_warning(capability)


@router.post("/real-api/decode-error")
def decode_real_api_error(request: RealApiErrorDecodeRequest) -> dict:
    return real_api_control_service.decode_error(request.error)
