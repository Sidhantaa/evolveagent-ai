from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

_STATUS_SCORE = {"ok": 100, "warn": 60, "critical": 20, "info": 100}


class HealthMonitorService:
    """v49.0 Health & Readiness Monitor.

    A read-only aggregation of platform health signals derived from local state —
    governance (blocked ratio), approvals backlog (MCP + business), secret-key
    readiness, MCP connectors, and policy posture — scored into a single health
    dashboard with per-check status (ok/warn/critical/info) and recommendations.
    It performs no actions; it only reads existing collections and can persist a
    health snapshot. Snapshot creation is governance-logged.
    """

    snapshots_file = "health_snapshots.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------
    def _checks(self) -> list[dict]:
        checks: list[dict] = []

        # Governance health — blocked ratio.
        gov = self.storage.read_list("governance_log.json")
        blocked = sum(1 for e in gov if e.get("blocked"))
        ratio = (blocked / len(gov)) if gov else 0
        checks.append({
            "name": "governance",
            "status": "ok" if ratio < 0.2 else "warn" if ratio < 0.5 else "critical",
            "detail": f"{blocked} blocked of {len(gov)} events ({round(ratio * 100)}%).",
            "value": blocked,
        })

        # Approvals backlog — MCP executions + business-operator pending.
        mcp_pending = sum(1 for r in self.storage.read_list("mcp_execution_requests.json") if r.get("status") == "pending_approval")
        biz_pending = sum(1 for a in self.storage.read_list("business_approval_items.json") if a.get("status") == "pending")
        backlog = mcp_pending + biz_pending
        checks.append({
            "name": "approvals_backlog",
            "status": "ok" if backlog == 0 else "warn" if backlog < 10 else "critical",
            "detail": f"{backlog} pending approval(s) ({mcp_pending} MCP, {biz_pending} business).",
            "value": backlog,
        })

        # Secret readiness — registered refs whose env key is unset.
        refs = self.storage.read_list("mcp_secret_refs.json")
        import os
        unset = sum(1 for r in refs if not (os.environ.get(r.get("key_name", "")) or "").strip())
        checks.append({
            "name": "secret_readiness",
            "status": "ok" if unset == 0 else "warn",
            "detail": f"{unset} of {len(refs)} registered secret reference(s) not set." if refs else "No secret references registered.",
            "value": unset,
        })

        # MCP connectors — informational posture.
        connectors = self.storage.read_list("mcp_connectors.json")
        enabled = sum(1 for c in connectors if c.get("enabled"))
        checks.append({
            "name": "mcp_connectors",
            "status": "info",
            "detail": f"{enabled} of {len(connectors)} connector(s) enabled.",
            "value": enabled,
        })

        # Policy posture — informational.
        policies = self.storage.read_list("mcp_policies.json")
        active = sum(1 for p in policies if p.get("enabled", True))
        checks.append({
            "name": "policies",
            "status": "info",
            "detail": f"{active} active deny policy/policies.",
            "value": active,
        })

        return checks

    def _score(self, checks: list[dict]) -> int:
        scored = [_STATUS_SCORE.get(c["status"], 100) for c in checks if c["status"] != "info"]
        return round(sum(scored) / len(scored)) if scored else 100

    def _recommendations(self, checks: list[dict]) -> list[str]:
        recs = []
        for c in checks:
            if c["status"] == "critical":
                recs.append(f"CRITICAL — {c['name']}: {c['detail']}")
            elif c["status"] == "warn":
                recs.append(f"Review {c['name']}: {c['detail']}")
        if not recs:
            recs.append("All monitored checks are healthy.")
        return recs

    # ------------------------------------------------------------------
    # Dashboard + snapshots
    # ------------------------------------------------------------------
    def dashboard(self) -> dict:
        checks = self._checks()
        score = self._score(checks)
        return {
            "health_score": score,
            "status": "healthy" if score >= 80 else "degraded" if score >= 50 else "unhealthy",
            "checks": checks,
            "recommendations": self._recommendations(checks),
            "snapshot_count": len(self.storage.read_list(self.snapshots_file)),
            "note": "Read-only aggregation of local health signals — no actions are taken.",
        }

    def create_snapshot(self) -> dict:
        checks = self._checks()
        snapshot = {
            "snapshot_id": str(uuid4()),
            "health_score": self._score(checks),
            "checks": checks,
            "created_at": self._now(),
        }
        self.storage.append(self.snapshots_file, snapshot)
        self.governance.log_event(
            GovernanceEvent(
                task_type="health_monitor",
                agent_name="Health & Readiness Monitor",
                action_type="health_snapshot_created",
                tool_used="HealthMonitorService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=3,
                reason=f"Health snapshot (score {snapshot['health_score']}).",
            )
        )
        return snapshot

    def list_snapshots(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.snapshots_file)[-limit:]))

    def analytics_summary(self) -> dict:
        checks = self._checks()
        return {
            "health_score": self._score(checks),
            "health_warn_checks": sum(1 for c in checks if c["status"] == "warn"),
            "health_critical_checks": sum(1 for c in checks if c["status"] == "critical"),
        }
