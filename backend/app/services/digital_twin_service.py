from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService
from app.services.workspace_service import WorkspaceService


class DigitalTwinService:
    filename = "digital_twin_profiles.json"

    def __init__(
        self,
        storage: StorageService,
        workspace_service: WorkspaceService,
        governance_service: GovernanceService,
    ):
        self.storage = storage
        self.workspace_service = workspace_service
        self.governance = governance_service

    # Profiles auto-refresh at most this often when consumed via get_profile()
    # -- bounds the extra write + governance log that refresh_profile() causes
    # to once per window per workspace, rather than on every single real
    # orchestration run that consults this profile.
    _STALE_AFTER_SECONDS = 3600

    def get_profile(self, workspace_id: str | None = None) -> dict[str, Any]:
        resolved = self.workspace_service.resolve_workspace_id(workspace_id)
        profile = self._profile_for(resolved)
        if profile and not self._is_stale(profile):
            return profile
        return self.refresh_profile(resolved)

    def _is_stale(self, profile: dict[str, Any]) -> bool:
        updated_at = profile.get("updated_at")
        if not updated_at:
            return True
        try:
            age = (datetime.now(UTC) - datetime.fromisoformat(updated_at)).total_seconds()
        except ValueError:
            return True
        return age > self._STALE_AFTER_SECONDS

    def refresh_profile(self, workspace_id: str | None = None) -> dict[str, Any]:
        resolved = self.workspace_service.resolve_workspace_id(workspace_id)
        existing = self._profile_for(resolved) or {}
        now = datetime.now(UTC).isoformat()
        preferences = self._workspace_items("user_preferences.json", resolved)
        feedback = self._workspace_items("feedback.json", resolved)
        runs = self._workspace_items("agent_analytics.json", resolved)
        goals = self._workspace_items("goals.json", resolved)

        preference_scores = Counter()
        evidence: dict[str, list[str]] = {}
        for item in preferences:
            name = item.get("preference")
            if not name:
                continue
            preference_scores[name] += int(item.get("score", 0) or 0)
            evidence.setdefault(name, []).extend(str(value) for value in item.get("evidence", [])[-3:])

        feedback_counts = Counter(item.get("rating", "unknown") for item in feedback)
        task_counts = Counter(item.get("task_type", "unknown") for item in runs)
        average_score = self._average(item.get("overall_judge_score") for item in runs)

        profile = {
            "profile_id": existing.get("profile_id") or str(uuid4()),
            "workspace_id": resolved,
            "version": 1,
            "created_at": existing.get("created_at") or now,
            "updated_at": now,
            "source": "derived_from_feedback_learning_and_runs",
            "style_profile": {
                "detail_level": self._detail_level(preference_scores),
                "technical_level": self._technical_level(preference_scores),
                "format": self._format_preference(preference_scores),
                "planning_style": self._planning_style(preference_scores, goals),
                "tone": existing.get("style_profile", {}).get("tone", "direct and practical"),
            },
            "preference_scores": dict(preference_scores),
            "top_preferences": [
                {"preference": name, "score": score, "evidence": evidence.get(name, [])[-3:]}
                for name, score in preference_scores.most_common(8)
            ],
            "task_patterns": [
                {"task_type": name, "count": count}
                for name, count in task_counts.most_common(8)
            ],
            "feedback_summary": {
                "helpful": feedback_counts.get("helpful", 0),
                "not_helpful": feedback_counts.get("not_helpful", 0),
                "saved": feedback_counts.get("saved", 0),
                "total": sum(feedback_counts.values()),
            },
            "quality_summary": {
                "runs_analyzed": len(runs),
                "average_judge_score": average_score,
            },
            "recommendations": self._recommendations(preference_scores, task_counts, average_score),
            "manual_overrides": existing.get("manual_overrides", {}),
            "safety_note": "This profile tunes orchestration and presentation preferences only. It does not train or fine-tune the base LLM.",
        }
        profile = self._apply_overrides(profile)
        self._upsert(profile)
        self._log("digital_twin_profile_refreshed", resolved, "Refreshed Digital Twin work-style profile.")
        return profile

    def update_profile(self, workspace_id: str | None = None, updates: dict[str, Any] | None = None) -> dict[str, Any]:
        resolved = self.workspace_service.resolve_workspace_id(workspace_id)
        profile = self.get_profile(resolved)
        updates = updates or {}
        overrides = profile.get("manual_overrides", {})

        for key in ("detail_level", "technical_level", "format", "planning_style", "tone"):
            if key in updates and updates[key] is not None:
                overrides[key] = str(updates[key])[:120]
        if "notes" in updates and updates["notes"] is not None:
            overrides["notes"] = str(updates["notes"])[:1000]

        profile["manual_overrides"] = overrides
        profile["updated_at"] = datetime.now(UTC).isoformat()
        profile = self._apply_overrides(profile)
        self._upsert(profile)
        self._log("digital_twin_profile_updated", resolved, "Applied manual Digital Twin profile override.")
        return profile

    def export_profile(self, workspace_id: str | None = None) -> dict[str, Any]:
        resolved = self.workspace_service.resolve_workspace_id(workspace_id)
        profile = self.get_profile(resolved)
        self._log("digital_twin_profile_exported", resolved, "Exported Digital Twin profile data for the user.")
        return {
            "exported_at": datetime.now(UTC).isoformat(),
            "workspace_id": resolved,
            "format": "evolveagent.digital_twin.v1",
            "profile": profile,
        }

    def reset_profile(self, workspace_id: str | None = None) -> dict[str, Any]:
        resolved = self.workspace_service.resolve_workspace_id(workspace_id)
        self._remove_profile(resolved)
        self._log("digital_twin_profile_reset", resolved, "Reset Digital Twin profile; manual overrides cleared and re-derived.")
        return self.refresh_profile(resolved)

    def delete_profile(self, workspace_id: str | None = None) -> dict[str, Any]:
        resolved = self.workspace_service.resolve_workspace_id(workspace_id)
        removed = self._remove_profile(resolved)
        self._log("digital_twin_profile_deleted", resolved, "Deleted Digital Twin profile data at user request.")
        return {"workspace_id": resolved, "deleted": removed}

    def _remove_profile(self, workspace_id: str) -> bool:
        profiles = self.storage.read_list(self.filename)
        remaining = [item for item in profiles if item.get("workspace_id") != workspace_id]
        if len(remaining) == len(profiles):
            return False
        self.storage.write_list(self.filename, remaining)
        return True

    def _profile_for(self, workspace_id: str) -> dict[str, Any] | None:
        return next(
            (item for item in self.storage.read_list(self.filename) if item.get("workspace_id") == workspace_id),
            None,
        )

    def _upsert(self, profile: dict[str, Any]) -> None:
        profiles = self.storage.read_list(self.filename)
        existing = next((item for item in profiles if item.get("workspace_id") == profile.get("workspace_id")), None)
        if existing:
            existing.update(profile)
        else:
            profiles.append(profile)
        self.storage.write_list(self.filename, profiles)

    def _workspace_items(self, filename: str, workspace_id: str) -> list[dict[str, Any]]:
        return [item for item in self.storage.read_list(filename) if item.get("workspace_id") == workspace_id]

    @staticmethod
    def _average(values: Any) -> float:
        usable = [float(value) for value in values if isinstance(value, (int, float))]
        return round(sum(usable) / len(usable), 2) if usable else 0

    @staticmethod
    def _detail_level(scores: Counter) -> str:
        if scores.get("detailed", 0) > scores.get("concise", 0):
            return "detailed"
        if scores.get("concise", 0):
            return "concise"
        return "balanced"

    @staticmethod
    def _technical_level(scores: Counter) -> str:
        if scores.get("technical", 0) > scores.get("simple", 0):
            return "technical"
        if scores.get("simple", 0):
            return "simple"
        return "adaptive"

    @staticmethod
    def _format_preference(scores: Counter) -> str:
        if scores.get("prefers_step_by_step", 0) >= max(scores.get("prefers_bullets", 0), 1):
            return "step_by_step"
        if scores.get("prefers_bullets", 0):
            return "bullets"
        if scores.get("prefers_code_examples", 0):
            return "code_examples"
        return "mixed"

    @staticmethod
    def _planning_style(scores: Counter, goals: list[dict[str, Any]]) -> str:
        if goals:
            return "goal_oriented"
        if scores.get("prefers_step_by_step", 0):
            return "sequenced"
        return "pragmatic"

    @staticmethod
    def _recommendations(scores: Counter, task_counts: Counter, average_score: float) -> list[str]:
        recommendations = []
        if scores.get("concise", 0) > scores.get("detailed", 0):
            recommendations.append("Default to concise answers with optional detail expansion.")
        if scores.get("prefers_step_by_step", 0):
            recommendations.append("Use numbered steps for implementation and setup tasks.")
        if scores.get("prefers_code_examples", 0):
            recommendations.append("Include code examples for coding and architecture tasks.")
        if task_counts:
            recommendations.append(f"Optimize routing for frequent task type: {task_counts.most_common(1)[0][0]}.")
        if average_score and average_score < 78:
            recommendations.append("Use Developer Mode review for low-scoring workflows before saving as good answers.")
        if not recommendations:
            recommendations.append("Keep collecting feedback to personalize response style.")
        return recommendations

    @staticmethod
    def _apply_overrides(profile: dict[str, Any]) -> dict[str, Any]:
        overrides = profile.get("manual_overrides", {})
        style = dict(profile.get("style_profile", {}))
        for key in ("detail_level", "technical_level", "format", "planning_style", "tone"):
            if overrides.get(key):
                style[key] = overrides[key]
        profile["style_profile"] = style
        return profile

    def _log(self, action_type: str, workspace_id: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                workspace_id=workspace_id,
                task_type="digital_twin",
                agent_name="Digital Twin Work Style Engine",
                action_type=action_type,
                tool_used="DigitalTwinService",
                permission_level="read_only",
                approved=False,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )
