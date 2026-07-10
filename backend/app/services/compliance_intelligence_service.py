from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.secret_scanner import SecretScanner
from app.services.storage_service import StorageService

DISCLAIMER = "This is not legal advice. It produces checklists, warnings, and audit material for human review."
# v190 — a genuine audit package embeds a real, immutable point-in-time
# snapshot (a real auditor needs "what it looked like on the audit date", not
# a view that silently changes afterward) — capped so one export can't balloon
# storage unbounded.
_MAX_AUDIT_EVENTS = 1000
POLICY_STATUSES = ["draft", "active", "archived"]

# Local PII / PHI classifiers (heuristic). Secrets use the existing SecretScanner.
_PII_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
}
_PHI_KEYWORDS = {
    "diagnosis", "patient", "prescription", "mrn", "medical record", "treatment",
    "phi", "hipaa", "icd-10", "health record", "lab result",
}
_CONTRACT_RISK_KEYWORDS = {
    "indemnity": "Indemnification clause — review liability exposure.",
    "non-compete": "Non-compete clause detected.",
    "auto-renew": "Auto-renewal clause — confirm cancellation terms.",
    "termination": "Termination clause — review notice period.",
    "liability": "Liability clause — review caps and exclusions.",
    "governing law": "Governing-law clause — confirm jurisdiction.",
    "confidential": "Confidentiality clause detected.",
    "penalty": "Penalty clause detected.",
}


