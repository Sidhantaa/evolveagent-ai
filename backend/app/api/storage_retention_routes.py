"""Storage retention routes -- manual, explicit archive-then-delete pruning
for the collections that showed up as large in /api/system/storage-status.

Nothing here runs automatically. dry_run defaults to True, so a caller must
explicitly pass dry_run=false to actually delete anything.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.routes import storage_retention_service
from app.models.request_models import StoragePruneRequest

router = APIRouter()


@router.get("/system/storage-prune/collections")
def get_prunable_collections() -> dict:
    return storage_retention_service.prunable_collections()


@router.post("/system/storage-prune")
def prune_storage(request: StoragePruneRequest) -> dict:
    try:
        if request.dry_run:
            return storage_retention_service.preview(request.collection, request.older_than_days)
        return storage_retention_service.prune(request.collection, request.older_than_days)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
