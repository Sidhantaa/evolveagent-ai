from __future__ import annotations

import json
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


class GovernanceConsoleService:
    """v82.0 Governance Console 3.0 — make safety visible and trustworthy.

    A read-only console over the governance log: a **governance dashboard** (totals,
    blocked ratio, by action/risk/permission-level), **policy violations** (blocked
    events), **secret redactions** (secret/PII/redaction events), **prompt-injection
    warnings** (firewall/injection events), an **approval audit** (approval events),
    an **external-action audit** (action-level / MCP-execution events), and an
    **exportable governance report** (markdown/JSON). It reads existing governance
    events only and never mutates them. Viewing is itself governance-logged.
    """

    log_file = "governance_log.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _events(self) -> list[dict]:
        return [e for e in self.storage.read_list(self.log_file) if isinstance(e, dict)]

    @staticmethod
    def _has(event: dict, *needles: str) -> bool:
        blob = f"{event.get('action_type', '')} {event.get('task_type', '')} {event.get('tool_used', '')} {event.get('reason', '')}".lower()
        return any(n in blob for n in needles)

    def dashboard(self) -> dict:
        events = self._events()
        total = len(events)
        blocked = sum(1 for e in events if e.get("blocked"))
        by_action: dict[str, int] = {}
        by_risk = {"low": 0, "medium": 0, "high": 0}
        by_permission: dict[str, int] = {}
        for e in events:
            by_action[e.get("action_type", "unknown")] = by_action.get(e.get("action_type", "unknown"), 0) + 1
            risk = e.get("risk_score", 0) or 0
            by_risk["high" if risk >= 6 else "medium" if risk >= 3 else "low"] += 1
            lvl = e.get("permission_level", "unknown")
            by_permission[lvl] = by_permission.get(lvl, 0) + 1
        top_actions = sorted(by_action.items(), key=lambda x: x[1], reverse=True)[:10]

        self._log("governance_console_viewed", f"Rendered the governance console over {total} event(s).")
        return {
            "total_events": total,
            "blocked_events": blocked,
            "blocked_ratio_pct": round((blocked / total) * 100, 1) if total else 0,
            "by_risk": by_risk,
            "by_permission_level": by_permission,
            "top_actions": [{"action": a, "count": c} for a, c in top_actions],
            "policy_violations": self._policy_violations(events),
            "secret_redactions": self._secret_events(events),
            "prompt_injection_warnings": self._injection_events(events),
            "approval_audit": self._approval_events(events),
            "external_action_audit": self._external_events(events),
            "note": "Read-only aggregation of governance events — nothing is mutated.",
        }

    def _policy_violations(self, events: list[dict]) -> dict:
        rows = [{"action": e.get("action_type"), "reason": (e.get("reason") or "")[:160], "at": e.get("created_at")}
                for e in events if e.get("blocked")]
        return {"count": len(rows), "recent": list(reversed(rows))[:10]}

    def _secret_events(self, events: list[dict]) -> dict:
        rows = [e for e in events if self._has(e, "secret", "redact", "pii", "sensitive")]
        return {"count": len(rows), "recent": [(e.get("action_type"), (e.get("reason") or "")[:120]) for e in list(reversed(rows))[:8]]}

    def _injection_events(self, events: list[dict]) -> dict:
        rows = [e for e in events if self._has(e, "injection", "firewall", "prompt attack", "jailbreak")]
        return {"count": len(rows), "recent": [(e.get("action_type"), (e.get("reason") or "")[:120]) for e in list(reversed(rows))[:8]]}

    def _approval_events(self, events: list[dict]) -> dict:
        rows = [e for e in events if self._has(e, "approv") or e.get("action_type", "").endswith("_approval_required")]
        return {"count": len(rows), "recent": [(e.get("action_type"), (e.get("reason") or "")[:120]) for e in list(reversed(rows))[:8]]}

    def _external_events(self, events: list[dict]) -> dict:
        rows = [e for e in events if e.get("permission_level") == "action" or self._has(e, "mcp_exec", "execution", "external")]
        return {"count": len(rows), "recent": [(e.get("action_type"), e.get("tool_used")) for e in list(reversed(rows))[:8]]}

    def report(self, fmt: str = "markdown") -> dict:
        dash = self.dashboard()
        if fmt == "json":
            content = json.dumps(dash, indent=2, default=str)
        else:
            lines = ["# Governance Report", "", f"_Generated {self._now()}_", "",
                     f"- Total events: {dash['total_events']} · Blocked: {dash['blocked_events']} ({dash['blocked_ratio_pct']}%)",
                     f"- Risk mix — high: {dash['by_risk']['high']}, medium: {dash['by_risk']['medium']}, low: {dash['by_risk']['low']}",
                     f"- Policy violations: {dash['policy_violations']['count']}",
                     f"- Secret/PII events: {dash['secret_redactions']['count']}",
                     f"- Prompt-injection warnings: {dash['prompt_injection_warnings']['count']}",
                     f"- Approval-audit events: {dash['approval_audit']['count']}",
                     f"- External-action-audit events: {dash['external_action_audit']['count']}",
                     "", "## Top actions", *[f"- {a['action']}: {a['count']}" for a in dash["top_actions"]]]
            content = "\n".join(lines)
        self._log("governance_report_exported", f"Exported a governance report ({fmt}).")
        return {"format": fmt, "content": content}

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="governance_console",
                agent_name="Governance Console",
                action_type=action_type,
                tool_used="GovernanceConsoleService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def analytics_summary(self) -> dict:
        events = self._events()
        return {"governance_console_events": len(events), "governance_console_blocked": sum(1 for e in events if e.get("blocked"))}

    def summary(self) -> dict:
        events = self._events()
        return {
            "total_events": len(events),
            "blocked_events": sum(1 for e in events if e.get("blocked")),
            "note": "Read-only governance console over the governance log.",
        }
