"""Memory v2 routes — semantic memory (pgvector / keyword fallback).

Imports the shared ``memory_service`` from routes.py (one-directional). main.py
includes this router under /api.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.routes import memory_service
from app.models.request_models import MemoryAddRequest

router = APIRouter()


@router.get("/memory-v2/status")
def memory_v2_status() -> dict:
    return memory_service.status()


@router.post("/memory-v2/add")
def memory_v2_add(request: MemoryAddRequest) -> dict:
    try:
        return memory_service.add(request.text, request.kind, request.source, request.metadata)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/memory-v2/search")
def memory_v2_search(q: str, limit: int = 5, workspace_id: str | None = None) -> dict:
    return memory_service.search(q, limit, workspace_id)


@router.get("/memory-v2/summary")
def memory_v2_summary() -> dict:
    return {**memory_service.status(), **memory_service.analytics_summary()}
