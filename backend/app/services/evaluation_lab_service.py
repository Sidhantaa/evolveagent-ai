from __future__ import annotations

import csv
import io
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


class EvaluationLabService:
    benchmarks_file = "evaluation_benchmarks.json"
    runs_file = "evaluation_runs.json"
    ab_tests_file = "evaluation_ab_tests.json"
    regressions_file = "evaluation_regressions.json"

    default_cases = [
        ("general", "Explain EvolveAgent AI in simple terms.", "Clear product summary with no raw internals."),
        ("coding", "Review a FastAPI endpoint design.", "Identifies risks, tests, and implementation guidance."),
        ("resume_review", "Improve an uploaded software engineering resume.", "Actionable ATS-friendly resume feedback."),
        ("file_summary", "Summarize an uploaded document.", "Concise summary with key points."),
        ("recording_summary", "Summarize a meeting recording.", "Summary, action items, and decisions."),
        ("image_generation", "Generate an image prompt for a futuristic AI assistant.", "Safe prompt and image metadata."),
        ("app_automation", "Add a settings panel to this app.", "Plan-first automation with approval requirements."),
    ]

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance_service = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _workspace_filter(self, items: list[dict], workspace_id: str | None) -> list[dict]:
        if not workspace_id:
            return items
        return [item for item in items if item.get("workspace_id") == workspace_id]

    def ensure_default_benchmarks(self) -> list[dict]:
        existing = self.storage.read_list(self.benchmarks_file)
        if existing:
            return existing
        now = self._now()
        benchmarks = []
        for task_type, prompt, expected in self.default_cases:
            benchmarks.append(
                {
                    "benchmark_id": f"default-{task_type}",
                    "name": f"{task_type.replace('_', ' ').title()} benchmark",
                    "task_type": task_type,
                    "description": f"Standard evaluation case for {task_type.replace('_', ' ')} workflows.",
                    "cases": [
                        {
                            "case_id": f"{task_type}-001",
                            "prompt": prompt,
                            "expected_behavior": expected,
                        }
                    ],
                    "created_at": now,
                    "updated_at": now,
                    "source": "default",
                }
            )
        self.storage.write_list(self.benchmarks_file, benchmarks)
        return benchmarks

    def list_benchmarks(self, task_type: str | None = None) -> list[dict]:
        benchmarks = self.ensure_default_benchmarks()
        if task_type:
            return [item for item in benchmarks if item.get("task_type") == task_type]
        return benchmarks

    def create_run(
        self,
        benchmark_id: str | None = None,
        task_type: str | None = None,
        workspace_id: str | None = None,
        notes: str | None = None,
    ) -> dict:
        benchmarks = self.list_benchmarks()
        selected = [item for item in benchmarks if (not benchmark_id or item.get("benchmark_id") == benchmark_id)]
        if task_type:
            selected = [item for item in selected if item.get("task_type") == task_type]
        if benchmark_id and not selected:
            raise ValueError("Benchmark not found")
        if not selected:
            selected = benchmarks

        analytics = self._workspace_filter(self.storage.read_list("agent_analytics.json"), workspace_id)
        history_by_task: dict[str, list[dict]] = defaultdict(list)
        for item in analytics:
            history_by_task[item.get("task_type", "unknown")].append(item)

        case_results = []
        for benchmark in selected:
            task_history = history_by_task.get(benchmark.get("task_type"), [])
            scores = [
                item.get("overall_judge_score")
                for item in task_history
                if isinstance(item.get("overall_judge_score"), (int, float))
            ]
            avg_score = round(sum(scores) / len(scores), 2) if scores else 0
            coverage_score = 100 if task_history else 35
            fallback_rate = round(
                (sum(1 for item in task_history if item.get("fallback_used")) / len(task_history)) * 100,
                2,
            ) if task_history else 0
            latency_values = [
                item.get("latency_ms")
                for item in task_history
                if isinstance(item.get("latency_ms"), (int, float))
            ]
            avg_latency = round(sum(latency_values) / len(latency_values), 2) if latency_values else 0
            score = round((avg_score * 0.7) + (coverage_score * 0.3), 2) if avg_score else coverage_score
            status = "passed" if score >= 75 else "warning" if score >= 55 else "needs_data"
            case_results.append(
                {
                    "benchmark_id": benchmark.get("benchmark_id"),
                    "task_type": benchmark.get("task_type"),
                    "case_count": len(benchmark.get("cases", [])),
                    "history_count": len(task_history),
                    "average_judge_score": avg_score,
                    "coverage_score": coverage_score,
                    "fallback_rate": fallback_rate,
                    "average_latency_ms": avg_latency,
                    "score": score,
                    "status": status,
                }
            )

        total_score = round(sum(item["score"] for item in case_results) / len(case_results), 2) if case_results else 0
        run = {
            "evaluation_run_id": str(uuid4()),
            "workspace_id": workspace_id,
            "benchmark_id": benchmark_id,
            "task_type": task_type,
            "score": total_score,
            "status": "passed" if total_score >= 75 else "warning" if total_score >= 55 else "needs_data",
            "case_results": case_results,
            "notes": notes,
            "created_at": self._now(),
        }
        self.storage.append(self.runs_file, run)
        self._record_regression_if_needed(run, workspace_id)
        self.governance_service.log_event(
            GovernanceEvent(
                workspace_id=workspace_id,
                task_type="evaluation_lab",
                agent_name="Evaluation Lab Service",
                action_type="evaluation_run_created",
                tool_used="evaluation_lab",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=f"Evaluation run scored {total_score}.",
            )
        )
        return run

    def list_runs(self, workspace_id: str | None = None, limit: int = 25) -> list[dict]:
        runs = self._workspace_filter(self.storage.read_list(self.runs_file), workspace_id)
        return list(reversed(runs[-limit:]))

    def _record_regression_if_needed(self, run: dict, workspace_id: str | None = None) -> None:
        prior = list(reversed(self._workspace_filter(self.storage.read_list(self.runs_file), workspace_id)[-6:]))
        prior_scores = [
            item.get("score")
            for item in prior
            if item.get("evaluation_run_id") != run.get("evaluation_run_id") and isinstance(item.get("score"), (int, float))
        ][:5]
        if len(prior_scores) < 2:
            return
        baseline = round(sum(prior_scores) / len(prior_scores), 2)
        drop = round(baseline - run.get("score", 0), 2)
        if drop < 10:
            return
        regression = {
            "regression_id": str(uuid4()),
            "evaluation_run_id": run.get("evaluation_run_id"),
            "workspace_id": workspace_id,
            "baseline_score": baseline,
            "current_score": run.get("score", 0),
            "drop": drop,
            "severity": "high" if drop >= 20 else "medium",
            "recommendation": "Review recent prompt, workflow, or provider changes before merging further work.",
            "created_at": self._now(),
        }
        self.storage.append(self.regressions_file, regression)

    def dashboard(self, workspace_id: str | None = None) -> dict:
        self.ensure_default_benchmarks()
        runs = self._workspace_filter(self.storage.read_list(self.runs_file), workspace_id)
        benchmarks = self.storage.read_list(self.benchmarks_file)
        regressions = self._workspace_filter(self.storage.read_list(self.regressions_file), workspace_id)
        latest = runs[-1] if runs else None
        scores = [item.get("score", 0) for item in runs if isinstance(item.get("score"), (int, float))]
        by_task: dict[str, list[float]] = defaultdict(list)
        for run in runs:
            for result in run.get("case_results", []):
                if isinstance(result.get("score"), (int, float)):
                    by_task[result.get("task_type", "unknown")].append(result["score"])
        task_scores = [
            {
                "task_type": task_type,
                "average_score": round(sum(values) / len(values), 2),
                "runs": len(values),
            }
            for task_type, values in sorted(by_task.items())
        ]
        trend = [{"created_at": item.get("created_at"), "score": item.get("score"), "status": item.get("status")} for item in runs[-12:]]
        return {
            "workspace_id": workspace_id,
            "benchmark_count": len(benchmarks),
            "evaluation_run_count": len(runs),
            "latest_run": latest,
            "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "task_scores": task_scores,
            "score_trend": trend,
            "regressions": list(reversed(regressions[-10:])),
            "regression_count": len(regressions),
            "recent_runs": list(reversed(runs[-8:])),
        }

    def create_ab_test(
        self,
        name: str,
        variant_a: str,
        variant_b: str,
        metric: str = "overall_judge_score",
        workspace_id: str | None = None,
    ) -> dict:
        analytics = self._workspace_filter(self.storage.read_list("agent_analytics.json"), workspace_id)
        scores_a = self._variant_scores(analytics, variant_a, metric)
        scores_b = self._variant_scores(analytics, variant_b, metric)
        avg_a = round(sum(scores_a) / len(scores_a), 2) if scores_a else 0
        avg_b = round(sum(scores_b) / len(scores_b), 2) if scores_b else 0
        winner = "tie"
        if avg_a > avg_b:
            winner = variant_a
        elif avg_b > avg_a:
            winner = variant_b
        record = {
            "ab_test_id": str(uuid4()),
            "workspace_id": workspace_id,
            "name": name,
            "variant_a": variant_a,
            "variant_b": variant_b,
            "metric": metric,
            "variant_a_count": len(scores_a),
            "variant_b_count": len(scores_b),
            "variant_a_average": avg_a,
            "variant_b_average": avg_b,
            "winner": winner,
            "confidence": "low" if min(len(scores_a), len(scores_b)) < 3 else "medium",
            "created_at": self._now(),
        }
        self.storage.append(self.ab_tests_file, record)
        return record

    def _variant_scores(self, analytics: list[dict], variant: str, metric: str) -> list[float]:
        values = []
        variant_lower = variant.lower()
        for item in analytics:
            agents = " ".join(item.get("agents_used", [])).lower()
            provider = str(item.get("provider", "")).lower()
            model = str(item.get("model", "")).lower()
            task_type = str(item.get("task_type", "")).lower()
            if variant_lower not in f"{agents} {provider} {model} {task_type}":
                continue
            value = item.get(metric)
            if isinstance(value, (int, float)):
                values.append(float(value))
        return values

    def list_ab_tests(self, workspace_id: str | None = None, limit: int = 25) -> list[dict]:
        records = self._workspace_filter(self.storage.read_list(self.ab_tests_file), workspace_id)
        return list(reversed(records[-limit:]))

    def regressions(self, workspace_id: str | None = None) -> dict:
        records = self._workspace_filter(self.storage.read_list(self.regressions_file), workspace_id)
        return {
            "workspace_id": workspace_id,
            "regression_count": len(records),
            "severity_counts": dict(Counter(item.get("severity", "unknown") for item in records)),
            "recent_regressions": list(reversed(records[-20:])),
        }

    def export(self, workspace_id: str | None = None, format: str = "json") -> str:
        payload = {
            "dashboard": self.dashboard(workspace_id),
            "benchmarks": self.list_benchmarks(),
            "runs": self.list_runs(workspace_id, limit=100),
            "ab_tests": self.list_ab_tests(workspace_id, limit=100),
            "regressions": self.regressions(workspace_id).get("recent_regressions", []),
        }
        if format == "json":
            return json.dumps(payload, indent=2)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["record_type", "id", "task_type", "score", "status", "created_at"])
        writer.writeheader()
        for run in payload["runs"]:
            writer.writerow(
                {
                    "record_type": "evaluation_run",
                    "id": run.get("evaluation_run_id"),
                    "task_type": run.get("task_type") or "mixed",
                    "score": run.get("score"),
                    "status": run.get("status"),
                    "created_at": run.get("created_at"),
                }
            )
        for regression in payload["regressions"]:
            writer.writerow(
                {
                    "record_type": "regression",
                    "id": regression.get("regression_id"),
                    "task_type": "",
                    "score": regression.get("current_score"),
                    "status": regression.get("severity"),
                    "created_at": regression.get("created_at"),
                }
            )
        return output.getvalue()
