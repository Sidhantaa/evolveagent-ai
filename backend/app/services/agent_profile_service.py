from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

TONES = ["professional", "friendly", "direct", "creative"]
VERBOSITY = ["low", "medium", "high"]
# Risky action classes an agent may declare — always start in requires_approval, never auto-run.
RISKY_ACTIONS = ["send", "email", "pay", "purchase", "delete", "deploy", "post", "publish", "transfer"]

STARTER_TEMPLATES = [
    {"key": "chief_of_staff", "name": "Chief of Staff", "role": "Run my day: plan, prioritize, and keep me on track.",
     "personality": {"tone": "professional", "verbosity": "medium"}, "tools": ["goals", "scheduled_tasks", "productivity"]},
    {"key": "research_assistant", "name": "Research Assistant", "role": "Dig up sources, compare claims, and brief me.",
     "personality": {"tone": "direct", "verbosity": "high"}, "tools": ["retrieval", "research_agent", "search"]},
    {"key": "inbox_manager", "name": "Inbox & Ops Manager", "role": "Keep me on top of approvals, notifications, and follow-ups.",
     "personality": {"tone": "friendly", "verbosity": "low"}, "tools": ["approvals", "notifications", "activity"]},
    {"key": "code_buddy", "name": "Code Buddy", "role": "Review code, flag risks, and suggest refactors (no unsafe edits).",
     "personality": {"tone": "direct", "verbosity": "medium"}, "tools": ["code_intel", "git_intel"]},
]


