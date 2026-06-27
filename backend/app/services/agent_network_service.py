from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

CONTRACT_STATUSES = ["draft", "sent", "accepted", "completed", "failed", "verified"]
HANDOFF_TYPES = ["local", "external_mock"]
HANDOFF_STATUSES = ["planned", "completed", "failed"]


class AgentNetworkService:
    """v23.0 Agent-to-Agent Network foundation.

    A local protocol for agent task contracts, handoffs, result verification, and
    cross-system audit logs. No real external agent calls are made — handoffs are
    either local or labelled external_mock and produce mock results. Every stateful
    action writes an audit record and a governance event.
    """

    contracts_file = "agent_network_contracts.json"
    handoffs_file = "agent_network_handoffs.json"
    audits_file = "agent_network_audits.json"

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

    def _string_list(self, values, limit: int = 20, item_max: int = 300) -> list[str]:
        cleaned: list[str] = []
        for value in values or []:
            text = str(value).strip()[:item_max]
            if text and text not in cleaned:
                cleaned.append(text)
            if len(cleaned) >= limit:
                break
        return cleaned

    def _audit(self, event_type: str, ref_id: str, detail: str) -> None:
        record = {
            "audit_id": str(uuid4()),
            "event_type": event_type,
            "ref_id": ref_id,
            "detail": detail,
            "created_at": self._now(),
        }
        self.storage.append(self.audits_file, record)

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="agent_network",
                agent_name="Agent Network Service",
                action_type=action_type,
                tool_used="AgentNetworkService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Contracts
    # ------------------------------------------------------------------
    def list_contracts(self) -> list[dict]:
        return self.storage.read_list(self.contracts_file)

    def get_contract(self, contract_id: str) -> dict | None:
        return next((c for c in self.storage.read_list(self.contracts_file) if c.get("contract_id") == contract_id), None)

    def create_contract(self, data: dict) -> dict:
        contract = {
            "contract_id": str(uuid4()),
            "source_agent": self._clean(data.get("source_agent"), 160) or "Master Orchestrator Agent",
            "target_agent": self._clean(data.get("target_agent"), 160) or "Specialist Agent",
            "task": self._clean(data.get("task"), 2000),
            "expected_output": self._clean(data.get("expected_output"), 2000),
            "constraints": self._string_list(data.get("constraints")),
            "status": self._enum(data.get("status"), CONTRACT_STATUSES, "draft"),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.contracts_file, contract)
        self._audit("contract_created", contract["contract_id"], f"Contract from {contract['source_agent']} to {contract['target_agent']}.")
        self._log("agent_network_contract_created", f"Created agent contract {contract['contract_id']}.")
        return contract

    def update_contract(self, contract_id: str, updates: dict) -> dict:
        contracts = self.storage.read_list(self.contracts_file)
        contract = next((c for c in contracts if c.get("contract_id") == contract_id), None)
        if contract is None:
            raise ValueError("Contract not found")
        for field, maxlen in (("source_agent", 160), ("target_agent", 160), ("task", 2000), ("expected_output", 2000)):
            if updates.get(field) is not None:
                contract[field] = self._clean(updates[field], maxlen)
        if updates.get("constraints") is not None:
            contract["constraints"] = self._string_list(updates["constraints"])
        if updates.get("status") is not None:
            contract["status"] = self._enum(updates["status"], CONTRACT_STATUSES, contract["status"])
        contract["updated_at"] = self._now()
        self.storage.write_list(self.contracts_file, contracts)
        self._audit("contract_updated", contract_id, f"Contract status: {contract['status']}.")
        self._log("agent_network_contract_updated", f"Updated agent contract {contract_id}.")
        return contract

    def _set_contract_status(self, contract_id: str, status: str) -> None:
        contracts = self.storage.read_list(self.contracts_file)
        contract = next((c for c in contracts if c.get("contract_id") == contract_id), None)
        if contract is not None:
            contract["status"] = status
            contract["updated_at"] = self._now()
            self.storage.write_list(self.contracts_file, contracts)

    # ------------------------------------------------------------------
    # Handoffs
    # ------------------------------------------------------------------
    def list_handoffs(self) -> list[dict]:
        return self.storage.read_list(self.handoffs_file)

    def get_handoff(self, handoff_id: str) -> dict | None:
        return next((h for h in self.storage.read_list(self.handoffs_file) if h.get("handoff_id") == handoff_id), None)

    def create_handoff(self, contract_id: str, handoff_type: str | None, payload: dict | None) -> dict:
        contract = self.get_contract(contract_id)
        if contract is None:
            raise ValueError("Contract not found")
        resolved_type = self._enum(handoff_type, HANDOFF_TYPES, "local")
        # Mock execution only — never calls a real external agent.
        result = {
            "produced_by": contract.get("target_agent"),
            "output": f"[mock {resolved_type} result] {contract.get('task', '')[:160]}",
            "note": "Mock handoff result — no real external agent was contacted.",
        }
        handoff = {
            "handoff_id": str(uuid4()),
            "contract_id": contract_id,
            "handoff_type": resolved_type,
            "payload": payload if isinstance(payload, dict) else {},
            "result": result,
            "verification": {},
            "status": "completed",
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.handoffs_file, handoff)
        self._set_contract_status(contract_id, "completed")
        self._audit("handoff_created", handoff["handoff_id"], f"{resolved_type} handoff for contract {contract_id}.")
        self._log("agent_network_handoff_created", f"Created {resolved_type} handoff {handoff['handoff_id']}.")
        return handoff

    def verify_handoff(self, handoff_id: str) -> dict:
        handoffs = self.storage.read_list(self.handoffs_file)
        handoff = next((h for h in handoffs if h.get("handoff_id") == handoff_id), None)
        if handoff is None:
            raise ValueError("Handoff not found")
        contract = self.get_contract(handoff.get("contract_id"))
        output = (handoff.get("result") or {}).get("output", "")
        expected = (contract or {}).get("expected_output", "")
        constraints = (contract or {}).get("constraints", [])
        checks = []
        passed = True
        # Output presence check.
        has_output = bool(output)
        checks.append({"check": "output_present", "passed": has_output})
        passed = passed and has_output
        # Expected-output keyword overlap (lightweight, local).
        if expected:
            overlap = any(word.lower() in output.lower() for word in expected.split()[:8] if len(word) > 3)
            checks.append({"check": "matches_expected", "passed": overlap})
            passed = passed and overlap
        # Constraint mention check (advisory).
        for constraint in constraints[:5]:
            checks.append({"check": f"constraint_considered:{constraint[:40]}", "passed": True})
        verification = {
            "verified": passed,
            "checks": checks,
            "verified_at": self._now(),
            "note": "Local mock verification — heuristic only.",
        }
        handoff["verification"] = verification
        handoff["status"] = "completed" if passed else "failed"
        handoff["updated_at"] = self._now()
        self.storage.write_list(self.handoffs_file, handoffs)
        self._set_contract_status(handoff.get("contract_id"), "verified" if passed else "failed")
        self._audit("handoff_verified", handoff_id, f"Verification {'passed' if passed else 'failed'}.")
        self._log("agent_network_handoff_verified", f"Verified handoff {handoff_id}: {'passed' if passed else 'failed'}.")
        return handoff

    # ------------------------------------------------------------------
    # Audit + dashboard
    # ------------------------------------------------------------------
    def audit_log(self, limit: int = 50) -> list[dict]:
        return list(reversed(self.storage.read_list(self.audits_file)[-limit:]))

    def dashboard(self) -> dict:
        contracts = self.storage.read_list(self.contracts_file)
        handoffs = self.storage.read_list(self.handoffs_file)
        status_counts: dict[str, int] = {}
        for contract in contracts:
            key = contract.get("status", "draft")
            status_counts[key] = status_counts.get(key, 0) + 1
        verified = sum(1 for h in handoffs if (h.get("verification") or {}).get("verified") is True)
        return {
            "total_contracts": len(contracts),
            "contract_status_counts": status_counts,
            "total_handoffs": len(handoffs),
            "verified_handoffs": verified,
            "audit_event_count": len(self.storage.read_list(self.audits_file)),
            "recent_audit": self.audit_log(limit=5),
            "recommended_next_action": (
                "Create an agent task contract to begin a handoff."
                if not contracts
                else "Run a handoff and verify the result."
            ),
        }
