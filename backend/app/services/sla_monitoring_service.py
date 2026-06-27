from __future__ import annotations

from app.services.storage_service import StorageService

RATING_THRESHOLDS = [
    (85, "excellent"),
    (70, "good"),
    (50, "watch"),
]


class SLAMonitoringService:
    """EVO-322 Production SLA Monitoring.

    Calculates platform reliability signals purely from existing local data. It
    never calls external monitoring tools — it reads analytics, governance,
    quality, evaluation, codex, and autopilot collections and derives proxy
    reliability metrics.
    """

    def __init__(self, storage: StorageService):
        self.storage = storage

    def _rating(self, score: float) -> str:
        return next((label for threshold, label in RATING_THRESHOLDS if score >= threshold), "at_risk")

    def sla(self) -> dict:
        analytics = self.storage.read_list("agent_analytics.json")
        governance = self.storage.read_list("governance_log.json")
        quality_runs = self.storage.read_list("quality_runs.json")
        evaluation_runs = self.storage.read_list("evaluation_runs.json")
        codex_jobs = self.storage.read_list("codex_jobs.json")
        autopilot_runs = self.storage.read_list("autopilot_runs.json")

        latencies = [run.get("latency_ms", 0) for run in analytics if isinstance(run.get("latency_ms"), (int, float))]
        average_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0

        total_runs = len(analytics)
        successful_runs = sum(1 for run in analytics if run.get("success", True))
        fallback_runs = sum(1 for run in analytics if run.get("fallback_used"))
        success_rate = round((successful_runs / total_runs) * 100, 2) if total_runs else 100.0
        fallback_rate = round((fallback_runs / total_runs) * 100, 2) if total_runs else 0.0

        blocked_action_count = sum(1 for event in governance if event.get("blocked"))
        failed_quality_runs = sum(
            1 for run in quality_runs if not (run.get("quality_gate") or {}).get("passed", True)
        )
        failed_codex_jobs = sum(1 for job in codex_jobs if job.get("status") == "failed")
        failed_autopilot = sum(1 for run in autopilot_runs if run.get("status") == "failed")
        eval_scores = [
            run.get("overall_judge_score")
            for run in evaluation_runs
            if isinstance(run.get("overall_judge_score"), (int, float))
        ]
        average_eval_score = round(sum(eval_scores) / len(eval_scores), 2) if eval_scores else 0

        # Uptime proxy: blend success rate with penalties for fallbacks, blocked
        # actions, and downstream job failures. Starts from the success rate.
        score = success_rate
        score -= min(fallback_rate, 30) * 0.5
        score -= min(blocked_action_count, 20) * 1.0
        score -= min(failed_quality_runs, 10) * 2.0
        score -= min(failed_codex_jobs, 10) * 1.5
        score -= min(failed_autopilot, 10) * 1.5
        uptime_proxy_score = max(0, min(100, round(score)))

        recent_incidents: list[dict] = []
        for event in reversed(governance):
            if event.get("blocked"):
                recent_incidents.append(
                    {
                        "type": "blocked_action",
                        "action_type": event.get("action_type"),
                        "agent_name": event.get("agent_name"),
                        "reason": event.get("reason"),
                    }
                )
            if len(recent_incidents) >= 5:
                break
        for job in reversed(codex_jobs):
            if len(recent_incidents) >= 8:
                break
            if job.get("status") == "failed":
                recent_incidents.append(
                    {"type": "codex_job_failed", "job_id": job.get("job_id"), "reason": job.get("status_detail")}
                )

        recommendations: list[str] = []
        if fallback_rate > 20:
            recommendations.append("Fallback rate is high; review primary model availability and prompts.")
        if blocked_action_count:
            recommendations.append("Investigate blocked governance actions to confirm they are expected.")
        if failed_quality_runs:
            recommendations.append("Address failing quality gates before the next release.")
        if failed_codex_jobs or failed_autopilot:
            recommendations.append("Re-run or triage failed automation jobs.")
        if average_eval_score and average_eval_score < 65:
            recommendations.append("Average evaluation score is low; tune underperforming workflows.")
        if not recommendations:
            recommendations.append("No reliability issues detected; maintain current monitoring cadence.")

        return {
            "uptime_proxy_score": uptime_proxy_score,
            "average_latency_ms": average_latency,
            "success_rate": success_rate,
            "fallback_rate": fallback_rate,
            "blocked_action_count": blocked_action_count,
            "failed_quality_runs": failed_quality_runs,
            "failed_codex_jobs": failed_codex_jobs,
            "recent_incidents": recent_incidents,
            "sla_rating": self._rating(uptime_proxy_score),
            "recommendations": recommendations,
        }
