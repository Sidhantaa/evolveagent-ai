from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

LEAD_STATUSES = ["new", "contacted", "qualified", "proposal_sent", "won", "lost"]
LEAD_SOURCES = ["manual", "chat", "file", "recording"]
SUPPORT_PRIORITIES = ["low", "medium", "high"]
SUPPORT_STATUSES = ["open", "waiting", "resolved", "escalated"]
DOCUMENT_TYPES = ["invoice", "contract", "proposal", "receipt", "other"]
PROPOSAL_STATUSES = ["draft", "reviewed", "sent_manually", "archived"]
MARKETING_CHANNELS = ["email", "linkedin", "website", "instagram", "other"]
MARKETING_STATUSES = ["planned", "drafted", "approved", "posted_manually"]

# Heuristic, local-only keyword sets for safe document processing.
_RISK_KEYWORDS = {
    "overdue": "Payment or task appears overdue.",
    "late fee": "Late fee clause detected.",
    "penalty": "Penalty clause detected.",
    "past due": "Account appears past due.",
    "auto-renew": "Auto-renewal clause detected.",
    "auto renew": "Auto-renewal clause detected.",
    "non-compete": "Non-compete clause detected.",
    "termination": "Termination clause detected.",
    "deadline": "Time-sensitive deadline detected.",
    "refund": "Refund-related content detected.",
    "dispute": "Possible dispute language detected.",
}
_ACTION_KEYWORDS = ("please", "need to", "must", "should", "follow up", "send", "review", "approve", "pay", "sign", "schedule")


