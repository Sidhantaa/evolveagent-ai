from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Callable
from uuid import uuid4

from app.models.request_models import RunRequest
from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.mcp_suggestion_service import MCPSuggestionService
from app.services.storage_service import StorageService

DISCLAIMER = (
    "The Master Agent is a governed orchestration layer, not AGI and not a self-trained model. "
    "It routes your request across the existing EvolveAgent systems (v1–v60) and never runs "
    "destructive, sending, or paid actions without explicit human approval."
)

# The Master Agent's knowledge of every capability it fronts (its "tuning" across v1–v60).
# domain, human label, API route, keyword triggers, and whether the action class is risky
# (risky => planning-first: it plans/asks for approval, it does not auto-execute).
CAPABILITY_ROUTES = [
    {"domain": "Coding & Review", "route": "/api/run", "risky": False,
     "keywords": ["code", "function", "bug", "refactor", "review", "pull request", "debug", "implement", "unit test", "python", "javascript"]},
    {"domain": "Research & Retrieval", "route": "/api/retrieval", "risky": False,
     "keywords": ["research", "find", "look up", "summarize", "explain", "what is", "how does", "compare", "documentation", "sources"]},
    {"domain": "Project & Portfolio", "route": "/api/project-manager", "risky": False,
     "keywords": ["project", "milestone", "roadmap", "portfolio", "status report", "risk", "deadline", "plan the project"]},
    {"domain": "Business Operations", "route": "/api/business-operator", "risky": True,
     "keywords": ["lead", "proposal", "invoice", "marketing", "campaign", "customer", "sales", "kpi", "business workflow"]},
    {"domain": "Compliance & Legal", "route": "/api/compliance", "risky": False,
     "keywords": ["compliance", "policy", "contract", "gdpr", "hipaa", "audit", "sensitive data", "pii", "legal"]},
    {"domain": "Personal / Life OS", "route": "/api/life-os", "risky": False,
     "keywords": ["remind", "schedule", "my day", "todo", "task list", "deadline", "personal", "plan my week"]},
    {"domain": "Innovation & Simulation", "route": "/api/innovation-lab", "risky": False,
     "keywords": ["idea", "brainstorm", "innovate", "prototype", "simulate", "scenario", "experiment", "trend"]},
    {"domain": "MCP Tools & Integrations", "route": "/api/mcp", "risky": True,
     "keywords": ["mcp", "connect", "integration", "github", "linear", "slack", "notion", "browser", "connector", "tool"]},
    {"domain": "Approvals & Governance", "route": "/api/approvals-center", "risky": False,
     "keywords": ["approve", "approval", "pending", "governance", "audit log", "who approved"]},
    {"domain": "Health & Ops", "route": "/api/health-monitor", "risky": False,
     "keywords": ["health", "status", "readiness", "usage", "cost", "ledger", "budget", "notifications"]},
    {"domain": "Playbooks & Automation", "route": "/api/playbooks", "risky": False,
     "keywords": ["playbook", "automate", "workflow", "scheduled", "recurring", "template"]},
]

# Verbs that imply a real-world side effect → require explicit approval before any execution.
_RISKY_VERBS = ["send", "email", "pay", "purchase", "delete", "remove", "deploy", "post to", "message the", "transfer", "charge", "publish"]


