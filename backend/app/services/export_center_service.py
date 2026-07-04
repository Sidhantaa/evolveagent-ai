from __future__ import annotations

import json
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Export kind → (collections, title field candidates). Read-only; secrets/governance excluded.
EXPORT_KINDS = {
    "chats": (["chat_sessions.json"], ["title", "name"]),
    "reports": (["portfolio_reports.json", "business_reports.json"], ["title", "headline", "name"]),
    "goals": (["goals.json"], ["title", "name"]),
    "memory": (["workspace_memory.json"], ["title", "key"]),
    "imported": (["imported_records.json"], ["content"]),
}
FORMATS = ["markdown", "json"]


class ExportCenterService:
    """v85.0 Export Center — make outputs portable.

    Read-only export of selected local data — **chats**, **reports**, **goals**,
    **memory**, **imported** records — as **markdown** or **JSON**, plus a **portfolio
    case-study** export and a **package builder** that bundles several kinds into one
    document. (PDF is produced client-side via print — the API returns markdown/JSON.)
    It excludes secrets, governance logs, and analytics, and never mutates data.
    Governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _title(item: dict, keys: list[str]) -> str:
        for key in keys:
            if isinstance(item.get(key), str) and item[key].strip():
                return item[key][:120]
        return "(untitled)"

    def _collect(self, kind: str, workspace_id: str | None) -> list[dict]:
        collections, title_keys = EXPORT_KINDS[kind]
        rows = []
        for collection in collections:
            for item in self.storage.read_list(collection):
                if not isinstance(item, dict):
                    continue
                if workspace_id and item.get("workspace_id") not in (None, workspace_id):
                    continue
                rows.append({"title": self._title(item, title_keys),
                             "created_at": item.get("created_at") or item.get("imported_at") or ""})
        return rows

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="export_center",
                agent_name="Export Center",
                action_type=action_type,
                tool_used="ExportCenterService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def export(self, kind: str, fmt: str = "markdown", workspace_id: str | None = None) -> dict:
        if kind not in EXPORT_KINDS:
            raise ValueError("Unsupported export kind")
        fmt = fmt if fmt in FORMATS else "markdown"
        rows = self._collect(kind, workspace_id)
        if fmt == "json":
            content = json.dumps(rows, indent=2, default=str)
        else:
            lines = [f"# Export: {kind}", "", f"_Generated {self._now()} · {len(rows)} item(s)_", ""]
            lines += [f"- {r['title']}" + (f" ({str(r['created_at'])[:10]})" if r["created_at"] else "") for r in rows]
            content = "\n".join(lines)
        self._log("export_generated", f"Exported {len(rows)} {kind} item(s) as {fmt}.")
        return {"kind": kind, "format": fmt, "item_count": len(rows), "content": content,
                "note": "Read-only export — excludes secrets, governance, and analytics; PDF via client-side print."}

    def case_study(self) -> dict:
        lines = [
            "# EvolveAgent AI — Portfolio Case Study", "",
            "A local-first, multi-agent AI operating system (FastAPI + React).", "",
            "## What it is",
            "A governed orchestration platform: a Master Agent routes each request across specialist subsystems,",
            "every stateful action is governance-logged, and Simple/Developer modes expose the right level of detail.", "",
            "## Scale",
            "80+ iterative versions on one additive pattern — routing, search, timelines, dashboards, a feature",
            "registry, MCP tool-connection, intelligence layers (context/agent-quality/workflow/document/code/",
            "research/meeting/collaboration), and platform-level safety (permissions, governance console, data",
            "manager, import/export).", "",
            "## Safety",
            "Local-first, planning-first, no unrestricted shell, no real send/pay/deploy without approval,",
            "boolean-only secret readiness, per-action governance logging. Not AGI — a governed orchestration layer.",
        ]
        self._log("export_case_study", "Exported the portfolio case study.")
        return {"format": "markdown", "content": "\n".join(lines)}

    def package(self, kinds: list[str], fmt: str = "markdown", workspace_id: str | None = None) -> dict:
        selected = [k for k in kinds if k in EXPORT_KINDS] or list(EXPORT_KINDS.keys())
        parts = {k: self.export(k, fmt, workspace_id) for k in selected}
        if fmt == "json":
            content = json.dumps({k: json.loads(v["content"]) for k, v in parts.items()}, indent=2, default=str)
        else:
            content = "\n\n---\n\n".join(v["content"] for v in parts.values())
        total = sum(v["item_count"] for v in parts.values())
        self._log("export_package_built", f"Built an export package of {len(selected)} kind(s), {total} item(s).")
        return {"kinds": selected, "format": fmt, "total_items": total, "content": content}

    def analytics_summary(self) -> dict:
        return {"export_center_kinds": len(EXPORT_KINDS)}

    def summary(self) -> dict:
        return {"supported_kinds": list(EXPORT_KINDS.keys()), "formats": FORMATS,
                "note": "Read-only export of selected local data; excludes secrets/governance/analytics; PDF via client print."}
