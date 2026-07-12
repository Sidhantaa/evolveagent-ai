"""Capability Directory routes -- a single, honest inventory of every real/
local/mock/needs-config/blocked capability built across this app's opt-in-real
surface (v200 strategy doc's Current Execution Priority #2)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import capability_directory_service

router = APIRouter()


@router.get("/capability-directory")
def list_capabilities(category: str | None = None, status: str | None = None) -> dict:
    entries = capability_directory_service.list_capabilities(category, status)
    return {"capabilities": entries, "count": len(entries), "categories": capability_directory_service.categories()}


@router.get("/capability-directory/summary")
def capability_directory_summary() -> dict:
    return capability_directory_service.summary()
