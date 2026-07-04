from __future__ import annotations

import fnmatch
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

SCOPE_TYPES = ["global", "workspace", "agent", "tool"]
EFFECTS = ["deny", "require_approval", "allow"]
RISK_LEVELS = ["low", "medium", "high"]
# Lower = more restrictive; the most restrictive matching profile wins.
_EFFECT_RANK = {"deny": 0, "require_approval": 1, "allow": 2}

# Approval chains by risk (advisory): how many approvers a risk level should require.
APPROVAL_CHAINS = {"low": 0, "medium": 1, "high": 2}


class PermissionProfilesService:
    """v81.0 Permission System 3.0 — stronger, previewable control over actions.

    Declarative **permission profiles** scoped to global / workspace / agent / tool,
    matching an action pattern + risk level, with an effect of **deny /
    require_approval / allow**. Evaluation returns the **most restrictive** matching
    decision plus a **blocked-action explanation** and the **approval chain** for the
    risk. Includes a **policy preview** (evaluate a hypothetical action). Consistent
    with the platform's planning-first posture and additive to the core
    ``PermissionService`` (this is a separate profile/policy layer): an ``allow``
    profile never grants new execution power — risky actions still default to approval
    when unprofiled, and profiles can only tighten. Governance-logged.
    """

    profiles_file = "permission_profiles.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str, blocked: bool = False) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="permission_system",
                agent_name="Permission System",
                action_type=action_type,
                tool_used="PermissionProfilesService",
                permission_level="read_only",
                approved=not blocked,
                blocked=blocked,
                risk_score=2,
                reason=reason,
            )
        )

    def create_profile(self, data: dict) -> dict:
        scope_type = data.get("scope_type") if data.get("scope_type") in SCOPE_TYPES else "global"
        effect = data.get("effect") if data.get("effect") in EFFECTS else "require_approval"
        risk = data.get("risk_level") if data.get("risk_level") in RISK_LEVELS else "high"
        profile = {
            "profile_id": str(uuid4()),
            "name": str(data.get("name") or "Unnamed profile")[:120],
            "scope_type": scope_type,
            "scope_value": str(data.get("scope_value") or "*")[:120],
            "action_pattern": str(data.get("action_pattern") or "*")[:120],
            "effect": effect,
            "risk_level": risk,
            "created_at": self._now(),
        }
        self.storage.append(self.profiles_file, profile)
        self._log("permission_profile_created", f"Created permission profile '{profile['name']}' ({effect}).")
        return profile

    def list_profiles(self) -> list[dict]:
        return self.storage.read_list(self.profiles_file)

    def delete_profile(self, profile_id: str) -> dict:
        profiles = self.list_profiles()
        remaining = [p for p in profiles if p.get("profile_id") != profile_id]
        if len(remaining) == len(profiles):
            raise ValueError("Permission profile not found")
        self.storage.write_list(self.profiles_file, remaining)
        self._log("permission_profile_deleted", "Deleted a permission profile.")
        return {"deleted": profile_id}

    def _matches(self, profile: dict, scope_type: str, scope_value: str, action: str, risk: str) -> bool:
        if profile["scope_type"] != "global" and profile["scope_type"] != scope_type:
            return False
        if profile["scope_type"] != "global" and profile["scope_value"] not in ("*", scope_value):
            return False
        if not fnmatch.fnmatch(action.lower(), profile["action_pattern"].lower()):
            return False
        # A profile applies at its risk level and above.
        return RISK_LEVELS.index(risk) >= RISK_LEVELS.index(profile["risk_level"])

    def evaluate(self, scope_type: str, scope_value: str, action: str, risk: str = "medium", log: bool = True) -> dict:
        scope_type = scope_type if scope_type in SCOPE_TYPES else "global"
        risk = risk if risk in RISK_LEVELS else "medium"
        matched = [p for p in self.list_profiles() if self._matches(p, scope_type, scope_value, action, risk)]

        if matched:
            winner = min(matched, key=lambda p: _EFFECT_RANK[p["effect"]])
            decision = winner["effect"]
            matched_profile = {"profile_id": winner["profile_id"], "name": winner["name"], "effect": winner["effect"]}
        else:
            # Default (planning-first): risky actions require approval; low-risk allowed.
            decision = "allow" if risk == "low" else "require_approval"
            matched_profile = None

        explanation = {
            "deny": f"Blocked by permission policy — a profile denies '{action}' at {risk} risk for this scope.",
            "require_approval": f"Held for approval — {action} at {risk} risk requires {APPROVAL_CHAINS[risk]} approver(s).",
            "allow": f"Allowed — {action} at {risk} risk is permitted (planning-first; no new execution power granted).",
        }[decision]

        if log:
            self._log("permission_evaluated", f"Evaluated {scope_type}:{scope_value} '{action}' ({risk}) -> {decision}.",
                      blocked=(decision == "deny"))
        return {
            "decision": decision,
            "scope_type": scope_type,
            "scope_value": scope_value,
            "action": action,
            "risk_level": risk,
            "matched_profile": matched_profile,
            "approval_chain": APPROVAL_CHAINS[risk],
            "explanation": explanation,
            "note": "An 'allow' never grants new execution power; risky actions still route to approval by default.",
        }

    def preview(self, scope_type: str, scope_value: str, action: str, risk: str) -> dict:
        return self.evaluate(scope_type, scope_value, action, risk, log=False)

    def analytics_summary(self) -> dict:
        return {"permission_profiles": len(self.list_profiles())}

    def summary(self) -> dict:
        profiles = self.list_profiles()
        by_effect = {e: sum(1 for p in profiles if p.get("effect") == e) for e in EFFECTS}
        return {
            "total_profiles": len(profiles),
            "by_effect": by_effect,
            "scope_types": SCOPE_TYPES,
            "approval_chains": APPROVAL_CHAINS,
            "note": "Permission profiles can only tighten (deny/require_approval); allow grants no new power.",
        }
