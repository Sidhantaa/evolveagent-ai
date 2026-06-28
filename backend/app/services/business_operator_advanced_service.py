from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

WORKFLOW_TYPES = ["lead_pipeline", "support_triage", "invoice_processing", "custom"]
WORKFLOW_STATUSES = ["queued", "in_review", "completed", "blocked"]
APPROVAL_KINDS = ["external_send", "payment", "high_risk", "data_share"]
APPROVAL_STATUSES = ["pending", "approved", "rejected"]


class BusinessOperatorAdvancedService:
    """v33.0 AI Business Operator Advanced.

    Extends the v18 Business Automation Layer (which exposes /api/business/*)
    with stronger operations workflows, reporting, KPI snapshots, an approval
    queue for risky/external actions, and an audit trail — under the new
    /api/business-operator/* surface. It reuses v18's stored business data and
    keeps ALL external actions draft-only: no real email send, no payment, no
    external CRM sync. Every stateful action is audited and governance-logged.
    """

    workflows_file = "business_workflows.json"
    approvals_file = "business_approval_items.json"
    reports_file = "business_reports.json"
    kpi_file = "business_kpi_snapshots.json"
    audit_file = "business_audit_records.json"

    # v18 collections (read-only here).
    leads_file = "business_leads.json"
    support_file = "business_support_cases.json"
    documents_file = "business_documents.json"
    proposals_file = "business_proposals.json"

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

    def _audit(self, event_type: str, ref_id: str, detail: str) -> None:
        self.storage.append(
            self.audit_file,
            {"audit_id": str(uuid4()), "event_type": event_type, "ref_id": ref_id, "detail": detail, "created_at": self._now()},
        )

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="business_operator_advanced",
                agent_name="Business Operator Advanced",
                action_type=action_type,
                tool_used="BusinessOperatorAdvancedService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=6,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Workflows
    # ------------------------------------------------------------------
    def list_workflows(self) -> list[dict]:
        return self.storage.read_list(self.workflows_file)

    def create_workflow(self, data: dict) -> dict:
        wf_type = self._enum(data.get("workflow_type"), WORKFLOW_TYPES, "custom")
        workflow = {
            "workflow_id": str(uuid4()),
            "workflow_type": wf_type,
            "title": self._clean(data.get("title"), 200) or wf_type.replace("_", " ").title(),
            "context": self._clean(data.get("context"), 2000),
            "next_steps": self._suggest_next_steps(wf_type),
            "status": self._enum(data.get("status"), WORKFLOW_STATUSES, "queued"),
            "draft_only": True,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.workflows_file, workflow)
        self._audit("workflow_created", workflow["workflow_id"], f"{wf_type} workflow created.")
        self._log("business_workflow_created", f"Created {wf_type} workflow {workflow['workflow_id']}.")
        return workflow

    def _suggest_next_steps(self, wf_type: str) -> list[str]:
        if wf_type == "lead_pipeline":
            return ["Review qualified leads", "Draft follow-up (no real send)", "Advance stage with approval"]
        if wf_type == "support_triage":
            return ["Sort by severity", "Draft response (review before sending)", "Escalate high-severity cases"]
        if wf_type == "invoice_processing":
            return ["Extract amounts and dates", "Flag risks", "Route payment to approval queue (no real payment)"]
        return ["Define the workflow goal", "List safe next steps", "Route risky actions to approvals"]

    # ------------------------------------------------------------------
    # Reports + KPI snapshots
    # ------------------------------------------------------------------
    def _business_kpis(self) -> dict:
        leads = self.storage.read_list(self.leads_file)
        cases = self.storage.read_list(self.support_file)
        proposals = self.storage.read_list(self.proposals_file)
        won = sum(1 for lead in leads if lead.get("status") == "won")
        lost = sum(1 for lead in leads if lead.get("status") == "lost")
        closed = won + lost
        return {
            "total_leads": len(leads),
            "won_leads": won,
            "lost_leads": lost,
            "conversion_rate": round((won / closed) * 100, 2) if closed else 0,
            "open_support_cases": sum(1 for c in cases if c.get("status") in {"open", "waiting", "escalated"}),
            "high_priority_cases": sum(1 for c in cases if c.get("priority") == "high"),
            "proposals": len(proposals),
        }

    def create_report(self, data: dict) -> dict:
        kpis = self._business_kpis()
        report = {
            "report_id": str(uuid4()),
            "title": self._clean(data.get("title"), 200) or "Business operations report",
            "period": self._clean(data.get("period"), 40) or "current",
            "kpis": kpis,
            "headline": (
                f"{kpis['total_leads']} lead(s), {kpis['conversion_rate']}% conversion, "
                f"{kpis['open_support_cases']} open case(s)."
            ),
            "created_at": self._now(),
        }
        self.storage.append(self.reports_file, report)
        self._audit("report_created", report["report_id"], "Business report generated.")
        self._log("business_report_created", f"Generated business report {report['report_id']}.")
        return report

    def list_reports(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.reports_file)[-limit:]))

    def create_kpi_snapshot(self) -> dict:
        snapshot = {
            "snapshot_id": str(uuid4()),
            "kpis": self._business_kpis(),
            "created_at": self._now(),
        }
        self.storage.append(self.kpi_file, snapshot)
        self._audit("kpi_snapshot_created", snapshot["snapshot_id"], "KPI snapshot captured.")
        self._log("business_kpi_snapshot_created", f"Captured KPI snapshot {snapshot['snapshot_id']}.")
        return snapshot

    def list_kpi_snapshots(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.kpi_file)[-limit:]))

    # ------------------------------------------------------------------
    # Approvals (for external-send / payment / high-risk — draft only)
    # ------------------------------------------------------------------
    def create_approval(self, data: dict) -> dict:
        approval = {
            "approval_id": str(uuid4()),
            "kind": self._enum(data.get("kind"), APPROVAL_KINDS, "high_risk"),
            "title": self._clean(data.get("title"), 200),
            "detail": self._clean(data.get("detail"), 2000),
            "status": "pending",
            "note": "Draft only — approving records a decision; no real send/payment/CRM action is performed.",
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.approvals_file, approval)
        self._audit("approval_created", approval["approval_id"], f"{approval['kind']} approval requested.")
        self._log("business_approval_created", f"Created approval item {approval['approval_id']} ({approval['kind']}).")
        return approval

    def list_approvals(self) -> list[dict]:
        return self.storage.read_list(self.approvals_file)

    def update_approval(self, approval_id: str, decision: str) -> dict:
        approvals = self.storage.read_list(self.approvals_file)
        approval = next((a for a in approvals if a.get("approval_id") == approval_id), None)
        if approval is None:
            raise ValueError("Approval not found")
        resolved = self._enum(decision, ["approved", "rejected"], "rejected")
        approval["status"] = resolved
        approval["updated_at"] = self._now()
        self.storage.write_list(self.approvals_file, approvals)
        self._audit("approval_decided", approval_id, f"Approval {resolved} (no real external action executed).")
        self._log("business_approval_updated", f"Approval {approval_id} {resolved}.")
        return approval

    # ------------------------------------------------------------------
    # Audit + dashboard
    # ------------------------------------------------------------------
    def audit_log(self, limit: int = 50) -> list[dict]:
        return list(reversed(self.storage.read_list(self.audit_file)[-limit:]))

    def dashboard(self) -> dict:
        workflows = self.list_workflows()
        approvals = self.list_approvals()
        return {
            "total_workflows": len(workflows),
            "blocked_workflows": sum(1 for w in workflows if w.get("status") == "blocked"),
            "pending_approvals": sum(1 for a in approvals if a.get("status") == "pending"),
            "total_reports": len(self.storage.read_list(self.reports_file)),
            "total_kpi_snapshots": len(self.storage.read_list(self.kpi_file)),
            "audit_event_count": len(self.storage.read_list(self.audit_file)),
            "kpis": self._business_kpis(),
            "draft_only": True,
            "safety_note": "Draft-only operations — no real email send, no payment, no external CRM sync. Risky actions go to the approval queue.",
        }
