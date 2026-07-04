from __future__ import annotations

import os
import re
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Sensitive-content patterns for redaction PREVIEW (nothing is written).
_SENSITIVE = [
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "email"),
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "card-like"),
    (re.compile(r"(sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{10,})"), "key-like token"),
]
# Collections considered ephemeral/runtime (cleanup SUGGESTIONS only — never auto-deleted).
_EPHEMERAL_HINTS = ("_log", "_runs", "_events", "_audit", "history", "notifications")


class DataManagerService:
    """v83.0 Local Data Manager — manage JSON storage safely (read-only / planning-first).

    A read-only view over the local JSON store: a **collection browser** (record counts
    + byte sizes), **storage usage** (totals, largest collections), **cleanup
    suggestions** (large/ephemeral collections — advisory), a **backup** helper (exports
    selected collections; reuses the read-only export path), and a **redaction preview**
    (counts sensitive matches per collection **without writing**). It never deletes,
    redacts, or overwrites data autonomously — destructive operations are surfaced as
    suggestions only, consistent with the no-destructive-autonomous-file-ops rule.
    Governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _collections(self) -> list[str]:
        try:
            return sorted(f for f in os.listdir(self.storage.data_dir) if f.endswith(".json"))
        except OSError:
            return []

    def _size(self, filename: str) -> int:
        try:
            return os.path.getsize(os.path.join(self.storage.data_dir, filename))
        except OSError:
            return 0

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="data_manager",
                agent_name="Local Data Manager",
                action_type=action_type,
                tool_used="DataManagerService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def browse(self) -> dict:
        rows = []
        for filename in self._collections():
            rows.append({"collection": filename, "records": len(self.storage.read_list(filename)), "bytes": self._size(filename)})
        rows.sort(key=lambda r: r["bytes"], reverse=True)
        self._log("data_browsed", f"Browsed {len(rows)} local collection(s).")
        return {"collections": rows, "count": len(rows)}

    def usage(self) -> dict:
        rows = [{"collection": f, "bytes": self._size(f)} for f in self._collections()]
        total = sum(r["bytes"] for r in rows)
        rows.sort(key=lambda r: r["bytes"], reverse=True)
        return {
            "total_bytes": total,
            "total_kb": round(total / 1024, 1),
            "collection_count": len(rows),
            "largest": rows[:10],
        }

    def cleanup_suggestions(self) -> dict:
        suggestions = []
        for filename in self._collections():
            size = self._size(filename)
            records = len(self.storage.read_list(filename))
            ephemeral = any(h in filename for h in _EPHEMERAL_HINTS)
            if ephemeral and records > 500:
                suggestions.append({"collection": filename, "records": records, "bytes": size,
                                    "suggestion": "Ephemeral/runtime collection is large — consider exporting a backup then archiving old entries (manual)."})
            elif size > 512 * 1024:
                suggestions.append({"collection": filename, "records": records, "bytes": size,
                                    "suggestion": "Large collection — review whether older records can be exported and pruned (manual)."})
        self._log("data_cleanup_suggested", f"Generated {len(suggestions)} cleanup suggestion(s).")
        return {"suggestions": suggestions, "count": len(suggestions),
                "note": "Advisory only — this tool never deletes or overwrites data; any cleanup is a manual, explicit step."}

    def redaction_preview(self, collection: str) -> dict:
        if not collection.endswith(".json") or collection not in self._collections():
            raise ValueError("Unknown collection")
        items = self.storage.read_list(collection)
        counts: dict[str, int] = {}
        for item in items:
            blob = str(item)
            for pattern, label in _SENSITIVE:
                found = len(pattern.findall(blob))
                if found:
                    counts[label] = counts.get(label, 0) + found
        self._log("data_redaction_previewed", f"Previewed redaction for {collection}.")
        return {"collection": collection, "sensitive_matches": counts, "total_matches": sum(counts.values()),
                "note": "Preview only — nothing is redacted or written; secret values are counted, never returned."}

    def analytics_summary(self) -> dict:
        return {"data_manager_collections": len(self._collections()), "data_manager_total_kb": self.usage()["total_kb"]}

    def summary(self) -> dict:
        usage = self.usage()
        return {
            "collection_count": usage["collection_count"],
            "total_kb": usage["total_kb"],
            "note": "Read-only / planning-first data manager — browse, usage, cleanup suggestions, redaction preview; no deletes or overwrites.",
        }