class MasterAgentService:
    """The Master Agent — a single top-level AI surface over all of v1–v60.

    You speak or type one request; the Master Agent classifies intent, decides which
    subsystems (capabilities) are relevant, suggests any MCP connectors + reports key
    readiness (boolean only, never secret values), and produces an answer by
    orchestrating the existing run pipeline. It is planning-first: risky action classes
    (send / pay / delete / deploy / external post) are flagged and require human approval
    rather than being auto-executed. Every route is governance-logged.

    It is *not* a newly trained model — its "tuning" is the CAPABILITY_ROUTES registry,
    i.e. explicit configured knowledge of every subsystem it fronts.
    """

    runs_file = "master_agent_runs.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, mcp_suggestion: MCPSuggestionService, run_fn: Callable[[RunRequest], object]):
        self.storage = storage
        self.governance = governance_service
        self.mcp_suggestion = mcp_suggestion
        self._run_fn = run_fn

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    # ------------------------------------------------------------------
    # Intent routing
    # ------------------------------------------------------------------
    def _classify(self, text: str) -> list[dict]:
        haystack = f" {re.sub(r'[^a-z0-9]+', ' ', (text or '').lower())} "
        scored = []
        for cap in CAPABILITY_ROUTES:
            hits = sum(1 for kw in cap["keywords"] if kw in haystack)
            if hits:
                scored.append({"domain": cap["domain"], "route": cap["route"], "risky": cap["risky"], "match_score": hits})
        scored.sort(key=lambda c: c["match_score"], reverse=True)
        # Always give the model a default so it never returns "no capability".
        if not scored:
            scored.append({"domain": "Research & Retrieval", "route": "/api/retrieval", "risky": False, "match_score": 0})
        return scored

    def _detect_risky_intent(self, text: str, engaged: list[dict]) -> tuple[bool, list[str]]:
        haystack = f" {(text or '').lower()} "
        verbs = [v for v in _RISKY_VERBS if v in haystack]
        risky_domains = [c["domain"] for c in engaged if c["risky"]]
        requires_approval = bool(verbs) or bool(risky_domains)
        reasons = []
        if verbs:
            reasons.append(f"Request implies a real-world action ({', '.join(sorted(set(verbs)))}).")
        if risky_domains:
            reasons.append(f"Touches a sensitive domain ({', '.join(sorted(set(risky_domains)))}).")
        return requires_approval, reasons

    def capabilities(self) -> dict:
        return {
            "capabilities": [
                {"domain": c["domain"], "route": c["route"], "risky": c["risky"], "trigger_examples": c["keywords"][:4]}
                for c in CAPABILITY_ROUTES
            ],
            "capability_count": len(CAPABILITY_ROUTES),
            "disclaimer": DISCLAIMER,
        }

    # ------------------------------------------------------------------
    # Main entry: route a request across the whole platform
    # ------------------------------------------------------------------
    def route(self, text: str, workspace_id: str | None = None, voice_used: bool = False, execute: bool = False) -> dict:
        text = (text or "").strip()
        engaged = self._classify(text)
        top = engaged[:3]
        mcp = self.mcp_suggestion.suggest(text)
        requires_approval, approval_reasons = self._detect_risky_intent(text, engaged)

        # Produce the actual answer via the existing orchestration pipeline. A risky
        # action class is ALWAYS held for human approval — the client-supplied `execute`
        # flag can never authorize send/pay/delete/deploy; it only permits auto-execution
        # of non-risky intents.
        answer = ""
        agents_used: list[str] = []
        answered = False
        blocked_execution = requires_approval
        try:
            run_request = RunRequest(user_input=text or "Summarize what you can help with.", workspace_id=workspace_id, voice_used=voice_used)
            response = self._run_fn(run_request)
            answer = getattr(response, "final_output", "") or ""
            agents_used = list(getattr(response, "agents_used", []) or [])
            answered = True
        except Exception as error:  # orchestration failure must not crash the Master Agent
            answer = f"(Routing succeeded, but the answer pipeline could not complete: {error})"

        sources = [
            {"label": c["domain"], "route": c["route"], "why": f"matched {c['match_score']} intent signal(s)"}
            for c in top
        ]
        for suggestion in mcp.get("suggestions", [])[:3]:
            sources.append({
                "label": f"MCP: {suggestion.get('name')}",
                "route": "/api/mcp",
                "why": "keys ready" if suggestion.get("keys_ready") else f"needs {', '.join(suggestion.get('missing_keys', []))}",
            })

        followups = self._build_followups(top, mcp, requires_approval)

        record = {
            "run_id": str(uuid4()),
            "request": text[:1000],
            "primary_domain": top[0]["domain"] if top else None,
            "engaged_domains": [c["domain"] for c in top],
            "requires_approval": requires_approval,
            "executed": answered and not blocked_execution,
            "keys_ready": all(s.get("keys_ready") for s in mcp.get("suggestions", [])) if mcp.get("suggestions") else True,
            "voice_used": voice_used,
            "created_at": self._now(),
        }
        self.storage.append(self.runs_file, record)
        self.governance.log_event(
            GovernanceEvent(
                task_type="master_agent",
                agent_name="Master Agent",
                action_type="master_route_approval_required" if requires_approval else "master_route",
                tool_used="MasterAgentService",
                permission_level="action" if (execute and not requires_approval) else "read_only",
                approved=not blocked_execution,
                blocked=blocked_execution,
                risk_score=6 if requires_approval else 3,
                reason=f"Master Agent routed to {record['primary_domain']}." + (" Approval required." if requires_approval else ""),
            )
        )

        return {
            "run_id": record["run_id"],
            "request": text,
            "intent": {
                "primary_domain": top[0]["domain"] if top else None,
                "engaged": top,
            },
            "answer": answer,
            "answered": answered,
            "agents_used": agents_used,
            "sources": sources,
            "followups": followups,
            "mcp_suggestions": mcp.get("suggestions", []),
            "keys_ready": record["keys_ready"],
            "requires_approval": requires_approval,
            "approval_reasons": approval_reasons,
            "blocked_execution": blocked_execution,
            "note": (
                "This is a planning-first orchestration. A real-world action was detected and is held for approval."
                if blocked_execution else
                "Routed and answered across the EvolveAgent platform."
            ),
            "disclaimer": DISCLAIMER,
        }

    def _build_followups(self, engaged: list[dict], mcp: dict, requires_approval: bool) -> list[str]:
        followups: list[str] = []
        if requires_approval:
            followups.append("Approve this action in the Approvals Center")
        for suggestion in mcp.get("suggestions", []):
            if not suggestion.get("keys_ready"):
                followups.append(f"Set keys for {suggestion.get('name')}: {', '.join(suggestion.get('missing_keys', []))}")
            elif not suggestion.get("already_enabled"):
                followups.append(f"Enable the {suggestion.get('name')} connector")
        for cap in engaged[:2]:
            followups.append(f"Open {cap['domain']} ({cap['route']})")
        # De-dup while preserving order, cap at 5.
        seen = set()
        unique = []
        for item in followups:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        return unique[:5]

    def analytics_summary(self) -> dict:
        runs = self.storage.read_list(self.runs_file)
        return {
            "master_agent_runs": len(runs),
            "master_agent_approvals_required": sum(1 for r in runs if r.get("requires_approval")),
        }

    def summary(self) -> dict:
        runs = self.storage.read_list(self.runs_file)
        by_domain: dict[str, int] = {}
        for run in runs:
            key = run.get("primary_domain") or "unknown"
            by_domain[key] = by_domain.get(key, 0) + 1
        return {
            "total_routes": len(runs),
            "approvals_required": sum(1 for r in runs if r.get("requires_approval")),
            "by_domain": by_domain,
            "capability_count": len(CAPABILITY_ROUTES),
            "recent": list(reversed(runs[-10:])),
            "disclaimer": DISCLAIMER,
        }
