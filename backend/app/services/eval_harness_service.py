from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


class EvalHarnessService:
    """v52.0 Evaluation Harness 2.0.

    Turns ad-hoc evaluation into repeatable **suites** and **scorecards** with
    regression tracking. A suite holds cases (prompt, a reference answer, and
    expected keywords). Running a suite is **deterministic and mock-safe** — it
    scores each case by how many expected keywords appear in its reference
    answer, with no real LLM call — so scores are stable and regressions are
    detectable across runs. Suite creation and runs are governance-logged.
    """

    suites_file = "eval_suites.json"
    runs_file = "eval_runs.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _string_list(self, values, limit: int = 40, item_max: int = 120) -> list[str]:
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
                task_type="eval_harness",
                agent_name="Evaluation Harness",
                action_type=action_type,
                tool_used="EvalHarnessService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=3,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Suites
    # ------------------------------------------------------------------
    def create_suite(self, data: dict) -> dict:
        data = data or {}
        cases = []
        for case in data.get("cases", [])[:100]:
            cases.append({
                "case_id": str(uuid4()),
                "prompt": self._clean(case.get("prompt"), 2000),
                "reference_answer": self._clean(case.get("reference_answer"), 4000),
                "expected_keywords": self._string_list(case.get("expected_keywords")),
            })
        suite = {
            "suite_id": str(uuid4()),
            "name": self._clean(data.get("name"), 160) or "Evaluation suite",
            "cases": cases,
            "case_count": len(cases),
            "created_at": self._now(),
        }
        self.storage.append(self.suites_file, suite)
        self._log("eval_suite_created", f"Created eval suite '{suite['name']}' ({len(cases)} case(s)).")
        return suite

    def list_suites(self) -> list[dict]:
        return [
            {"suite_id": s["suite_id"], "name": s.get("name"), "case_count": s.get("case_count"), "created_at": s.get("created_at")}
            for s in self.storage.read_list(self.suites_file)
        ]

    def get_suite(self, suite_id: str) -> dict | None:
        return next((s for s in self.storage.read_list(self.suites_file) if s.get("suite_id") == suite_id), None)

    # ------------------------------------------------------------------
    # Runs (deterministic scoring)
    # ------------------------------------------------------------------
    def _score_case(self, case: dict) -> dict:
        keywords = case.get("expected_keywords", [])
        reference = (case.get("reference_answer") or "").lower()
        if not keywords:
            matched = []
            score = 1.0 if reference else 0.0
        else:
            matched = [k for k in keywords if k.lower() in reference]
            score = round(len(matched) / len(keywords), 4)
        return {
            "case_id": case.get("case_id"),
            "prompt": case.get("prompt"),
            "score": score,
            "matched_keywords": matched,
            "expected_keywords": keywords,
            "passed": score >= 0.5,
        }

    def run_suite(self, suite_id: str) -> dict:
        suite = self.get_suite(suite_id)
        if suite is None:
            raise ValueError("Suite not found")
        case_results = [self._score_case(c) for c in suite.get("cases", [])]
        overall = round(sum(c["score"] for c in case_results) / len(case_results), 4) if case_results else 0.0
        pass_count = sum(1 for c in case_results if c["passed"])
        # Regression vs the previous run of this suite.
        prev = [r for r in self.storage.read_list(self.runs_file) if r.get("suite_id") == suite_id]
        prev_score = prev[-1]["score"] if prev else None
        run = {
            "run_id": str(uuid4()),
            "suite_id": suite_id,
            "suite_name": suite.get("name"),
            "score": overall,
            "pass_count": pass_count,
            "case_count": len(case_results),
            "previous_score": prev_score,
            "delta": round(overall - prev_score, 4) if prev_score is not None else None,
            "regressed": (prev_score is not None and overall < prev_score),
            "cases": case_results,
            "created_at": self._now(),
        }
        self.storage.append(self.runs_file, run)
        self._log("eval_suite_run", f"Ran eval suite {suite_id} (score {overall}, {pass_count}/{len(case_results)} passed).")
        return run

    def list_runs(self, suite_id: str | None = None, limit: int = 50) -> list[dict]:
        runs = self.storage.read_list(self.runs_file)
        if suite_id:
            runs = [r for r in runs if r.get("suite_id") == suite_id]
        return list(reversed(runs[-limit:]))

    def regression(self, suite_id: str) -> dict:
        runs = [r for r in self.storage.read_list(self.runs_file) if r.get("suite_id") == suite_id]
        if len(runs) < 2:
            return {"suite_id": suite_id, "runs": len(runs), "regressed": False, "detail": "Need at least two runs to compare."}
        latest, previous = runs[-1], runs[-2]
        return {
            "suite_id": suite_id,
            "runs": len(runs),
            "latest_score": latest["score"],
            "previous_score": previous["score"],
            "delta": round(latest["score"] - previous["score"], 4),
            "regressed": latest["score"] < previous["score"],
        }

    # ------------------------------------------------------------------
    # Summary + analytics
    # ------------------------------------------------------------------
    def summary(self) -> dict:
        runs = self.storage.read_list(self.runs_file)
        return {
            "suite_count": len(self.storage.read_list(self.suites_file)),
            "run_count": len(runs),
            "latest_score": runs[-1]["score"] if runs else None,
            "regressed_runs": sum(1 for r in runs if r.get("regressed")),
            "note": "Deterministic, mock-safe scoring — no real LLM call; scores are stable and regressions detectable.",
        }

    def analytics_summary(self) -> dict:
        runs = self.storage.read_list(self.runs_file)
        return {
            "eval_suites": len(self.storage.read_list(self.suites_file)),
            "eval_runs": len(runs),
            "eval_regressed_runs": sum(1 for r in runs if r.get("regressed")),
        }
