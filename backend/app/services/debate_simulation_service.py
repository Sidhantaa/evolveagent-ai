from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.secret_scanner import SecretScanner
from app.services.storage_service import StorageService


class DebateSimulationService:
    debate_file = "debate_sessions.json"
    simulation_file = "simulation_runs.json"

    default_agents = [
        "Strategy Agent",
        "Risk Agent",
        "Implementation Agent",
        "User Advocate Agent",
    ]

    def __init__(
        self,
        storage: StorageService,
        governance_service: GovernanceService,
        secret_scanner: SecretScanner | None = None,
    ):
        self.storage = storage
        self.governance_service = governance_service
        self.secret_scanner = secret_scanner or SecretScanner()

    def create_debate(self, prompt: str, workspace_id: str | None = None, agents: list[str] | None = None) -> dict:
        safe_prompt, secret_scan = self.secret_scanner.redact(prompt)
        selected_agents = agents or self.default_agents
        turns = [self._agent_turn(agent, safe_prompt, index) for index, agent in enumerate(selected_agents[:6])]
        consensus = self._judge_consensus(safe_prompt, turns)
        debate = {
            "debate_id": str(uuid4()),
            "workspace_id": workspace_id,
            "prompt": safe_prompt,
            "agents": selected_agents[:6],
            "turns": turns,
            "consensus": consensus,
            "audit_log": self._audit_log("debate_created", safe_prompt, turns, consensus),
            "secret_scan": secret_scan.model_dump(),
            "status": "completed",
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        self.storage.append(self.debate_file, debate)
        self._log_event("debate_created", debate, risk_score=20)
        return debate

    def list_debates(self, workspace_id: str | None = None) -> list[dict]:
        debates = self.storage.read_list(self.debate_file)
        if workspace_id:
            debates = [item for item in debates if item.get("workspace_id") == workspace_id]
        return list(reversed(debates))

    def get_debate(self, debate_id: str) -> dict | None:
        return next((item for item in self.storage.read_list(self.debate_file) if item.get("debate_id") == debate_id), None)

    def consensus_for(self, debate_id: str) -> dict:
        debate = self.get_debate(debate_id)
        if not debate:
            return {"success": False, "error": "Debate session not found."}
        consensus = self._judge_consensus(debate.get("prompt", ""), debate.get("turns", []))
        debate["consensus"] = consensus
        debate["updated_at"] = datetime.now(UTC).isoformat()
        debate["audit_log"] = [*debate.get("audit_log", []), *self._audit_log("consensus_selected", debate["prompt"], debate["turns"], consensus)]
        self._replace(self.debate_file, "debate_id", debate)
        self._log_event("debate_consensus_selected", debate, risk_score=20)
        return {"success": True, "debate": debate, "consensus": consensus}

    def create_simulation(self, prompt: str, scenario: str | None = None, workspace_id: str | None = None) -> dict:
        safe_prompt, secret_scan = self.secret_scanner.redact(prompt)
        scenario_text = scenario or "Compare optimistic, realistic, and risk-heavy outcomes before taking action."
        outcomes = [
            self._simulation_outcome("optimistic", safe_prompt, scenario_text),
            self._simulation_outcome("realistic", safe_prompt, scenario_text),
            self._simulation_outcome("risk-heavy", safe_prompt, scenario_text),
        ]
        recommendation = self._simulation_recommendation(outcomes)
        simulation = {
            "simulation_id": str(uuid4()),
            "workspace_id": workspace_id,
            "prompt": safe_prompt,
            "scenario": scenario_text,
            "outcomes": outcomes,
            "recommendation": recommendation,
            "side_effects": [],
            "audit_log": [
                {
                    "event": "simulation_created",
                    "summary": "Simulation ran without file edits, commands, API calls, or external side effects.",
                    "created_at": datetime.now(UTC).isoformat(),
                }
            ],
            "secret_scan": secret_scan.model_dump(),
            "status": "completed",
            "created_at": datetime.now(UTC).isoformat(),
        }
        self.storage.append(self.simulation_file, simulation)
        self._log_event("simulation_created", simulation, risk_score=15)
        return simulation

    def list_simulations(self, workspace_id: str | None = None) -> list[dict]:
        runs = self.storage.read_list(self.simulation_file)
        if workspace_id:
            runs = [item for item in runs if item.get("workspace_id") == workspace_id]
        return list(reversed(runs))

    def get_simulation(self, simulation_id: str) -> dict | None:
        return next((item for item in self.storage.read_list(self.simulation_file) if item.get("simulation_id") == simulation_id), None)

    def summary(self, workspace_id: str | None = None) -> dict:
        debates = self.list_debates(workspace_id)
        simulations = self.list_simulations(workspace_id)
        return {
            "total_debates": len(debates),
            "total_simulations": len(simulations),
            "recent_debates": debates[:5],
            "recent_simulations": simulations[:5],
        }

    def _agent_turn(self, agent: str, prompt: str, index: int) -> dict:
        stance = {
            "Strategy Agent": "Prioritize a clear path, milestones, and success criteria.",
            "Risk Agent": "Challenge assumptions, unsafe actions, and missing validation.",
            "Implementation Agent": "Prefer a small reversible implementation with tests.",
            "User Advocate Agent": "Keep the result understandable and useful in Simple Mode.",
        }.get(agent, "Contribute a focused specialist perspective.")
        recommendation = [
            "Start with a scoped plan and validate with a small testable slice.",
            "Add explicit safety gates before any state-changing action.",
            "Record evidence so Developer Mode can explain the decision.",
            "Keep the final answer concise while preserving inspectable detail.",
        ][index % 4]
        return {
            "agent_name": agent,
            "position": stance,
            "argument": f"For: {prompt[:180]}. {stance}",
            "concern": self._concern(agent),
            "recommendation": recommendation,
            "score": max(70, 92 - index * 5),
        }

    def _concern(self, agent: str) -> str:
        if "Risk" in agent:
            return "The plan may skip validation or hide unresolved assumptions."
        if "Implementation" in agent:
            return "The plan should avoid broad rewrites and keep tests fast."
        if "User" in agent:
            return "The interface should not expose internal mechanics by default."
        return "The plan needs a measurable next step."

    def _judge_consensus(self, prompt: str, turns: list[dict]) -> dict:
        strongest = max(turns, key=lambda item: item.get("score", 0), default={})
        risk_notes = [turn.get("concern", "") for turn in turns if turn.get("concern")]
        return {
            "selected_agent": strongest.get("agent_name", "Strategy Agent"),
            "confidence": 84 if turns else 0,
            "final_recommendation": (
                "Use a small, reversible implementation path with explicit validation, governance logging, "
                "and a clean Simple Mode result."
            ),
            "why": f"The selected approach best balances user value, safety, and implementation feasibility for: {prompt[:160]}",
            "risk_notes": risk_notes[:4],
            "next_steps": [
                "Define the smallest useful slice.",
                "Run it in simulation before side effects.",
                "Add tests or build checks.",
                "Expose details only in Developer Mode.",
            ],
        }

    def _simulation_outcome(self, mode: str, prompt: str, scenario: str) -> dict:
        risk = {"optimistic": "low", "realistic": "medium", "risk-heavy": "high"}[mode]
        return {
            "mode": mode,
            "summary": f"{mode.title()} outcome for '{prompt[:120]}' under scenario '{scenario[:120]}'.",
            "expected_result": {
                "optimistic": "Fast completion with minimal blockers.",
                "realistic": "Useful progress with one or two validation passes.",
                "risk-heavy": "Requires tighter scope, extra approvals, or manual review.",
            }[mode],
            "risk_level": risk,
            "mitigation": "Keep changes reversible and require approval before side effects.",
        }

    def _simulation_recommendation(self, outcomes: list[dict]) -> dict:
        return {
            "decision": "proceed_with_controls",
            "summary": "Proceed only through approval-gated, testable steps.",
            "required_controls": [
                "No file edits during simulation.",
                "No shell commands during simulation.",
                "Log all simulated decisions.",
                "Require approval for real execution.",
            ],
        }

    def _audit_log(self, event: str, prompt: str, turns: list[dict], consensus: dict) -> list[dict]:
        return [
            {
                "event": event,
                "prompt_preview": prompt[:160],
                "agents_considered": [turn.get("agent_name") for turn in turns],
                "selected_agent": consensus.get("selected_agent"),
                "created_at": datetime.now(UTC).isoformat(),
            }
        ]

    def _replace(self, filename: str, key: str, item: dict) -> None:
        records = self.storage.read_list(filename)
        self.storage.write_list(filename, [item if record.get(key) == item.get(key) else record for record in records])

    def _log_event(self, action_type: str, item: dict, risk_score: int = 0) -> None:
        self.governance_service.log_event(
            GovernanceEvent(
                workspace_id=item.get("workspace_id"),
                task_type="debate_simulation",
                agent_name="Debate Simulation Service",
                action_type=action_type,
                tool_used="debate_simulation",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=risk_score,
                reason="Debate/simulation ran without side effects.",
            )
        )
