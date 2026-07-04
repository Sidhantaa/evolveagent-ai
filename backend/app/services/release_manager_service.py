from __future__ import annotations

from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.feature_registry_service import FeatureRegistryService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

VERSION_CHECKLIST = [
    "Backend tests pass (pytest -q).",
    "Frontend build succeeds (npm run build).",
    "VERSIONS.md, README.md, and FINAL_CHECKLIST.md updated.",
    "New service is additive — no feature removed, API contracts preserved.",
    "Safety boundary documented (planning-first, governance-logged, no secrets).",
    "PR opened, CI green, merged to main.",
]
DEMO_CHECKLIST = [
    "Reset demo data and seed a demo-safe workspace (/api/demo).",
    "Open the Master Agent hero and run a sample query.",
    "Show Global Search, Activity Timeline, and Dashboard Home.",
    "Trigger a risky action and show it held for approval.",
    "Open the Governance Console and Feature Registry.",
]
LINEAR_SYNC_CHECKLIST = [
    "Move the issue to In Progress when starting.",
    "Reference the version in the branch name (linear/vNN-...).",
    "Link the PR to the issue.",
    "Move to Done only after merge is verified on main.",
]


class ReleaseManagerService:
    """v89.0 Release Manager — prepare versions professionally.

    Read-only generators for release hygiene: a **version checklist**, a **changelog**
    (derived from the feature registry, grouped by version), a **PR summary** generator,
    **release notes**, a **GitHub tag planner** (suggests the next semver-ish tag), a
    **demo checklist**, and a **Linear sync checklist**. It produces text only — it does
    not tag, push, or call GitHub/Linear. Governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService, feature_registry: FeatureRegistryService):
        self.storage = storage
        self.governance = governance_service
        self.features = feature_registry

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="release_manager",
                agent_name="Release Manager",
                action_type=action_type,
                tool_used="ReleaseManagerService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def changelog(self) -> dict:
        features = self.features.list_features()["features"]
        by_version: dict[str, list[str]] = {}
        for feature in features:
            by_version.setdefault(feature["version"], []).append(feature["name"])
        lines = ["# Changelog", ""]
        for version in sorted(by_version.keys(), reverse=True):
            lines.append(f"## {version}")
            lines += [f"- {name}" for name in by_version[version]]
            lines.append("")
        self._log("changelog_generated", f"Generated a changelog across {len(by_version)} version group(s).")
        return {"format": "markdown", "content": "\n".join(lines), "version_groups": len(by_version)}

    def tag_planner(self, current_tag: str | None = None) -> dict:
        current = current_tag or "v0.0.0"
        parts = current.lstrip("v").split(".")
        try:
            major, minor, patch = (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0, int(parts[2]) if len(parts) > 2 else 0)
        except (ValueError, IndexError):
            major, minor, patch = 0, 0, 0
        return {
            "current": current,
            "suggested_patch": f"v{major}.{minor}.{patch + 1}",
            "suggested_minor": f"v{major}.{minor + 1}.0",
            "suggested_major": f"v{major + 1}.0.0",
            "note": "Suggestion only — this does not create or push any git tag.",
        }

    def pr_summary(self, title: str, changes: list[str]) -> dict:
        changes = [c for c in (changes or []) if isinstance(c, str)][:30]
        change_lines = [f"- {c}" for c in changes] or ["- (describe changes)"]
        lines = [f"## {title}", "", "### Changes", *change_lines, "",
                 "### Safety", "- Additive; planning-first; governance-logged; no secrets exposed.", "",
                 "### Verification", "- Backend tests pass; frontend build succeeds."]
        self._log("pr_summary_generated", "Generated a PR summary.")
        return {"format": "markdown", "content": "\n".join(lines)}

    def release_notes(self, version: str, highlights: list[str]) -> dict:
        highlights = [h for h in (highlights or []) if isinstance(h, str)][:30]
        highlight_lines = [f"- {h}" for h in highlights] or ["- (add highlights)"]
        lines = [f"# Release {version}", "", f"_Released {self._now()[:10]}_", "", "## Highlights",
                 *highlight_lines, "",
                 "## Notes", "- Local-first, planning-first, governance-logged. Not AGI."]
        self._log("release_notes_generated", f"Generated release notes for {version}.")
        return {"format": "markdown", "content": "\n".join(lines)}

    def dashboard(self) -> dict:
        self._log("release_dashboard_viewed", "Rendered the Release Manager dashboard.")
        return {
            "version_checklist": VERSION_CHECKLIST,
            "demo_checklist": DEMO_CHECKLIST,
            "linear_sync_checklist": LINEAR_SYNC_CHECKLIST,
            "tag_planner": self.tag_planner("v90.0.0"),
            "note": "Read-only release hygiene generators — produces text only; no git tag/push, no GitHub/Linear calls.",
        }

    def analytics_summary(self) -> dict:
        return {"release_manager_checklists": 3}

    def summary(self) -> dict:
        return {
            "checklists": ["version", "demo", "linear_sync"],
            "generators": ["changelog", "pr_summary", "release_notes", "tag_planner"],
            "note": "Read-only release preparation — text generators only; no tagging/pushing/external calls.",
        }
