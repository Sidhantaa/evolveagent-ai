from __future__ import annotations

import json
import re
from collections import Counter
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


class ComplianceService:
    policies_filename = "compliance_policies.json"
    reports_filename = "compliance_reports.json"

    pii_patterns: list[tuple[str, re.Pattern[str]]] = [
        ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
        ("phone", re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")),
        ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
        ("credit_card", re.compile(r"\b(?:\d[ -]*?){13,16}\b")),
        ("ip_address", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ]

    default_policies: list[dict[str, Any]] = [
        {
            "collection": "messages.json",
            "retention_days": 365,
            "action": "review",
            "enabled": True,
            "description": "Review old chat messages before retaining or archiving.",
        },
        {
            "collection": "files.json",
            "retention_days": 90,
            "action": "review",
            "enabled": True,
            "description": "Review uploaded file metadata and extracted text references.",
        },
        {
            "collection": "recordings.json",
            "retention_days": 90,
            "action": "review",
            "enabled": True,
            "description": "Review recording metadata and transcript retention.",
        },
        {
            "collection": "governance_log.json",
            "retention_days": 730,
            "action": "keep",
            "enabled": True,
            "description": "Keep governance events longer for auditability.",
        },
        {
            "collection": "agent_analytics.json",
            "retention_days": 365,
            "action": "keep",
            "enabled": True,
            "description": "Keep aggregate analytics for workflow evaluation.",
        },
    ]

    def __init__(self, storage: StorageService, governance: GovernanceService):
        self.storage = storage
        self.governance = governance
        self._ensure_default_policies()

    def scan_pii(self, text: str | None, redact: bool = True) -> dict[str, Any]:
        source = text or ""
        detected_types: list[str] = []
        redaction_count = 0
        redacted = source
        for label, pattern in self.pii_patterns:
            matches = pattern.findall(source)
            if matches:
                detected_types.append(label)
                redaction_count += len(matches)
                if redact:
                    redacted = pattern.sub(f"[REDACTED_{label.upper()}]", redacted)
        return {
            "status": "redacted" if redaction_count else "passed",
            "pii_detected": redaction_count > 0,
            "redaction_count": redaction_count,
            "detected_types": detected_types,
            "redacted_text": redacted if redact else "",
            "recommendation": (
                "PII-like values were detected and redacted for compliance review."
                if redaction_count
                else "No PII-like values were detected."
            ),
        }

    def policies(self) -> list[dict[str, Any]]:
        return self.storage.read_list(self.policies_filename)

    def upsert_policy(self, collection: str, updates: dict[str, Any]) -> dict[str, Any]:
        policies = self.policies()
        existing = next((item for item in policies if item.get("collection") == collection), None)
        now = datetime.now(UTC).isoformat()
        if existing:
            existing.update(
                {
                    key: value
                    for key, value in updates.items()
                    if key in {"retention_days", "action", "enabled", "description"} and value is not None
                }
            )
            existing["updated_at"] = now
        else:
            existing = {
                "collection": collection,
                "retention_days": int(updates.get("retention_days") or 365),
                "action": updates.get("action") or "review",
                "enabled": bool(updates.get("enabled", True)),
                "description": updates.get("description") or "Workspace compliance retention policy.",
                "created_at": now,
                "updated_at": now,
            }
            policies.append(existing)
        self.storage.write_list(self.policies_filename, policies)
        self.governance.log_event(
            {
                "task_type": "compliance",
                "agent_name": "Compliance Service",
                "action_type": "retention_policy_updated",
                "tool_used": "ComplianceService",
                "permission_level": "plan_only",
                "approved": True,
                "blocked": False,
                "risk_score": 10,
                "reason": f"Retention policy updated for {collection}.",
            }
        )
        return existing

    def retention_review(self, workspace_id: str | None = None) -> dict[str, Any]:
        reviews: list[dict[str, Any]] = []
        now = datetime.now(UTC)
        for policy in self.policies():
            if not policy.get("enabled", True):
                continue
            collection = policy["collection"]
            records = self._filter_workspace(self.storage.read_list(collection), workspace_id)
            stale = [item for item in records if self._age_days(item, now) >= int(policy.get("retention_days", 365))]
            reviews.append(
                {
                    "collection": collection,
                    "retention_days": policy.get("retention_days"),
                    "action": policy.get("action"),
                    "total_records": len(records),
                    "records_needing_review": len(stale),
                    "oldest_record_age_days": max([self._age_days(item, now) for item in records], default=0),
                    "recommendation": self._retention_recommendation(policy, stale),
                }
            )
        return {
            "workspace_id": workspace_id,
            "policies": self.policies(),
            "reviews": reviews,
            "review_only": True,
            "note": "Retention review never deletes data automatically.",
        }

    def audit_events(
        self,
        workspace_id: str | None = None,
        action_type: str | None = None,
        blocked: bool | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        events = self._filter_workspace(self.storage.read_list("governance_log.json"), workspace_id)
        if action_type:
            events = [event for event in events if event.get("action_type") == action_type]
        if blocked is not None:
            events = [event for event in events if bool(event.get("blocked")) is blocked]
        return list(reversed(events[-limit:]))

    def admin_summary(self, workspace_id: str | None = None) -> dict[str, Any]:
        events = self._filter_workspace(self.storage.read_list("governance_log.json"), workspace_id)
        blocked = [event for event in events if event.get("blocked")]
        actions = Counter(event.get("action_type", "unknown") for event in events)
        permissions = Counter(event.get("permission_level", "unknown") for event in events)
        return {
            "workspace_id": workspace_id,
            "total_audit_events": len(events),
            "blocked_actions": len(blocked),
            "high_risk_events": sum(1 for event in events if int(event.get("risk_score") or 0) >= 70),
            "top_actions": actions.most_common(8),
            "permission_levels": dict(permissions),
            "retention_collections": len(self.policies()),
            "admin_recommendations": self._admin_recommendations(events, blocked),
        }

    def compliance_report(self, workspace_id: str | None = None) -> dict[str, Any]:
        events = self._filter_workspace(self.storage.read_list("governance_log.json"), workspace_id)
        retention = self.retention_review(workspace_id)
        admin = self.admin_summary(workspace_id)
        pii_summary = self._pii_summary(workspace_id)
        report = {
            "report_id": str(uuid4()),
            "workspace_id": workspace_id,
            "created_at": datetime.now(UTC).isoformat(),
            "summary": {
                "total_audit_events": len(events),
                "blocked_actions": admin["blocked_actions"],
                "high_risk_events": admin["high_risk_events"],
                "retention_items_needing_review": sum(item["records_needing_review"] for item in retention["reviews"]),
                "pii_findings": pii_summary["total_findings"],
            },
            "audit": {
                "recent_events": list(reversed(events[-25:])),
                "action_counts": dict(Counter(event.get("action_type", "unknown") for event in events)),
            },
            "retention": retention,
            "pii": pii_summary,
            "admin": admin,
        }
        self.storage.append(self.reports_filename, report)
        return report

    def export_report(self, workspace_id: str | None = None, format: str = "json") -> str:
        report = self.compliance_report(workspace_id)
        if format == "json":
            return json.dumps(report, indent=2)
        if format != "markdown":
            raise ValueError("format must be json or markdown")
        summary = report["summary"]
        lines = [
            "# EvolveAgent AI Compliance Report",
            "",
            f"Generated: {report['created_at']}",
            f"Workspace: {workspace_id or 'all'}",
            "",
            "## Summary",
            f"- Audit events: {summary['total_audit_events']}",
            f"- Blocked actions: {summary['blocked_actions']}",
            f"- High-risk events: {summary['high_risk_events']}",
            f"- Retention items needing review: {summary['retention_items_needing_review']}",
            f"- PII findings: {summary['pii_findings']}",
            "",
            "## Retention Review",
        ]
        for item in report["retention"]["reviews"]:
            lines.append(
                f"- {item['collection']}: {item['records_needing_review']} of {item['total_records']} need {item['action']}"
            )
        lines.extend(["", "## Admin Recommendations"])
        lines.extend(f"- {item}" for item in report["admin"]["admin_recommendations"])
        return "\n".join(lines) + "\n"

    def _ensure_default_policies(self) -> None:
        current = self.storage.read_list(self.policies_filename)
        if current:
            return
        now = datetime.now(UTC).isoformat()
        self.storage.write_list(
            self.policies_filename,
            [dict(policy, created_at=now, updated_at=now) for policy in self.default_policies],
        )

    @staticmethod
    def _filter_workspace(items: list[dict[str, Any]], workspace_id: str | None) -> list[dict[str, Any]]:
        if not workspace_id:
            return items
        return [item for item in items if item.get("workspace_id") in {workspace_id, None}]

    @staticmethod
    def _age_days(item: dict[str, Any], now: datetime) -> int:
        stamp = item.get("created_at") or item.get("updated_at")
        if not stamp:
            return 0
        try:
            parsed = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        except ValueError:
            return 0
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return max((now - parsed).days, 0)

    @staticmethod
    def _retention_recommendation(policy: dict[str, Any], stale: list[dict[str, Any]]) -> str:
        if not stale:
            return "No records currently need retention review."
        return f"{len(stale)} record(s) should be reviewed for {policy.get('action', 'review')}."

    def _pii_summary(self, workspace_id: str | None) -> dict[str, Any]:
        findings = Counter()
        scanned_collections = ("messages.json", "workspace_memory.json", "files.json", "recordings.json")
        for collection in scanned_collections:
            for item in self._filter_workspace(self.storage.read_list(collection), workspace_id):
                text = " ".join(str(item.get(key, "")) for key in ("content", "text_preview", "transcript", "title", "filename"))
                result = self.scan_pii(text, redact=False)
                for label in result["detected_types"]:
                    findings[label] += 1
        return {
            "total_findings": sum(findings.values()),
            "findings_by_type": dict(findings),
            "scanned_collections": list(scanned_collections),
        }

    @staticmethod
    def _admin_recommendations(events: list[dict[str, Any]], blocked: list[dict[str, Any]]) -> list[str]:
        recommendations = []
        if blocked:
            recommendations.append("Review blocked governance events before enabling higher automation permissions.")
        if any(event.get("action_type") == "secret_redaction" for event in events):
            recommendations.append("Rotate any exposed secret-like values and keep them out of prompts/files.")
        if not events:
            recommendations.append("No governance events recorded yet; run normal workflows to populate audit data.")
        if not recommendations:
            recommendations.append("Governance posture looks normal for the current workspace.")
        return recommendations
