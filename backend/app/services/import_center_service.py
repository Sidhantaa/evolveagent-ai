from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

IMPORT_KINDS = ["document", "csv", "markdown", "chat_history", "project_notes"]
_MAX_RECORDS = 500

# Sanitization: sensitive values are redacted before anything is saved.
_REDACTIONS = [
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[redacted-email]"),
    (re.compile(r"(sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]{10,}|AKIA[0-9A-Z]{12,})"), "[redacted-token]"),
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "[redacted-number]"),
]


class ImportCenterService:
    """v84.0 Import Center — bring external data into EvolveAgent safely.

    Parses submitted content by **kind** (document, csv, markdown, chat_history,
    project_notes) into records, **validates** (allowed kind, size caps) and
    **sanitizes** (redacts emails/keys/card-like numbers) **before saving**, offers an
    **import preview** (shows the sanitized records without writing), and a **commit**
    that appends the sanitized records to a dedicated ``imported_records`` collection
    (never into core collections). Additive and governance-logged; secret values are
    redacted, never stored.
    """

    records_file = "imported_records.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _sanitize(text: str) -> tuple[str, int]:
        redactions = 0
        for pattern, replacement in _REDACTIONS:
            text, n = pattern.subn(replacement, text)
            redactions += n
        return text, redactions

    def _parse(self, kind: str, content: str) -> list[str]:
        content = content or ""
        if kind == "csv":
            lines = [ln for ln in content.splitlines() if ln.strip()]
            return lines  # header + rows as records
        if kind in ("markdown", "project_notes"):
            return [block.strip() for block in re.split(r"\n\s*\n", content) if block.strip()]
        if kind == "chat_history":
            return [ln.strip() for ln in content.splitlines() if ln.strip()]
        # document / default: paragraphs
        return [block.strip() for block in re.split(r"\n\s*\n", content) if block.strip()] or [content.strip()]

    def _build(self, kind: str, content: str) -> tuple[list[dict], int]:
        raw = self._parse(kind, content)[:_MAX_RECORDS]
        records = []
        total_redactions = 0
        for i, piece in enumerate(raw):
            clean, redactions = self._sanitize(piece)
            total_redactions += redactions
            records.append({"index": i, "kind": kind, "content": clean[:2000], "redactions": redactions})
        return records, total_redactions

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="import_center",
                agent_name="Import Center",
                action_type=action_type,
                tool_used="ImportCenterService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=2,
                reason=reason,
            )
        )

    def preview(self, kind: str, content: str) -> dict:
        if kind not in IMPORT_KINDS:
            raise ValueError("Unsupported import kind")
        records, redactions = self._build(kind, content)
        self._log("import_previewed", f"Previewed import of {len(records)} {kind} record(s).")
        return {
            "kind": kind,
            "record_count": len(records),
            "redactions": redactions,
            "preview": records[:25],
            "note": "Preview only — nothing is saved yet; sensitive values are redacted before any import.",
        }

    def commit(self, kind: str, content: str, workspace_id: str | None = None) -> dict:
        if kind not in IMPORT_KINDS:
            raise ValueError("Unsupported import kind")
        records, redactions = self._build(kind, content)
        batch_id = str(uuid4())
        for record in records:
            self.storage.append(self.records_file, {
                "record_id": str(uuid4()), "batch_id": batch_id, "workspace_id": workspace_id,
                "kind": kind, "content": record["content"], "imported_at": self._now(),
            })
        self._log("import_committed", f"Imported {len(records)} sanitized {kind} record(s) (batch {batch_id[:8]}).")
        return {
            "batch_id": batch_id, "kind": kind, "imported_count": len(records), "redactions": redactions,
            "note": "Saved sanitized records to the imported_records collection (not core collections); secrets were redacted.",
        }

    def list_records(self, kind: str | None = None, limit: int = 50) -> dict:
        records = self.storage.read_list(self.records_file)
        if kind:
            records = [r for r in records if r.get("kind") == kind]
        return {"records": list(reversed(records))[:limit], "total": len(self.storage.read_list(self.records_file))}

    def analytics_summary(self) -> dict:
        return {"import_center_records": len(self.storage.read_list(self.records_file))}

    def summary(self) -> dict:
        records = self.storage.read_list(self.records_file)
        by_kind: dict[str, int] = {}
        for r in records:
            by_kind[r.get("kind", "unknown")] = by_kind.get(r.get("kind", "unknown"), 0) + 1
        return {
            "supported_kinds": IMPORT_KINDS,
            "total_imported": len(records),
            "by_kind": by_kind,
            "note": "Imports are validated + sanitized before saving to a dedicated collection; secrets are redacted.",
        }
