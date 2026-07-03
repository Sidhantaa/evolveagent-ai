from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

CATEGORIES = ["api_key", "token", "webhook", "database", "other"]


class MCPSecretRegistryService:
    """v47.0 Secret Reference Registry (references only — never values).

    A local catalog of *which* secret/env keys the MCP connectors (and other
    integrations) need — with readiness (is the env var set? true/false), an
    owner label, a category, and rotation reminders. It records only the **key
    name**; it never stores, reads, logs, or returns the secret value. Readiness
    is derived from ``os.environ`` as a boolean. Stateful actions are
    governance-logged.
    """

    refs_file = "mcp_secret_refs.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _enum(self, value, allowed: list[str], default: str) -> str:
        candidate = str(value or "").strip().lower()
        return candidate if candidate in allowed else default

    @staticmethod
    def _is_set(key_name: str) -> bool:
        value = os.environ.get(key_name)
        return bool(value and value.strip())

    def _rotation_due(self, ref: dict) -> bool:
        days = ref.get("rotation_days") or 0
        if not days:
            return False
        last = ref.get("last_rotated_at") or ref.get("created_at")
        if not last:
            return True
        try:
            last_dt = datetime.fromisoformat(last)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=UTC)
        except (ValueError, TypeError):
            return True
        return datetime.now(UTC) >= last_dt + timedelta(days=days)

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="mcp_secret_registry",
                agent_name="Secret Reference Registry",
                action_type=action_type,
                tool_used="MCPSecretRegistryService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=6,
                reason=reason,
            )
        )

    def _present(self, ref: dict) -> dict:
        """Return a ref safe for API/UI — key name + readiness bool only, never a value."""
        out = dict(ref)
        out.pop("value", None)  # defensive: never expose any value field
        out["is_set"] = self._is_set(ref.get("key_name", ""))
        out["rotation_due"] = self._rotation_due(ref)
        return out

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def list_refs(self) -> list[dict]:
        return [self._present(r) for r in self.storage.read_list(self.refs_file)]

    def _raw(self) -> list[dict]:
        return self.storage.read_list(self.refs_file)

    def register_ref(self, data: dict) -> dict:
        data = data or {}
        ref = {
            "ref_id": str(uuid4()),
            "key_name": self._clean(data.get("key_name"), 120) or "SECRET_KEY",
            "label": self._clean(data.get("label"), 160),
            "owner": self._clean(data.get("owner"), 120),
            "category": self._enum(data.get("category"), CATEGORIES, "api_key"),
            "connector_slug": self._clean(data.get("connector_slug"), 60).lower() or None,
            "rotation_days": max(0, min(3650, int(data.get("rotation_days") or 0))) if str(data.get("rotation_days") or "").strip().isdigit() else 0,
            "last_rotated_at": None,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.refs_file, ref)
        self._log("secret_ref_registered", f"Registered secret reference '{ref['key_name']}' (no value stored).")
        return self._present(ref)

    def update_ref(self, ref_id: str, data: dict) -> dict:
        refs = self._raw()
        ref = next((r for r in refs if r.get("ref_id") == ref_id), None)
        if ref is None:
            raise ValueError("Secret reference not found")
        data = data or {}
        if data.get("label") is not None:
            ref["label"] = self._clean(data["label"], 160)
        if data.get("owner") is not None:
            ref["owner"] = self._clean(data["owner"], 120)
        if data.get("category") is not None:
            ref["category"] = self._enum(data["category"], CATEGORIES, ref["category"])
        if data.get("rotation_days") is not None:
            try:
                ref["rotation_days"] = max(0, min(3650, int(data["rotation_days"])))
            except (TypeError, ValueError):
                pass
        # Never accept a value field.
        ref.pop("value", None)
        ref["updated_at"] = self._now()
        self.storage.write_list(self.refs_file, refs)
        self._log("secret_ref_updated", f"Updated secret reference {ref_id}.")
        return self._present(ref)

    def mark_rotated(self, ref_id: str) -> dict:
        refs = self._raw()
        ref = next((r for r in refs if r.get("ref_id") == ref_id), None)
        if ref is None:
            raise ValueError("Secret reference not found")
        ref["last_rotated_at"] = self._now()
        ref["updated_at"] = self._now()
        self.storage.write_list(self.refs_file, refs)
        self._log("secret_ref_rotated", f"Marked secret reference {ref_id} as rotated (no value handled).")
        return self._present(ref)

    # ------------------------------------------------------------------
    # Summary + analytics
    # ------------------------------------------------------------------
    def summary(self) -> dict:
        refs = self.list_refs()
        return {
            "total_refs": len(refs),
            "set_count": sum(1 for r in refs if r["is_set"]),
            "unset_count": sum(1 for r in refs if not r["is_set"]),
            "rotation_due_count": sum(1 for r in refs if r["rotation_due"]),
            "refs": refs,
            "note": "Reference catalog only — key names and readiness (set/unset). Secret values are never stored, logged, or returned.",
        }

    def analytics_summary(self) -> dict:
        refs = self.list_refs()
        return {
            "mcp_secret_refs_total": len(refs),
            "mcp_secret_refs_set": sum(1 for r in refs if r["is_set"]),
            "mcp_secret_refs_rotation_due": sum(1 for r in refs if r["rotation_due"]),
        }