class BusinessOperatorService:
    """v18.0 Real Business Automation Layer (Business Operator).

    Manages leads, support cases, document processing, proposals, a marketing
    calendar, and a KPI dashboard from local JSON storage only. Everything is
    draft/plan oriented: it never sends email, never makes payments, and never
    calls an external CRM. Every stateful action is logged through governance.
    """

    leads_file = "business_leads.json"
    support_file = "business_support_cases.json"
    documents_file = "business_documents.json"
    proposals_file = "business_proposals.json"
    marketing_file = "business_marketing_calendar.json"
    kpis_file = "business_kpis.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        text = str(value if value is not None else default).strip()
        return text[:max_length]

    def _filter_workspace(self, items: list[dict], workspace_id: str | None) -> list[dict]:
        if not workspace_id:
            return items
        return [item for item in items if item.get("workspace_id") == workspace_id]

    def _get(self, filename: str, key: str, value: str) -> dict | None:
        return next((item for item in self.storage.read_list(filename) if item.get(key) == value), None)

    def _update_record(self, filename: str, key: str, value: str, updates: dict, allowed: dict) -> dict:
        records = self.storage.read_list(filename)
        record = next((item for item in records if item.get(key) == value), None)
        if record is None:
            raise ValueError("Record not found")
        for field, validator in allowed.items():
            if updates.get(field) is not None:
                record[field] = validator(updates[field])
        record["updated_at"] = self._now()
        self.storage.write_list(filename, records)
        return record

    def _log(self, action_type: str, workspace_id: str | None, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                workspace_id=workspace_id,
                task_type="business_operator",
                agent_name="Business Operator",
                action_type=action_type,
                tool_used="BusinessOperatorService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    @staticmethod
    def _enum(value, allowed: list[str], default: str) -> str:
        candidate = str(value or "").strip().lower()
        return candidate if candidate in allowed else default

    # ------------------------------------------------------------------
    # Leads
    # ------------------------------------------------------------------
    def list_leads(self, workspace_id: str | None = None) -> list[dict]:
        return self._filter_workspace(self.storage.read_list(self.leads_file), workspace_id)

    def create_lead(self, data: dict) -> dict:
        lead = {
            "lead_id": str(uuid4()),
            "workspace_id": data.get("workspace_id"),
            "name": self._clean(data.get("name"), 160),
            "company": self._clean(data.get("company"), 160),
            "email": self._clean(data.get("email"), 200),
            "status": self._enum(data.get("status"), LEAD_STATUSES, "new"),
            "source": self._enum(data.get("source"), LEAD_SOURCES, "manual"),
            "notes": self._clean(data.get("notes"), 4000),
            "next_step": self._clean(data.get("next_step"), 500),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.leads_file, lead)
        self._log("business_lead_created", lead["workspace_id"], f"Created lead: {lead['name'] or lead['company'] or lead['lead_id']}.")
        return lead

    def update_lead(self, lead_id: str, updates: dict) -> dict:
        record = self._update_record(
            self.leads_file,
            "lead_id",
            lead_id,
            updates,
            {
                "name": lambda v: self._clean(v, 160),
                "company": lambda v: self._clean(v, 160),
                "email": lambda v: self._clean(v, 200),
                "status": lambda v: self._enum(v, LEAD_STATUSES, "new"),
                "source": lambda v: self._enum(v, LEAD_SOURCES, "manual"),
                "notes": lambda v: self._clean(v, 4000),
                "next_step": lambda v: self._clean(v, 500),
            },
        )
        self._log("business_lead_updated", record.get("workspace_id"), f"Updated lead {lead_id}.")
        return record

    # ------------------------------------------------------------------
    # Support cases (with local triage)
    # ------------------------------------------------------------------
    def list_support_cases(self, workspace_id: str | None = None) -> list[dict]:
        return self._filter_workspace(self.storage.read_list(self.support_file), workspace_id)

    def _triage(self, subject: str, description: str, priority: str) -> tuple[str, str]:
        snippet = (description or subject or "").strip()
        summary = f"{priority.capitalize()} priority. {snippet[:200]}".strip()
        draft_reply = (
            f"Hi,\n\nThanks for reaching out about \"{subject[:120]}\". "
            "We've received your request and are looking into it. "
            "We'll follow up shortly with an update.\n\nBest regards,\nSupport Team\n\n"
            "[DRAFT — review before sending. EvolveAgent never sends email automatically.]"
        )
        return summary, draft_reply

    def create_support_case(self, data: dict) -> dict:
        subject = self._clean(data.get("subject"), 200)
        description = self._clean(data.get("description"), 4000)
        priority = self._enum(data.get("priority"), SUPPORT_PRIORITIES, "medium")
        triage_summary, draft_reply = self._triage(subject, description, priority)
        case = {
            "case_id": str(uuid4()),
            "workspace_id": data.get("workspace_id"),
            "customer": self._clean(data.get("customer"), 160),
            "subject": subject,
            "description": description,
            "priority": priority,
            "status": self._enum(data.get("status"), SUPPORT_STATUSES, "open"),
            "triage_summary": triage_summary,
            "draft_reply": draft_reply,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.support_file, case)
        self._log("business_support_case_created", case["workspace_id"], f"Created support case: {subject or case['case_id']}.")
        return case

    def update_support_case(self, case_id: str, updates: dict) -> dict:
        record = self._update_record(
            self.support_file,
            "case_id",
            case_id,
            updates,
            {
                "customer": lambda v: self._clean(v, 160),
                "subject": lambda v: self._clean(v, 200),
                "description": lambda v: self._clean(v, 4000),
                "priority": lambda v: self._enum(v, SUPPORT_PRIORITIES, "medium"),
                "status": lambda v: self._enum(v, SUPPORT_STATUSES, "open"),
                "triage_summary": lambda v: self._clean(v, 1000),
                "draft_reply": lambda v: self._clean(v, 4000),
            },
        )
        self._log("business_support_case_updated", record.get("workspace_id"), f"Updated support case {case_id}.")
        return record

    # ------------------------------------------------------------------
    # Document processing (safe, local heuristics only)
    # ------------------------------------------------------------------
    def list_documents(self, workspace_id: str | None = None) -> list[dict]:
        return self._filter_workspace(self.storage.read_list(self.documents_file), workspace_id)

    def _process_content(self, content: str) -> tuple[str, list[str], list[str]]:
        text = (content or "").strip()
        lowered = text.lower()
        summary = text[:240] + ("…" if len(text) > 240 else "")
        action_items: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if any(keyword in stripped.lower() for keyword in _ACTION_KEYWORDS):
                action_items.append(stripped[:200])
            if len(action_items) >= 10:
                break
        risk_flags: list[str] = []
        for keyword, message in _RISK_KEYWORDS.items():
            if keyword in lowered and message not in risk_flags:
                risk_flags.append(message)
        return summary, action_items, risk_flags

    def process_document(self, data: dict) -> dict:
        content = self._clean(data.get("content"), 20000)
        summary, action_items, risk_flags = self._process_content(content)
        document = {
            "document_id": str(uuid4()),
            "workspace_id": data.get("workspace_id"),
            "title": self._clean(data.get("title"), 200),
            "document_type": self._enum(data.get("document_type"), DOCUMENT_TYPES, "other"),
            "content": content,
            "extracted_summary": summary,
            "action_items": action_items,
            "risk_flags": risk_flags,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.documents_file, document)
        self._log("business_document_processed", document["workspace_id"], f"Processed document: {document['title'] or document['document_id']}.")
        return document

    def update_document(self, document_id: str, updates: dict) -> dict:
        records = self.storage.read_list(self.documents_file)
        record = next((item for item in records if item.get("document_id") == document_id), None)
        if record is None:
            raise ValueError("Record not found")
        if updates.get("title") is not None:
            record["title"] = self._clean(updates["title"], 200)
        if updates.get("document_type") is not None:
            record["document_type"] = self._enum(updates["document_type"], DOCUMENT_TYPES, "other")
        if updates.get("content") is not None:
            record["content"] = self._clean(updates["content"], 20000)
            summary, action_items, risk_flags = self._process_content(record["content"])
            record["extracted_summary"] = summary
            record["action_items"] = action_items
            record["risk_flags"] = risk_flags
        record["updated_at"] = self._now()
        self.storage.write_list(self.documents_file, records)
        self._log("business_document_updated", record.get("workspace_id"), f"Updated document {document_id}.")
        return record

    # ------------------------------------------------------------------
    # Proposals (drafts only)
    # ------------------------------------------------------------------
    def list_proposals(self, workspace_id: str | None = None) -> list[dict]:
        return self._filter_workspace(self.storage.read_list(self.proposals_file), workspace_id)

    def _build_proposal_draft(self, title: str, client: str, scope: str) -> str:
        return (
            f"Proposal: {title}\nPrepared for: {client}\n\n"
            f"Scope of work:\n{scope}\n\n"
            "Next steps: review internally, then send manually.\n\n"
            "[DRAFT — EvolveAgent does not send proposals automatically.]"
        )

    def create_proposal(self, data: dict) -> dict:
        title = self._clean(data.get("title"), 200)
        client = self._clean(data.get("client"), 160)
        scope = self._clean(data.get("scope"), 4000)
        draft = self._clean(data.get("draft"), 8000) or self._build_proposal_draft(title, client, scope)
        proposal = {
            "proposal_id": str(uuid4()),
            "workspace_id": data.get("workspace_id"),
            "lead_id": self._clean(data.get("lead_id"), 120) or None,
            "title": title,
            "client": client,
            "scope": scope,
            "draft": draft,
            "status": self._enum(data.get("status"), PROPOSAL_STATUSES, "draft"),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.proposals_file, proposal)
        self._log("business_proposal_created", proposal["workspace_id"], f"Created proposal draft: {title or proposal['proposal_id']}.")
        return proposal

    def update_proposal(self, proposal_id: str, updates: dict) -> dict:
        record = self._update_record(
            self.proposals_file,
            "proposal_id",
            proposal_id,
            updates,
            {
                "lead_id": lambda v: self._clean(v, 120) or None,
                "title": lambda v: self._clean(v, 200),
                "client": lambda v: self._clean(v, 160),
                "scope": lambda v: self._clean(v, 4000),
                "draft": lambda v: self._clean(v, 8000),
                "status": lambda v: self._enum(v, PROPOSAL_STATUSES, "draft"),
            },
        )
        self._log("business_proposal_updated", record.get("workspace_id"), f"Updated proposal {proposal_id}.")
        return record

    # ------------------------------------------------------------------
    # Marketing calendar (drafts only)
    # ------------------------------------------------------------------
    def list_marketing_items(self, workspace_id: str | None = None) -> list[dict]:
        return self._filter_workspace(self.storage.read_list(self.marketing_file), workspace_id)

    def create_marketing_item(self, data: dict) -> dict:
        item = {
            "item_id": str(uuid4()),
            "workspace_id": data.get("workspace_id"),
            "title": self._clean(data.get("title"), 200),
            "channel": self._enum(data.get("channel"), MARKETING_CHANNELS, "other"),
            "scheduled_for": self._clean(data.get("scheduled_for"), 60),
            "status": self._enum(data.get("status"), MARKETING_STATUSES, "planned"),
            "draft_content": self._clean(data.get("draft_content"), 4000),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.marketing_file, item)
        self._log("business_marketing_item_created", item["workspace_id"], f"Created marketing item: {item['title'] or item['item_id']}.")
        return item

    def update_marketing_item(self, item_id: str, updates: dict) -> dict:
        record = self._update_record(
            self.marketing_file,
            "item_id",
            item_id,
            updates,
            {
                "title": lambda v: self._clean(v, 200),
                "channel": lambda v: self._enum(v, MARKETING_CHANNELS, "other"),
                "scheduled_for": lambda v: self._clean(v, 60),
                "status": lambda v: self._enum(v, MARKETING_STATUSES, "planned"),
                "draft_content": lambda v: self._clean(v, 4000),
            },
        )
        self._log("business_marketing_item_updated", record.get("workspace_id"), f"Updated marketing item {item_id}.")
        return record

    # ------------------------------------------------------------------
    # KPI dashboard
    # ------------------------------------------------------------------
    def dashboard(self, workspace_id: str | None = None) -> dict:
        leads = self.list_leads(workspace_id)
        cases = self.list_support_cases(workspace_id)
        documents = self.list_documents(workspace_id)
        proposals = self.list_proposals(workspace_id)
        marketing = self.list_marketing_items(workspace_id)

        won = sum(1 for lead in leads if lead.get("status") == "won")
        lost = sum(1 for lead in leads if lead.get("status") == "lost")
        qualified = sum(1 for lead in leads if lead.get("status") in {"qualified", "proposal_sent", "won"})
        closed = won + lost
        conversion_rate = round((won / closed) * 100, 2) if closed else 0

        activity = []
        for collection, label_key in (
            (leads, "name"),
            (cases, "subject"),
            (documents, "title"),
            (proposals, "title"),
            (marketing, "title"),
        ):
            for record in collection:
                activity.append(
                    {
                        "type": next(iter([k for k in ("lead_id", "case_id", "document_id", "proposal_id", "item_id") if k in record]), "record"),
                        "label": record.get(label_key) or record.get("company") or record.get("customer") or "",
                        "status": record.get("status"),
                        "updated_at": record.get("updated_at"),
                    }
                )
        activity.sort(key=lambda item: item.get("updated_at") or "", reverse=True)

        return {
            "workspace_id": workspace_id,
            "total_leads": len(leads),
            "qualified_leads": qualified,
            "open_support_cases": sum(1 for case in cases if case.get("status") in {"open", "waiting", "escalated"}),
            "high_priority_cases": sum(1 for case in cases if case.get("priority") == "high"),
            "proposal_count": len(proposals),
            "draft_proposals": sum(1 for proposal in proposals if proposal.get("status") == "draft"),
            "planned_marketing_items": sum(1 for item in marketing if item.get("status") == "planned"),
            "won_leads": won,
            "lost_leads": lost,
            "conversion_rate": conversion_rate,
            "document_count": len(documents),
            "recent_activity": activity[:10],
        }

    def workflow_summary(self, workspace_id: str | None = None) -> dict:
        kpis = self.dashboard(workspace_id)
        return {
            "headline": (
                f"{kpis['total_leads']} lead(s), {kpis['open_support_cases']} open case(s), "
                f"{kpis['draft_proposals']} draft proposal(s)."
            ),
            "kpis": kpis,
            "safety_notes": [
                "Drafts only — EvolveAgent never sends email automatically.",
                "No payments are processed and no external CRM is contacted.",
            ],
        }