class AgentProfileService:
    """Phase 2 Agent Studio — build your own agent via SAFE personalization.

    Create, configure, test, evaluate, version, and locally publish custom agent
    **profiles**: role, personality, tools, permissions, memory scope, few-shot
    examples, and guardrails. This is **not base-model training** — personalization is
    configuration + retrieval + few-shot examples + preference/evaluation feedback. The
    **test** and **evaluate** paths are deterministic and mock-safe (no real LLM call,
    nothing executed): test simulates what the agent *would* do from its config, and
    evaluate scores its declared test cases by keyword coverage. Risky declared actions
    always start as ``requires_approval`` and can never auto-run. Governance-logged.
    """

    profiles_file = "agent_profiles.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="agent_studio",
                agent_name="Agent Studio",
                action_type=action_type,
                tool_used="AgentProfileService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=2,
                reason=reason,
            )
        )

    def templates(self) -> dict:
        return {"templates": STARTER_TEMPLATES, "count": len(STARTER_TEMPLATES)}

    @staticmethod
    def _clean_guardrails(g: dict) -> dict:
        g = g or {}
        allowed = [str(a)[:60] for a in (g.get("allowed_actions") or [])][:30]
        blocked = [str(a)[:60] for a in (g.get("blocked_actions") or [])][:30]
        # Any risky-looking allowed action is forced into requires_approval (safety).
        requires = list({str(a)[:60] for a in (g.get("requires_approval") or [])})
        for a in allowed:
            if any(v in a.lower() for v in RISKY_ACTIONS) and a not in requires:
                requires.append(a)
        return {"allowed_actions": allowed, "blocked_actions": blocked, "requires_approval": requires[:30]}

    def _build(self, data: dict, existing: dict | None = None) -> dict:
        personality = data.get("personality") or {}
        profile = {
            "agent_id": (existing or {}).get("agent_id") or str(uuid4()),
            "name": str(data.get("name") or "Untitled Agent")[:120],
            "role": str(data.get("role") or "")[:1000],
            "description": str(data.get("description") or "")[:1000],
            "personality": {
                "tone": personality.get("tone") if personality.get("tone") in TONES else "professional",
                "verbosity": personality.get("verbosity") if personality.get("verbosity") in VERBOSITY else "medium",
            },
            "tools": [str(t)[:60] for t in (data.get("tools") or [])][:30],
            "permissions": data.get("permissions") or {},
            "memory_scope": {
                "workspace": bool((data.get("memory_scope") or {}).get("workspace", True)),
                "personal": bool((data.get("memory_scope") or {}).get("personal", False)),
                "documents": [str(d)[:120] for d in ((data.get("memory_scope") or {}).get("documents") or [])][:20],
            },
            "examples": [{"input": str(e.get("input", ""))[:1000], "output": str(e.get("output", ""))[:2000]}
                         for e in (data.get("examples") or []) if isinstance(e, dict)][:20],
            "guardrails": self._clean_guardrails(data.get("guardrails")),
            "evaluation": (existing or {}).get("evaluation") or {"score": None, "test_cases": data.get("test_cases") or []},
            "published_local": (existing or {}).get("published_local", False),
            "version": ((existing or {}).get("version") or 0) + 1,
            "versions": (existing or {}).get("versions") or [],
            "created_at": (existing or {}).get("created_at") or self._now(),
            "updated_at": self._now(),
        }
        return profile

    def create(self, data: dict) -> dict:
        profile = self._build(data)
        self.storage.append(self.profiles_file, profile)
        self._log("agent_created", f"Created custom agent '{profile['name']}' (config-only, not trained).")
        return profile

    def list_agents(self) -> dict:
        agents = self.storage.read_list(self.profiles_file)
        return {"agents": agents, "count": len(agents)}

    def get(self, agent_id: str) -> dict:
        agent = next((a for a in self.storage.read_list(self.profiles_file) if a.get("agent_id") == agent_id), None)
        if agent is None:
            raise ValueError("Agent not found")
        return agent

    _SNAP_FIELDS = ("version", "name", "role", "description", "personality", "tools", "guardrails", "examples")

    def _snapshot(self, agent: dict) -> dict:
        snap = {k: agent.get(k) for k in self._SNAP_FIELDS}
        snap["snapshot_at"] = self._now()
        return snap

    def update(self, agent_id: str, data: dict) -> dict:
        agents = self.storage.read_list(self.profiles_file)
        idx = next((i for i, a in enumerate(agents) if a.get("agent_id") == agent_id), None)
        if idx is None:
            raise ValueError("Agent not found")
        existing = agents[idx]
        merged = {**existing, **data}
        rebuilt = self._build(merged, existing=existing)
        # Keep a rolling history of prior versions so changes can be rolled back.
        rebuilt["versions"] = ([*(existing.get("versions") or []), self._snapshot(existing)])[-10:]
        agents[idx] = rebuilt
        self.storage.write_list(self.profiles_file, agents)
        self._log("agent_updated", f"Updated agent '{rebuilt['name']}' → v{rebuilt['version']}.")
        return rebuilt

    def duplicate(self, agent_id: str) -> dict:
        src = self.get(agent_id)
        data = {k: src.get(k) for k in ("name", "role", "description", "personality", "tools", "memory_scope", "examples", "guardrails")}
        data["name"] = f"{src.get('name', 'Agent')} (copy)"[:120]
        profile = self._build(data)
        self.storage.append(self.profiles_file, profile)
        self._log("agent_duplicated", f"Forked agent '{src.get('name')}' → '{profile['name']}'.")
        return profile

    def versions(self, agent_id: str) -> dict:
        agent = self.get(agent_id)
        return {"agent_id": agent_id, "current_version": agent.get("version"),
                "versions": agent.get("versions") or [], "count": len(agent.get("versions") or [])}

    def rollback(self, agent_id: str, version: int) -> dict:
        agent = self.get(agent_id)
        snap = next((v for v in (agent.get("versions") or []) if v.get("version") == version), None)
        if snap is None:
            raise ValueError(f"No prior version {version} to roll back to")
        data = {k: snap.get(k) for k in ("name", "role", "description", "personality", "tools", "guardrails", "examples")}
        result = self.update(agent_id, data)  # snapshots current, applies old config as a new version
        self._log("agent_rolledback", f"Rolled agent '{agent.get('name')}' back to v{version} (now v{result['version']}).")
        return result

    def preview(self, agent_id: str) -> dict:
        """Assemble a read-only preview of the agent's context — what it would 'see'."""
        a = self.get(agent_id)
        lines = [
            f"# {a['name']}",
            f"Role: {a['role'] or '(none)'}",
            f"Style: {a['personality']['tone']}, {a['personality']['verbosity']} verbosity",
            f"Tools: {', '.join(a['tools']) or 'general reasoning'}",
        ]
        req = a["guardrails"].get("requires_approval") or []
        if req:
            lines.append(f"Held for approval: {', '.join(req)}")
        if a["examples"]:
            lines.append("\nFew-shot examples:")
            for i, e in enumerate(a["examples"][:5], 1):
                lines.append(f"  {i}. IN: {str(e.get('input',''))[:120]}\n     OUT: {str(e.get('output',''))[:160]}")
        return {"agent_id": agent_id, "preview": "\n".join(lines), "example_count": len(a["examples"])}

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {t for t in re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).split() if len(t) > 2}

    def test(self, agent_id: str, prompt: str) -> dict:
        agent = self.get(agent_id)
        # Deterministic, mock-safe simulation — describes what the agent WOULD do from its config.
        # A risky prompt (send/pay/delete/deploy/...) is always held for approval, as is any agent
        # that declares requires_approval actions.
        prompt_risky = any(v in prompt.lower() for v in RISKY_ACTIONS)
        requires_approval = prompt_risky or bool(agent["guardrails"]["requires_approval"])
        self._log("agent_tested", f"Ran a mock test of agent '{agent['name']}'.")
        return {
            "agent_id": agent_id,
            "prompt": prompt,
            "simulated_response": (
                f"[{agent['name']} · {agent['personality']['tone']}] I would approach this using "
                f"{', '.join(agent['tools']) or 'general reasoning'} within my role: {agent['role'][:160]}."
            ),
            "would_use_tools": agent["tools"],
            "requires_approval": requires_approval,
            "note": "Mock simulation — no real LLM call, nothing executed; risky actions are held for approval.",
        }

    def evaluate(self, agent_id: str) -> dict:
        agent = self.get(agent_id)
        cases = agent["evaluation"].get("test_cases") or []
        corpus = " ".join([agent["role"], agent["description"]] + [e.get("output", "") for e in agent["examples"]])
        got = self._tokens(corpus)
        scored = []
        for case in cases:
            expected = self._tokens(str(case.get("expected", "")))
            hit = expected & got
            scored.append({
                "case": str(case.get("input", ""))[:120],
                "score": round((len(hit) / len(expected)) * 100) if expected else 0,
                "missing_keywords": sorted(expected - got)[:10],
            })
        avg = round(sum(s["score"] for s in scored) / len(scored)) if scored else None
        grade = self._grade(avg)
        agents = self.storage.read_list(self.profiles_file)
        for a in agents:
            if a.get("agent_id") == agent_id:
                a["evaluation"]["score"] = avg
                a["evaluation"]["grade"] = grade
        self.storage.write_list(self.profiles_file, agents)
        self._log("agent_evaluated", f"Evaluated agent '{agent['name']}' → score {avg} ({grade}).")
        return {"agent_id": agent_id, "score": avg, "grade": grade, "case_scores": scored,
                "note": "Deterministic mock evaluation over declared examples/test cases — no real LLM."}

    @staticmethod
    def _grade(score: int | None) -> str:
        if score is None:
            return "n/a"
        return "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "F"

    def publish_local(self, agent_id: str) -> dict:
        agents = self.storage.read_list(self.profiles_file)
        target = next((a for a in agents if a.get("agent_id") == agent_id), None)
        if target is None:
            raise ValueError("Agent not found")
        target["published_local"] = True
        target["updated_at"] = self._now()
        self.storage.write_list(self.profiles_file, agents)
        self._log("agent_published_local", f"Published agent '{target['name']}' to the local marketplace.")
        return {"agent_id": agent_id, "published_local": True}

    def import_profile(self, doc: dict) -> dict:
        if not isinstance(doc, dict) or not (doc.get("name") or doc.get("role")):
            raise ValueError("Invalid agent profile")
        # Re-build (sanitizes + assigns a fresh id + resets version) — never trust imported ids/permissions blindly.
        clean = {k: doc.get(k) for k in ("name", "role", "description", "personality", "tools", "memory_scope", "examples", "guardrails")}
        profile = self._build(clean)
        self.storage.append(self.profiles_file, profile)
        self._log("agent_imported", f"Imported agent '{profile['name']}' (sanitized).")
        return profile

    def analytics_summary(self) -> dict:
        agents = self.storage.read_list(self.profiles_file)
        return {"agent_studio_agents": len(agents), "agent_studio_published": sum(1 for a in agents if a.get("published_local"))}

    def summary(self) -> dict:
        agents = self.storage.read_list(self.profiles_file)
        return {
            "total_agents": len(agents),
            "published_local": sum(1 for a in agents if a.get("published_local")),
            "templates": [t["key"] for t in STARTER_TEMPLATES],
            "note": "Custom agents are configuration + examples + evaluation — not base-model training.",
        }
