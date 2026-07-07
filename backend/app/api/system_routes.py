"""System routes — infrastructure/status endpoints (v100).

Read-only observability into the storage layer. Imports the shared ``storage``
singleton from routes.py (one-directional, no cycle); main.py includes this
router under /api.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import storage
from app.config import settings

router = APIRouter()


@router.get("/system/storage-status")
def storage_status() -> dict:
    """Which storage backend is active, how much data it holds, and what infra is
    configured. Secret-safe (booleans only — never any URL with credentials)."""
    return {
        **storage.status(),
        "configured_backend": settings.storage_backend,
    }
