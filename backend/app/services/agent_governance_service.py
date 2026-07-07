"""Agent Governance (v100 stretch) — risk scoring + a tighten-only policy engine
for the Agent Registry.

Two real capabilities, both additive to the existing governance layer:

1. **Risk scoring** — computes a deterministic 0-100 risk score for any agent in
   the unified Agent Registry (task 9), from real signals already on each entry
   (approval_gated, status, declared tool count, quality_score). Reuses
   ``GovernanceService._risk_bucket`` for the low/medium/high bucketing so the
   scale matches every other risk score in the app.

2. **Agent policies** — a **tighten-only, deny-only** policy engine, matching the
   exact contract and safety posture of the existing ``MCPPolicyService`` (which
   gates MCP connector actions): a policy can only ADD a block, never grant new
   access. Policies match on registry ``source``, computed ``risk_level``, and an
   optional case-insensitive name substring.

Per the master plan's rule ("agents with approval_gated=true from the registry
auto-inherit stricter policy"): ``requires_approval`` is *always* true when the
registry entry itself declares ``approval_gated`` or when the computed risk is
"high" — no policy can loosen that; policies can only add further blocks.

Read-only with respect to the registry itself — no agent data is modified here.
Governance-logged.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.agent_registry_service import AgentRegistryService
from app.services.agent_registry_service import SOURCES as AGENT_SOURCES
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

RISK_LEVELS = ["low", "medium", "high"]


class AgentGovernanceService:
    policies_file = "agent_governance_policies.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, registry: AgentRegistryService):
        self.storage = storage
        self.governance = governance_service
        self.registry = registry

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _matcher(self, value, allowed: list[str]) -> str:
        candidate = str(value or "*").strip().lower()
        return candidate if candidate == "*" or candidate in allowed else "*"

    def _log(self, action_type: str, reason: str, risk_score: int = 5, blocked: bool = False) -> None:
        self.governance.log_event(GovernanceEvent(
            task_type="agent_governance", agent_name="Agent Governance", action_type=action_type,
            tool_used="AgentGovernanceService", permission_level="read_only", approved=not blocked,
            blocked=blocked, risk_score=risk_score, reason=reason,
        ))

    # -- risk scoring ----------------------------------------------------------
    def score_agent(self, entry: dict) -> dict:
        score = 10
        factors: list[str] = []

        if entry.get("approval_gated"):
            score += 30
            factors.append("declares an action that requires approval")

        status = str(entry.get("status", "")).lower()
        if status in ("draft", "disabled", "inactive"):
            score += 15
            factors.append(f"status is '{status}' (not published/active)")

        tools = entry.get("tools") or []
        if tools:
            bump = min(len(tools) * 3, 15)
            score += bump
            factors.append(f"{len(tools)} tool(s) declared")

        quality = entry.get("quality_score")
        if isinstance(quality, (int, float)):
            if quality < 50:
                score += 15
                factors.append(f"low quality/evaluation score ({quality})")
            elif quality >= 85:
                score -= 10
                factors.append(f"high quality/evaluation score ({quality})")

        score = max(0, min(100, score))
        return {"score": score, "level": GovernanceService._risk_bucket(score), "factors": factors}

    def _decorate(self, entry: dict) -> dict:
        risk = self.score_agent(entry)
        decision = self.evaluate(entry, risk["level"])
        requires_approval = bool(entry.get("approval_gated")) or risk["level"] == "high"
        return {
            **entry,
            "risk_score": risk["score"],
            "risk_level": risk["level"],
            "risk_factors": risk["factors"],
            "requires_approval": requires_approval,
            "policy_allowed": decision["allowed"],
            "policy_reason": decision["reason"],
            "policy_id": decision["policy_id"],
        }

    def list_agent_risk(self, source: str | None = None, min_level: str | None = None, limit: int = 200) -> dict:
        registry = self.registry.list_agents(source=source, limit=limit)
        decorated = [self._decorate(e) for e in registry["agents"]]
        if min_level in RISK_LEVELS:
            rank = {"low": 0, "medium": 1, "high": 2}
            decorated = [d for d in decorated if rank[d["risk_level"]] >= rank[min_level]]
        decorated.sort(key=lambda d: d["risk_score"], reverse=True)
        self._log("agent_risk_listed", f"Scored {len(decorated)} agents (source={source or 'all'})")
        return {"agents": decorated, "count": len(decorated),
                "by_level": {lvl: sum(1 for d in decorated if d["risk_level"] == lvl) for lvl in RISK_LEVELS}}

    def get_agent_risk(self, registry_id: str) -> dict:
        entry = self.registry.get(registry_id)  # raises ValueError if not found
        decorated = self._decorate(entry)
        self._log("agent_risk_scored", f"Scored agent {registry_id}: {decorated['risk_level']} ({decorated['risk_score']})")
        return decorated

    # -- policies (tighten-only deny) ------------------------------------------
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
            "effect": "deny",  # tighten-only: deny is the only effect, ever
            "source": self._matcher(data.get("source", "*"), list(AGENT_SOURCES)),
            "risk_level": self._matcher(data.get("risk_level", "*"), RISK_LEVELS),
            "name_contains": self._clean(data.get("name_contains", "*"), 80).lower() or "*",
            "enabled": bool(data.get("enabled", True)),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.policies_file, policy)
        self._log("agent_policy_created", f"Created deny policy '{policy['name']}' ({policy['source']}/{policy['risk_level']}).")
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
        if data.get("source") is not None:
            policy["source"] = self._matcher(data["source"], list(AGENT_SOURCES))
        if data.get("risk_level") is not None:
            policy["risk_level"] = self._matcher(data["risk_level"], RISK_LEVELS)
        if data.get("name_contains") is not None:
            policy["name_contains"] = self._clean(data["name_contains"], 80).lower() or "*"
        if data.get("enabled") is not None:
            policy["enabled"] = bool(data["enabled"])
        policy["effect"] = "deny"  # never editable to widen access
        policy["updated_at"] = self._now()
        self.storage.write_list(self.policies_file, policies)
        self._log("agent_policy_updated", f"Updated policy {policy_id} (enabled={policy['enabled']}).")
        return policy

    def evaluate(self, entry: dict, risk_level: str) -> dict:
        """Return {allowed, reason, policy_id}. Default allow; deny only on match."""
        source = str(entry.get("source", "")).lower()
        name = str(entry.get("name", "")).lower()
        for policy in self.list_policies():
            if not policy.get("enabled", True) or policy.get("effect") != "deny":
                continue
            if policy.get("source", "*") not in ("*", source):
                continue
            if policy.get("risk_level", "*") not in ("*", risk_level):
                continue
            needle = policy.get("name_contains", "*")
            if needle != "*" and needle not in name:
                continue
            return {"allowed": False, "reason": f"Blocked by policy '{policy.get('name')}' ({policy.get('policy_id')}).",
                    "policy_id": policy.get("policy_id")}
        return {"allowed": True, "reason": None, "policy_id": None}

    def summarize_policies(self) -> dict:
        policies = self.list_policies()
        return {
            "total_policies": len(policies),
            "active_policies": sum(1 for p in policies if p.get("enabled", True)),
            "effect": "deny_only",
            "note": "Agent policies are tighten-only deny rules. They can only add blocks, never grant access. "
                    "approval_gated agents and high-risk agents always require approval regardless of policy.",
            "policies": policies,
        }

    # -- analytics ---------------------------------------------------------------
    def analytics_summary(self) -> dict:
        policies = self.list_policies()
        risk = self.list_agent_risk()
        return {
            "agent_governance_policies": len(policies),
            "agent_governance_policies_active": sum(1 for p in policies if p.get("enabled", True)),
            "agent_governance_high_risk": risk["by_level"].get("high", 0),
        }

    def summary(self) -> dict:
        return {**self.analytics_summary(), **self.summarize_policies()}