class ComplianceIntelligenceService:
    """v34.0 Legal / Compliance Intelligence Layer.

    Creates policies, classifies sensitive data (PII/PHI/secrets), reviews
    contracts/checklists with risk flags, runs HIPAA/PHI warning workflows, and
    generates audit packages from governance + findings. It is NOT legal advice;
    it produces checklists, warnings, and audit material for human review. Every
    stateful action is governance-logged.

    v190: an audit package used to be only a summary of counts — real numbers,
    but nothing a compliance officer could actually hand to an auditor. Every
    package now embeds a real, capped, point-in-time snapshot of the
    governance log, sensitive-data findings, policies, checklists, and
    contract reviews at the moment it was generated (immutable by design — a
    real audit record shouldn't silently change after the fact).
    """

    policies_file = "compliance_intel_policies.json"
    scans_file = "compliance_scans.json"
    findings_file = "sensitive_data_findings.json"
    contracts_file = "contract_reviews.json"
    checklists_file = "compliance_checklists.json"
    audit_packages_file = "audit_packages.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, secret_scanner: SecretScanner | None = None):
        self.storage = storage
        self.governance = governance_service
        self.secret_scanner = secret_scanner or SecretScanner()

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _enum(self, value, allowed: list[str], default: str) -> str:
        candidate = str(value or "").strip().lower()
        return candidate if candidate in allowed else default

    def _string_list(self, values, limit: int = 30, item_max: int = 300) -> list[str]:
        cleaned: list[str] = []
        for value in values or []:
            text = str(value).strip()[:item_max]
            if text and text not in cleaned:
                cleaned.append(text)
            if len(cleaned) >= limit:
                break
        return cleaned

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="compliance_intelligence",
                agent_name="Compliance Intelligence",
                action_type=action_type,
                tool_used="ComplianceIntelligenceService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=8,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Policies
    # ------------------------------------------------------------------
    def list_policies(self) -> list[dict]:
        return self.storage.read_list(self.policies_file)

    def create_policy(self, data: dict) -> dict:
        policy = {
            "policy_id": str(uuid4()),
            "name": self._clean(data.get("name"), 160) or "Compliance policy",
            "category": self._clean(data.get("category"), 80) or "general",
            "rules": self._string_list(data.get("rules")),
            "status": self._enum(data.get("status"), POLICY_STATUSES, "draft"),
            "disclaimer": DISCLAIMER,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.policies_file, policy)
        self._log("compliance_policy_created", f"Created policy: {policy['name']}.")
        return policy

    def update_policy(self, policy_id: str, updates: dict) -> dict:
        policies = self.storage.read_list(self.policies_file)
        policy = next((p for p in policies if p.get("policy_id") == policy_id), None)
        if policy is None:
            raise ValueError("Policy not found")
        if updates.get("name") is not None:
            policy["name"] = self._clean(updates["name"], 160) or policy["name"]
        if updates.get("category") is not None:
            policy["category"] = self._clean(updates["category"], 80)
        if updates.get("rules") is not None:
            policy["rules"] = self._string_list(updates["rules"])
        if updates.get("status") is not None:
            policy["status"] = self._enum(updates["status"], POLICY_STATUSES, policy["status"])
        policy["updated_at"] = self._now()
        self.storage.write_list(self.policies_file, policies)
        self._log("compliance_policy_updated", f"Updated policy {policy_id}.")
        return policy

    # ------------------------------------------------------------------
    # Sensitive data classifier
    # ------------------------------------------------------------------
    def scan(self, content: str, label: str = "") -> dict:
        text = content or ""
        lowered = text.lower()
        _, secret_result = self.secret_scanner.redact(text)
        pii_found: dict[str, int] = {}
        for name, pattern in _PII_PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                pii_found[name] = len(matches)
        phi_terms = sorted({kw for kw in _PHI_KEYWORDS if kw in lowered})
        finding = {
            "finding_id": str(uuid4()),
            "scan_id": str(uuid4()),
            "label": self._clean(label, 160),
            "secrets_detected": secret_result.secrets_detected,
            "secret_types": secret_result.detected_types,
            "pii_detected": bool(pii_found),
            "pii_types": list(pii_found.keys()),
            "phi_detected": bool(phi_terms),
            "phi_terms": phi_terms,
            "hipaa_warning": bool(phi_terms),
            "risk_level": "high" if (secret_result.secrets_detected or phi_terms) else "medium" if pii_found else "low",
            "recommendation": (
                "Redact and restrict access; PHI present — handle under HIPAA-aware controls."
                if phi_terms
                else "Redact secrets/PII before storage, sharing, or model use."
                if (secret_result.secrets_detected or pii_found)
                else "No strong sensitive-data signals detected — review manually if needed."
            ),
            "disclaimer": DISCLAIMER,
            "created_at": self._now(),
        }
        self.storage.append(self.scans_file, {"scan_id": finding["scan_id"], "label": finding["label"], "created_at": finding["created_at"]})
        self.storage.append(self.findings_file, finding)
        self._log("compliance_scan_run", f"Scanned content '{label[:60]}' (risk {finding['risk_level']}).")
        return finding

    def list_scans(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.findings_file)[-limit:]))

    # ------------------------------------------------------------------
    # Contract review
    # ------------------------------------------------------------------
    def review_contract(self, data: dict) -> dict:
        text = self._clean(data.get("content"), 20000)
        lowered = text.lower()
        risk_flags = [message for keyword, message in _CONTRACT_RISK_KEYWORDS.items() if keyword in lowered]
        review = {
            "review_id": str(uuid4()),
            "title": self._clean(data.get("title"), 200) or "Contract review",
            "risk_flags": risk_flags,
            "risk_level": "high" if len(risk_flags) >= 3 else "medium" if risk_flags else "low",
            "recommended_checklist": [
                "Confirm parties and effective dates.",
                "Review liability, indemnity, and termination terms.",
                "Confirm governing law and dispute resolution.",
                "Have a qualified human/legal reviewer approve before signing.",
            ],
            "disclaimer": DISCLAIMER,
            "created_at": self._now(),
        }
        self.storage.append(self.contracts_file, review)
        self._log("compliance_contract_reviewed", f"Reviewed contract '{review['title']}' ({len(risk_flags)} flag(s)).")
        return review

    def list_contract_reviews(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.contracts_file)[-limit:]))

    # ------------------------------------------------------------------
    # Checklists
    # ------------------------------------------------------------------
    def create_checklist(self, data: dict) -> dict:
        framework = self._clean(data.get("framework"), 80) or "general"
        presets = {
            "hipaa": [
                "Identify all PHI in scope.",
                "Apply access controls and audit logging.",
                "Confirm BAAs with third parties.",
                "Document breach-response procedure.",
            ],
            "gdpr": [
                "Map personal data and lawful basis.",
                "Provide data-subject access/erasure paths.",
                "Document data-processing agreements.",
            ],
            "soc2": [
                "Document security policies.",
                "Enable monitoring and audit trails.",
                "Review vendor risk.",
            ],
        }
        items = self._string_list(data.get("items")) or presets.get(framework.lower(), [
            "Define the compliance objective.",
            "List required controls.",
            "Assign a human reviewer.",
        ])
        checklist = {
            "checklist_id": str(uuid4()),
            "title": self._clean(data.get("title"), 200) or f"{framework.upper()} checklist",
            "framework": framework,
            "items": [{"item": item, "done": False} for item in items],
            "disclaimer": DISCLAIMER,
            "created_at": self._now(),
        }
        self.storage.append(self.checklists_file, checklist)
        self._log("compliance_checklist_created", f"Created {framework} checklist.")
        return checklist

    def list_checklists(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.checklists_file)[-limit:]))

    # ------------------------------------------------------------------
    # Audit packages
    # ------------------------------------------------------------------
    def create_audit_package(self, data: dict) -> dict:
        governance = self.storage.read_list("governance_log.json")
        findings = self.storage.read_list(self.findings_file)
        policies = self.list_policies()
        checklists = self.storage.read_list(self.checklists_file)
        contracts = self.storage.read_list(self.contracts_file)
        package = {
            "package_id": str(uuid4()),
            "title": self._clean(data.get("title"), 200) or "Audit package",
            "generated_at": self._now(),
            "governance_event_count": len(governance),
            "blocked_action_count": sum(1 for e in governance if e.get("blocked")),
            "sensitive_findings_count": len(findings),
            "high_risk_findings": sum(1 for f in findings if f.get("risk_level") == "high"),
            "policy_count": len(policies),
            "contents": [
                "Governance event summary",
                "Sensitive-data findings summary",
                "Active policies and checklists",
                "Recent contract reviews",
            ],
            "disclaimer": DISCLAIMER,
            # Real, embedded, point-in-time snapshot — not just the counts
            # above. governance_events is capped; every other collection here
            # is already naturally small (policies/checklists/contract
            # reviews a compliance team manages directly).
            "bundle": {
                "governance_events": governance[-_MAX_AUDIT_EVENTS:],
                "sensitive_findings": findings,
                "policies": policies,
                "checklists": checklists,
                "contract_reviews": contracts,
            },
        }
        self.storage.append(self.audit_packages_file, package)
        self._log("compliance_audit_package_created", f"Generated audit package {package['package_id']} ({len(governance)} governance events).")
        return package

    def list_audit_packages(self, limit: int = 25) -> list[dict]:
        """Lightweight — omits each package's embedded bundle so the list view
        stays small; fetch get_audit_package(id) for the full export."""
        rows = list(reversed(self.storage.read_list(self.audit_packages_file)[-limit:]))
        return [{k: v for k, v in row.items() if k != "bundle"} for row in rows]

    def get_audit_package(self, package_id: str) -> dict:
        for row in self.storage.read_list(self.audit_packages_file):
            if row.get("package_id") == package_id:
                return row
        raise ValueError(f"Audit package not found: {package_id}")

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard(self) -> dict:
        findings = self.storage.read_list(self.findings_file)
        return {
            "policy_count": len(self.list_policies()),
            "scan_count": len(findings),
            "high_risk_findings": sum(1 for f in findings if f.get("risk_level") == "high"),
            "phi_findings": sum(1 for f in findings if f.get("phi_detected")),
            "contract_review_count": len(self.storage.read_list(self.contracts_file)),
            "checklist_count": len(self.storage.read_list(self.checklists_file)),
            "audit_package_count": len(self.storage.read_list(self.audit_packages_file)),
            "recent_findings": list(reversed(findings[-5:])),
            "disclaimer": DISCLAIMER,
        }
