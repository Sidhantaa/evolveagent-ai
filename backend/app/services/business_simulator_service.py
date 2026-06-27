from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

SCENARIO_TYPES = ["decision", "cost", "time", "risk", "launch", "workflow", "custom"]

# Keywords that raise the simulated risk score (with the factor they imply).
_RISK_KEYWORDS = {
    "urgent": "Urgency increases execution risk.",
    "deadline": "Hard deadline increases schedule risk.",
    "launch": "Launch activity carries go-to-market risk.",
    "payment": "Payment handling carries financial/compliance risk.",
    "legal": "Legal exposure detected.",
    "compliance": "Compliance requirements detected.",
    "health": "Health-related impact raises stakes.",
    "customer": "Direct customer impact raises stakes.",
    "production": "Production impact carries reliability risk.",
    "security": "Security implications detected.",
    "migration": "Migration carries data/regression risk.",
}

# Rough cost anchors (USD) per scenario type — illustrative estimates only.
_COST_ANCHORS = {
    "decision": (200, 800, 2000),
    "cost": (500, 2000, 6000),
    "time": (300, 1200, 4000),
    "risk": (200, 1000, 3500),
    "launch": (1000, 4000, 12000),
    "workflow": (300, 1500, 5000),
    "custom": (250, 1200, 4000),
}

# Rough time anchors (days) per scenario type — illustrative estimates only.
_TIME_ANCHORS = {
    "decision": (1, 3, 7),
    "cost": (2, 5, 12),
    "time": (3, 7, 18),
    "risk": (1, 4, 10),
    "launch": (5, 14, 35),
    "workflow": (2, 6, 15),
    "custom": (2, 5, 14),
}


class BusinessSimulatorService:
    """v20.0 Autonomous Business Simulator.

    Runs rule-based, local-only "what-if" simulations over scenarios the user
    describes: decision scoring, rough cost/time estimates, risk estimates, and
    option comparison. It never makes real financial claims, never executes
    actions, and labels every result as simulation/estimate only. Stateful
    actions are logged through governance.
    """

    scenarios_file = "business_simulation_scenarios.json"
    results_file = "business_simulation_results.json"
    sim_file = "business_simulations.json"

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

    def _filter_workspace(self, items: list[dict], workspace_id: str | None) -> list[dict]:
        if not workspace_id:
            return items
        return [item for item in items if item.get("workspace_id") == workspace_id]

    def _log(self, action_type: str, workspace_id: str | None, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                workspace_id=workspace_id,
                task_type="business_simulator",
                agent_name="Business Simulator",
                action_type=action_type,
                tool_used="BusinessSimulatorService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Scenarios
    # ------------------------------------------------------------------
    def list_scenarios(self, workspace_id: str | None = None) -> list[dict]:
        return self._filter_workspace(self.storage.read_list(self.scenarios_file), workspace_id)

    def get_scenario(self, scenario_id: str) -> dict | None:
        return next(
            (item for item in self.storage.read_list(self.scenarios_file) if item.get("scenario_id") == scenario_id),
            None,
        )

    def create_scenario(self, data: dict) -> dict:
        scenario = {
            "scenario_id": str(uuid4()),
            "workspace_id": data.get("workspace_id"),
            "title": self._clean(data.get("title"), 200),
            "description": self._clean(data.get("description"), 4000),
            "scenario_type": self._enum(data.get("scenario_type"), SCENARIO_TYPES, "decision"),
            "assumptions": self._string_list(data.get("assumptions")),
            "options": self._string_list(data.get("options")),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.scenarios_file, scenario)
        self._log("business_simulation_scenario_created", scenario["workspace_id"], f"Created simulation scenario: {scenario['title'] or scenario['scenario_id']}.")
        return scenario

    def update_scenario(self, scenario_id: str, updates: dict) -> dict:
        scenarios = self.storage.read_list(self.scenarios_file)
        scenario = next((item for item in scenarios if item.get("scenario_id") == scenario_id), None)
        if scenario is None:
            raise ValueError("Scenario not found")
        if updates.get("title") is not None:
            scenario["title"] = self._clean(updates["title"], 200)
        if updates.get("description") is not None:
            scenario["description"] = self._clean(updates["description"], 4000)
        if updates.get("scenario_type") is not None:
            scenario["scenario_type"] = self._enum(updates["scenario_type"], SCENARIO_TYPES, "decision")
        if updates.get("assumptions") is not None:
            scenario["assumptions"] = self._string_list(updates["assumptions"])
        if updates.get("options") is not None:
            scenario["options"] = self._string_list(updates["options"])
        scenario["updated_at"] = self._now()
        self.storage.write_list(self.scenarios_file, scenarios)
        self._log("business_simulation_scenario_updated", scenario.get("workspace_id"), f"Updated simulation scenario {scenario_id}.")
        return scenario

    # ------------------------------------------------------------------
    # Simulation engine (rule-based, local only)
    # ------------------------------------------------------------------
    def _risk_estimate(self, scenario: dict) -> dict:
        text = f"{scenario.get('title', '')} {scenario.get('description', '')} {' '.join(scenario.get('assumptions', []))}".lower()
        factors: list[str] = []
        score = 20  # baseline uncertainty
        for keyword, message in _RISK_KEYWORDS.items():
            if keyword in text and message not in factors:
                factors.append(message)
                score += 12
        # Missing assumptions raise uncertainty/risk.
        if len(scenario.get("assumptions", [])) < 2:
            score += 10
            factors.append("Few stated assumptions — higher uncertainty.")
        score = max(0, min(100, score))
        level = "high" if score >= 60 else "medium" if score >= 35 else "low"
        mitigations = [
            "Validate the riskiest assumption with a small test before committing.",
            "Add human approval checkpoints for irreversible steps.",
        ]
        if level == "high":
            mitigations.append("Consider a phased rollout to contain downside.")
        return {"risk_score": score, "risk_level": level, "risk_factors": factors, "mitigations": mitigations}

    def _cost_estimate(self, scenario: dict) -> dict:
        low, expected, high = _COST_ANCHORS.get(scenario.get("scenario_type", "custom"), _COST_ANCHORS["custom"])
        option_count = len(scenario.get("options", []))
        # More options modestly widen the range.
        multiplier = 1 + 0.1 * max(0, option_count - 1)
        return {
            "low": round(low * 1.0),
            "expected": round(expected * multiplier),
            "high": round(high * multiplier),
            "notes": [
                "Rough order-of-magnitude estimate only — not financial advice.",
                "Anchored to scenario type and number of options; adjust with real quotes.",
            ],
        }

    def _time_estimate(self, scenario: dict) -> dict:
        best, expected, worst = _TIME_ANCHORS.get(scenario.get("scenario_type", "custom"), _TIME_ANCHORS["custom"])
        option_count = len(scenario.get("options", []))
        multiplier = 1 + 0.08 * max(0, option_count - 1)
        return {
            "best_case_days": best,
            "expected_days": round(expected * multiplier),
            "worst_case_days": round(worst * multiplier),
            "notes": [
                "Estimated effort window only — actual time depends on scope and capacity.",
                "Worst case assumes blockers or rework.",
            ],
        }

    def _decision_score(self, scenario: dict, risk: dict) -> int:
        # Higher when more options to compare and lower risk; bounded 0-100.
        score = 50
        score += min(20, len(scenario.get("options", [])) * 8)
        score += min(15, len(scenario.get("assumptions", [])) * 3)
        score -= round(risk["risk_score"] * 0.3)
        return max(0, min(100, score))

    def _confidence(self, scenario: dict) -> int:
        # More assumptions + options => more grounded => higher confidence.
        assumptions = len(scenario.get("assumptions", []))
        options = len(scenario.get("options", []))
        confidence = 30 + assumptions * 10 + options * 6
        return max(10, min(90, confidence))

    def _option_comparison(self, scenario: dict, cost: dict, time: dict, risk: dict) -> list[dict]:
        options = scenario.get("options", [])
        comparison = []
        for index, option in enumerate(options):
            # Spread estimates across options deterministically for a comparable view.
            factor = 1 + (index - (len(options) - 1) / 2) * 0.12 if len(options) > 1 else 1
            comparison.append(
                {
                    "option": option,
                    "estimated_cost": round(cost["expected"] * factor),
                    "estimated_days": max(1, round(time["expected_days"] * factor)),
                    "risk_level": risk["risk_level"],
                    "note": "Relative estimate vs. other options — simulation only.",
                }
            )
        return comparison

    def run_simulation(self, scenario_id: str) -> dict:
        scenario = self.get_scenario(scenario_id)
        if scenario is None:
            raise ValueError("Scenario not found")
        risk = self._risk_estimate(scenario)
        cost = self._cost_estimate(scenario)
        time = self._time_estimate(scenario)
        decision_score = self._decision_score(scenario, risk)
        confidence = self._confidence(scenario)
        comparison = self._option_comparison(scenario, cost, time, risk)

        if risk["risk_level"] == "high":
            recommendation = "High simulated risk — test the riskiest assumption first and keep the change reversible."
        elif decision_score >= 65:
            recommendation = "Simulation looks favorable — proceed in a small, governed step and re-simulate as you learn."
        else:
            recommendation = "Mixed outlook — gather one or two more assumptions, then re-run the simulation."

        result = {
            "result_id": str(uuid4()),
            "scenario_id": scenario_id,
            "workspace_id": scenario.get("workspace_id"),
            "summary": (
                f"Decision score {decision_score}/100, {risk['risk_level']} risk, "
                f"~{time['expected_days']} day(s), ~${cost['expected']} expected cost (estimate)."
            ),
            "decision_score": decision_score,
            "cost_estimate": cost,
            "time_estimate": time,
            "risk_estimate": risk,
            "option_comparison": comparison,
            "recommendation": recommendation,
            "confidence": confidence,
            "simulation_only": True,
            "created_at": self._now(),
        }
        self.storage.append(self.results_file, result)
        self._log("business_simulation_run", scenario.get("workspace_id"), f"Ran simulation for scenario {scenario_id}.")
        return result

    def list_results(self, workspace_id: str | None = None, limit: int = 25) -> list[dict]:
        results = self._filter_workspace(self.storage.read_list(self.results_file), workspace_id)
        return list(reversed(results[-limit:]))

    def get_result(self, result_id: str) -> dict | None:
        return next(
            (item for item in self.storage.read_list(self.results_file) if item.get("result_id") == result_id),
            None,
        )

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard(self, workspace_id: str | None = None) -> dict:
        scenarios = self.list_scenarios(workspace_id)
        results = self._filter_workspace(self.storage.read_list(self.results_file), workspace_id)
        risk_scores = [r.get("risk_estimate", {}).get("risk_score", 0) for r in results]
        average_risk = round(sum(risk_scores) / len(risk_scores), 2) if risk_scores else 0
        high_risk = [
            {"result_id": r.get("result_id"), "scenario_id": r.get("scenario_id"), "summary": r.get("summary")}
            for r in results
            if r.get("risk_estimate", {}).get("risk_level") == "high"
        ]
        recommended = (
            "Create a scenario describing a decision you're weighing, then run a simulation."
            if not scenarios
            else "Run or re-run a simulation on your most uncertain scenario."
        )
        self._log("business_simulation_dashboard_viewed", workspace_id, "Viewed business simulator dashboard.")
        return {
            "total_scenarios": len(scenarios),
            "total_results": len(results),
            "average_risk_score": average_risk,
            "high_risk_scenarios": high_risk,
            "recent_results": list(reversed(results[-5:])),
            "recommended_next_simulation": recommended,
            "simulation_only": True,
        }
