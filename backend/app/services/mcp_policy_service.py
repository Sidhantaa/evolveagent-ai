from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

RISK_LEVELS = ["low", "medium", "high"]


class MCPPolicyService:
    """v45.0 MCP Policy Engine (tighten-only, deny rules).

    Declarative **deny** policies evaluated *before* v41 connector planning. A
    policy can only ADD a block — it never grants new power (there is no "allow"
    effect that could widen access). Each policy matches on optional filters
    (connector slug, action, risk level) with an optional ``except_actions``
    carve-out, so you can express rules like "deny all Filesystem actions except
    ``fs_list_directory``". With no policies defined, evaluation returns *allow*
    and connector behaviour is unchanged. Stateful actions are governance-logged.
    """

    policies_file = "mcp_policies.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _string_list(self, values, limit: int = 40, item_max: int = 80) -> list[str]:
        cleaned: list[str] = []
        for value in values or []:
            text = str(value).strip()[:item_max]
            if text and text not in cleaned:
                cleaned.append(text)
            if len(cleaned) >= limit:
                break
        return cleaned

    def _matcher(self, value, allowed: list[str]) -> str:
        candidate = str(value or "*").strip().lower()
        if candidate == "*" or candidate in allowed:
            return candidate
        return "*"

    def _log(self, action_type: str, reason: str, blocked: bool = False) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="mcp_policy",
                agent_name="MCP Policy Engine",
                action_type=action_type,
                tool_used="MCPPolicyService",
                permission_level="read_only",
                approved=not blocked,
                blocked=blocked,
                risk_score=6,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def list_policies(self) -> list[dict]:
        return self.storage.read_list(self.policies_file)

    def get_policy(self, policy_id: str) -> dict | None:
        return next((p for p in self.list_policies() if p.get("policy_id") == policy_id), None)

    def create_policy(self, data: dict) -> dict:
        data = data or {}
        policy = {
            "policy_id": str(uuid4()),
            "name": self._clean(data.get("name"), 120) or "Deny policy",
            "description": self._clean(data.get("description"), 400),
            "effect": "deny",  # tighten-only: deny is the only effect
            "connector_slug": self._clean(data.get("connector_slug", "*"), 60).lower() or "*",
            "action": self._clean(data.get("action", "*"), 80) or "*",
            "risk_level": self._matcher(data.get("risk_level", "*"), RISK_LEVELS),
            "except_actions": self._string_list(data.get("except_actions")),
            "enabled": bool(data.get("enabled", True)),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.policies_file, policy)
        self._log("mcp_policy_created", f"Created deny policy '{policy['name']}' ({policy['connector_slug']}/{policy['action']}/{policy['risk_level']}).")
        return policy

    def update_policy(self, policy_id: str, data: dict) -> dict:
        policies = self.list_policies()
        policy = next((p for p in policies if p.get("policy_id") == policy_id), None)
        if policy is None:
            raise ValueError("Policy not found")
        data = data or {}
        if data.get("name") is not None:
            policy["name"] = self._clean(data["name"], 120) or policy["name"]
        if data.get("description") is not None:
            policy["description"] = self._clean(data["description"], 400)
        if data.get("connector_slug") is not None:
            policy["connector_slug"] = self._clean(data["connector_slug"], 60).lower() or "*"
        if data.get("action") is not None:
            policy["action"] = self._clean(data["action"], 80) or "*"
        if data.get("risk_level") is not None:
            policy["risk_level"] = self._matcher(data["risk_level"], RISK_LEVELS)
        if data.get("except_actions") is not None:
            policy["except_actions"] = self._string_list(data["except_actions"])
        if data.get("enabled") is not None:
            policy["enabled"] = bool(data["enabled"])
        # effect stays "deny" — tighten-only, never editable to widen access.
        policy["effect"] = "deny"
        policy["updated_at"] = self._now()
        self.storage.write_list(self.policies_file, policies)
        self._log("mcp_policy_updated", f"Updated policy {policy_id} (enabled={policy['enabled']}).")
        return policy

    # ------------------------------------------------------------------
    # Evaluation (tighten-only)
    # ------------------------------------------------------------------
    def evaluate(self, connector: dict, action_name: str) -> dict:
        """Return {allowed, reason, policy_id}. Default allow; deny only on match."""
        slug = str(connector.get("slug", "")).lower()
        risk = str(connector.get("risk_level", "")).lower()
        action = str(action_name or "")
        for policy in self.list_policies():
            if not policy.get("enabled", True) or policy.get("effect") != "deny":
                continue
            if policy.get("connector_slug", "*") not in ("*", slug):
                continue
            if policy.get("risk_level", "*") not in ("*", risk):
                continue
            if policy.get("action", "*") not in ("*", action):
                continue
            if action in (policy.get("except_actions") or []):
                continue  # carve-out — this action is explicitly exempted
            return {
                "allowed": False,
                "reason": f"Blocked by policy '{policy.get('name')}' ({policy.get('policy_id')}).",
                "policy_id": policy.get("policy_id"),
            }
        return {"allowed": True, "reason": None, "policy_id": None}

    def evaluate_and_log(self, connector: dict, action_name: str) -> dict:
        decision = self.evaluate(connector, action_name)
        if not decision["allowed"]:
            self._log("mcp_policy_denied", f"Policy denied action '{action_name}' on {connector.get('slug')}: {decision['reason']}", blocked=True)
        return decision

    # ------------------------------------------------------------------
    # Summary + analytics
    # ------------------------------------------------------------------
    def summarize(self) -> dict:
        policies = self.list_policies()
        return {
            "total_policies": len(policies),
            "active_policies": sum(1 for p in policies if p.get("enabled", True)),
            "effect": "deny_only",
            "note": "Policies are tighten-only deny rules evaluated before connector planning. They can only add blocks, never grant access.",
            "policies": policies,
        }

    def analytics_summary(self) -> dict:
        policies = self.list_policies()
        return {
            "mcp_policies_total": len(policies),
            "mcp_policies_active": sum(1 for p in policies if p.get("enabled", True)),
        }
