from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Deliberately narrow: only the collections that actually showed up as large
# in /api/system/storage-status (the resource-exhaustion lens, rounds 39-40),
# not all ~220 StorageService-managed files. Maps each to its own real
# timestamp field -- these are NOT uniform across services (audit_packages
# uses generated_at, everything else here uses created_at).
_PRUNABLE_COLLECTIONS: dict[str, str] = {
    "governance_log.json": "created_at",
    "chat_sessions.json": "created_at",
    "messages.json": "created_at",
    "tasks.json": "created_at",
    "audit_packages.json": "generated_at",
}
_ARCHIVE_DIR_NAME = "archives"
_MIN_OLDER_THAN_DAYS = 1  # sanity floor -- never allow pruning "everything from today"


class StorageRetentionService:
    """Manual-trigger, archive-then-delete retention for the handful of
    collections real usage has shown grow largest. Nothing here runs
    automatically -- every prune is a real, explicit human-initiated call
    (POST /api/system/storage-prune), defaults to a dry run, and archives
    pruned records to a dated export under data_dir/archives/ before
    removing them from the live collection, so nothing is unrecoverably
    lost -- matters most for governance_log.json, an audit trail.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="storage_retention",
                agent_name="Storage Retention",
                action_type=action_type,
                tool_used="StorageRetentionService",
                permission_level="approve_to_run",
                approved=True,
                blocked=False,
                risk_score=15,
                reason=reason,
            )
        )

    def prunable_collections(self) -> dict[str, Any]:
        return {
            "collections": sorted(_PRUNABLE_COLLECTIONS),
            "min_older_than_days": _MIN_OLDER_THAN_DAYS,
            "note": "Archive-then-delete. Every prune is a real, explicit call -- nothing runs automatically.",
        }

    @staticmethod
    def _field_for(collection: str) -> str:
        field = _PRUNABLE_COLLECTIONS.get(collection)
        if field is None:
            raise ValueError(f"'{collection}' is not a prunable collection. Prunable: {sorted(_PRUNABLE_COLLECTIONS)}.")
        return field

    @staticmethod
    def _cutoff(older_than_days: int) -> str:
        if older_than_days < _MIN_OLDER_THAN_DAYS:
            raise ValueError(f"older_than_days must be >= {_MIN_OLDER_THAN_DAYS}.")
        return (datetime.now(UTC) - timedelta(days=older_than_days)).isoformat()

    @staticmethod
    def _is_older(entry: dict, field: str, cutoff: str) -> bool:
        value = entry.get(field)
        if not value or not isinstance(value, str):
            return False  # missing/malformed timestamp -> fail safe, never prune it
        return value < cutoff  # consistent ISO-8601 (datetime.now(UTC).isoformat() everywhere) sorts lexicographically == chronologically

    def preview(self, collection: str, older_than_days: int) -> dict[str, Any]:
        """Read-only: how many records WOULD be pruned. Never writes anything."""
        field = self._field_for(collection)
        cutoff = self._cutoff(older_than_days)
        entries = self.storage.read_list(collection)
        to_prune = sum(1 for entry in entries if self._is_older(entry, field, cutoff))
        return {
            "collection": collection,
            "older_than_days": older_than_days,
            "cutoff": cutoff,
            "total_records": len(entries),
            "records_to_prune": to_prune,
            "records_to_keep": len(entries) - to_prune,
            "dry_run": True,
        }

    def prune(self, collection: str, older_than_days: int) -> dict[str, Any]:
        """The real action: archives pruned records to a dated export file,
        then removes them from the live collection via a single update_list()
        call (atomic against concurrent writers, same primitive used
        throughout this app's concurrency fixes)."""
        field = self._field_for(collection)
        cutoff = self._cutoff(older_than_days)
        archived: list[dict] = []

        def _apply(entries: list[dict]) -> dict:
            keep = [entry for entry in entries if not self._is_older(entry, field, cutoff)]
            archived.extend(entry for entry in entries if self._is_older(entry, field, cutoff))
            entries[:] = keep  # in-place mutation -- update_list() writes back this same list object
            return {"pruned": len(archived), "kept": len(keep)}

        result = self.storage.update_list(collection, _apply)

        archive_path = self._write_archive(collection, archived) if archived else None

        self._log(
            "storage_pruned",
            f"Pruned {result['pruned']} record(s) older than {older_than_days}d from {collection}"
            + (f"; archived to {archive_path}." if archive_path else "; nothing to archive."),
        )
        return {
            "collection": collection,
            "older_than_days": older_than_days,
            "cutoff": cutoff,
            "pruned_count": result["pruned"],
            "remaining_count": result["kept"],
            "archive_path": archive_path,
            "dry_run": False,
        }

    def _write_archive(self, collection: str, records: list[dict]) -> str:
        archive_dir = os.path.join(self.storage.data_dir, _ARCHIVE_DIR_NAME)
        os.makedirs(archive_dir, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        base = collection[:-5] if collection.endswith(".json") else collection
        filename = f"{base}-{stamp}-{uuid4().hex[:8]}.json"
        path = os.path.join(archive_dir, filename)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=2)
        return path
