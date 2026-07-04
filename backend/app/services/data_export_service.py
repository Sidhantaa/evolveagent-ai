from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

BUNDLE_VERSION = "1.0"

# Content collections that are safe to export/import. Excludes governance/audit
# logs and analytics; contains no secret values (secret registry stores key names
# and readiness booleans only).
EXPORTABLE_COLLECTIONS = [
    "workspaces.json",
    "goals.json",
    "task_graphs.json",
    "custom_agents.json",
    "mcp_connectors.json",
    "mcp_policies.json",
    "mcp_secret_refs.json",
    "playbooks.json",
    "scheduled_tasks.json",
    "workspace_templates.json",
    "innovation_ideas.json",
    "simulation_worlds.json",
    "team_members.json",
    "business_leads.json",
    "eval_suites.json",
]

_MAX_ITEMS_PER_COLLECTION = 5000


def _item_id(item: dict) -> str | None:
    if not isinstance(item, dict):
        return None
    if "id" in item:
        return str(item["id"])
    for key in item:
        if key.endswith("_id"):
            return str(item[key])
    return None


class DataExportService:
    """v59.0 Data Export & Backup (local bundle — no external upload).

    Exports a curated set of local content collections into a single JSON
    **bundle** the user can download, and imports a bundle back in. Import is
    **non-destructive**: it merges by appending items whose id is not already
    present, never overwriting or deleting existing data. Everything is local —
    no external upload or network. Exports and imports are governance-logged.
    """

    log_file = "data_export_log.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="data_export",
                agent_name="Data Export & Backup",
                action_type=action_type,
                tool_used="DataExportService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=4,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export_bundle(self) -> dict:
        collections: dict[str, list] = {}
        total = 0
        for name in EXPORTABLE_COLLECTIONS:
            items = self.storage.read_list(name)[:_MAX_ITEMS_PER_COLLECTION]
            collections[name] = items
            total += len(items)
        bundle = {
            "bundle_version": BUNDLE_VERSION,
            "created_at": self._now(),
            "collection_count": len(collections),
            "total_items": total,
            "collections": collections,
            "note": "Local backup bundle — content collections only. No secret values, governance logs, or external data are included.",
        }
        self.storage.append(self.log_file, {"log_id": str(uuid4()), "action": "export", "total_items": total, "created_at": self._now()})
        self._log("data_exported", f"Exported {total} item(s) across {len(collections)} collection(s) into a local bundle.")
        return bundle

    # ------------------------------------------------------------------
    # Import (non-destructive merge)
    # ------------------------------------------------------------------
    def import_bundle(self, bundle: dict) -> dict:
        bundle = bundle or {}
        incoming = bundle.get("collections")
        if not isinstance(incoming, dict):
            raise ValueError("Invalid bundle: missing 'collections' object")
        imported: dict[str, int] = {}
        skipped: dict[str, int] = {}
        for name, items in incoming.items():
            if name not in EXPORTABLE_COLLECTIONS or not isinstance(items, list):
                continue
            existing = self.storage.read_list(name)
            existing_ids = {_item_id(i) for i in existing if _item_id(i)}
            added = 0
            skip = 0
            for item in items[:_MAX_ITEMS_PER_COLLECTION]:
                if not isinstance(item, dict):
                    continue
                iid = _item_id(item)
                if iid and iid in existing_ids:
                    skip += 1
                    continue
                existing.append(item)
                if iid:
                    existing_ids.add(iid)
                added += 1
            if added:
                self.storage.write_list(name, existing)
            imported[name] = added
            skipped[name] = skip
        total_imported = sum(imported.values())
        self.storage.append(self.log_file, {"log_id": str(uuid4()), "action": "import", "total_items": total_imported, "created_at": self._now()})
        self._log("data_imported", f"Imported {total_imported} new item(s) (merge, non-destructive).")
        return {
            "imported": imported,
            "skipped_existing": skipped,
            "total_imported": total_imported,
            "note": "Non-destructive merge — items with an existing id were skipped; nothing was overwritten or deleted.",
        }

    # ------------------------------------------------------------------
    # Summary + analytics
    # ------------------------------------------------------------------
    def summary(self) -> dict:
        log = self.storage.read_list(self.log_file)
        counts = {name: len(self.storage.read_list(name)) for name in EXPORTABLE_COLLECTIONS}
        return {
            "exportable_collections": len(EXPORTABLE_COLLECTIONS),
            "current_item_counts": counts,
            "total_current_items": sum(counts.values()),
            "export_events": sum(1 for e in log if e.get("action") == "export"),
            "import_events": sum(1 for e in log if e.get("action") == "import"),
            "note": "Local export/import only — no external upload; import is non-destructive.",
        }

    def analytics_summary(self) -> dict:
        log = self.storage.read_list(self.log_file)
        return {
            "data_exports": sum(1 for e in log if e.get("action") == "export"),
            "data_imports": sum(1 for e in log if e.get("action") == "import"),
        }
