from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

MEMBER_TYPES = ["human", "ai_agent"]
ASSIGNMENT_PRIORITIES = ["low", "medium", "high"]
ASSIGNMENT_STATUSES = ["todo", "in_progress", "blocked", "done", "archived"]


class TeamManagerService:
    """v31.0 AI Team Lead / Manager Mode.

    Manages a mixed human + AI team locally: members, assignments, standups,
    sprint planning/review, and productivity analytics. It plans and summarizes
    only — it never sends external messages or changes real project state. Every
    stateful action is governance-logged.
    """

    members_file = "team_members.json"
    assignments_file = "team_assignments.json"
    standups_file = "team_standups.json"
    sprints_file = "team_sprints.json"
    reviews_file = "team_reviews.json"
    reports_file = "team_manager_reports.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _today(self):
        return datetime.now(UTC).date()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _enum(self, value, allowed: list[str], default: str) -> str:
        candidate = str(value or "").strip().lower()
        return candidate if candidate in allowed else default

    def _string_list(self, values, limit: int = 20, item_max: int = 200) -> list[str]:
        cleaned: list[str] = []
        for value in values or []:
            text = str(value).strip()[:item_max]
            if text and text not in cleaned:
                cleaned.append(text)
            if len(cleaned) >= limit:
                break
        return cleaned

    def _days_until(self, value):
        if not value:
            return None
        try:
            due = datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None
        return (due - self._today()).days

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="team_manager",
                agent_name="AI Team Lead",
                action_type=action_type,
                tool_used="TeamManagerService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Members
    # ------------------------------------------------------------------
    def list_members(self) -> list[dict]:
        return self.storage.read_list(self.members_file)

    def create_member(self, data: dict) -> dict:
        member = {
            "member_id": str(uuid4()),
            "name": self._clean(data.get("name"), 160) or "Team member",
            "member_type": self._enum(data.get("member_type"), MEMBER_TYPES, "human"),
            "role": self._clean(data.get("role"), 160),
            "skills": self._string_list(data.get("skills")),
            "active": True,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.members_file, member)
        self._log("team_member_created", f"Added {member['member_type']} member: {member['name']}.")
        return member

    def update_member(self, member_id: str, updates: dict) -> dict:
        members = self.storage.read_list(self.members_file)
        member = next((m for m in members if m.get("member_id") == member_id), None)
        if member is None:
            raise ValueError("Member not found")
        if updates.get("name") is not None:
            member["name"] = self._clean(updates["name"], 160) or member["name"]
        if updates.get("member_type") is not None:
            member["member_type"] = self._enum(updates["member_type"], MEMBER_TYPES, member["member_type"])
        if updates.get("role") is not None:
            member["role"] = self._clean(updates["role"], 160)
        if updates.get("skills") is not None:
            member["skills"] = self._string_list(updates["skills"])
        if updates.get("active") is not None:
            member["active"] = bool(updates["active"])
        member["updated_at"] = self._now()
        self.storage.write_list(self.members_file, members)
        self._log("team_member_updated", f"Updated member {member_id}.")
        return member

    # ------------------------------------------------------------------
    # Assignments
    # ------------------------------------------------------------------
    def list_assignments(self) -> list[dict]:
        return self.storage.read_list(self.assignments_file)

    def create_assignment(self, data: dict) -> dict:
        assignment = {
            "assignment_id": str(uuid4()),
            "title": self._clean(data.get("title"), 200),
            "owner_id": self._clean(data.get("owner_id"), 120) or None,
            "owner_name": self._clean(data.get("owner_name"), 160),
            "priority": self._enum(data.get("priority"), ASSIGNMENT_PRIORITIES, "medium"),
            "status": self._enum(data.get("status"), ASSIGNMENT_STATUSES, "todo"),
            "due_date": self._clean(data.get("due_date"), 10) or None,
            "blocked_reason": self._clean(data.get("blocked_reason"), 500),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.assignments_file, assignment)
        self._log("team_assignment_created", f"Created assignment: {assignment['title'] or assignment['assignment_id']}.")
        return assignment

    def update_assignment(self, assignment_id: str, updates: dict) -> dict:
        assignments = self.storage.read_list(self.assignments_file)
        assignment = next((a for a in assignments if a.get("assignment_id") == assignment_id), None)
        if assignment is None:
            raise ValueError("Assignment not found")
        if updates.get("title") is not None:
            assignment["title"] = self._clean(updates["title"], 200)
        if updates.get("owner_id") is not None:
            assignment["owner_id"] = self._clean(updates["owner_id"], 120) or None
        if updates.get("owner_name") is not None:
            assignment["owner_name"] = self._clean(updates["owner_name"], 160)
        if updates.get("priority") is not None:
            assignment["priority"] = self._enum(updates["priority"], ASSIGNMENT_PRIORITIES, assignment["priority"])
        if updates.get("status") is not None:
            assignment["status"] = self._enum(updates["status"], ASSIGNMENT_STATUSES, assignment["status"])
        if updates.get("due_date") is not None:
            assignment["due_date"] = self._clean(updates["due_date"], 10) or None
        if updates.get("blocked_reason") is not None:
            assignment["blocked_reason"] = self._clean(updates["blocked_reason"], 500)
        assignment["updated_at"] = self._now()
        self.storage.write_list(self.assignments_file, assignments)
        self._log("team_assignment_updated", f"Updated assignment {assignment_id}.")
        return assignment

    # ------------------------------------------------------------------
    # Standups
    # ------------------------------------------------------------------
    def create_standup(self) -> dict:
        assignments = self.list_assignments()
        in_progress = [a for a in assignments if a.get("status") == "in_progress"]
        blocked = [a for a in assignments if a.get("status") == "blocked"]
        done = [a for a in assignments if a.get("status") == "done"]
        overdue = [a for a in assignments if a.get("status") not in {"done", "archived"} and (self._days_until(a.get("due_date")) or 0) < 0]
        standup = {
            "standup_id": str(uuid4()),
            "date": self._today().isoformat(),
            "summary": (
                f"{len(in_progress)} in progress, {len(blocked)} blocked, "
                f"{len(done)} done, {len(overdue)} overdue."
            ),
            "in_progress": [{"title": a.get("title"), "owner": a.get("owner_name")} for a in in_progress[:10]],
            "blockers": [{"title": a.get("title"), "reason": a.get("blocked_reason")} for a in blocked[:10]],
            "completed": [a.get("title") for a in done[:10]],
            "overdue": [{"title": a.get("title"), "owner": a.get("owner_name")} for a in overdue[:10]],
            "created_at": self._now(),
        }
        self.storage.append(self.standups_file, standup)
        self._log("team_standup_created", f"Generated standup for {standup['date']}.")
        return standup

    def list_standups(self, limit: int = 20) -> list[dict]:
        return list(reversed(self.storage.read_list(self.standups_file)[-limit:]))

    # ------------------------------------------------------------------
    # Sprints + reviews
    # ------------------------------------------------------------------
    def create_sprint(self, data: dict) -> dict:
        sprint = {
            "sprint_id": str(uuid4()),
            "name": self._clean(data.get("name"), 160) or "Sprint",
            "goals": self._string_list(data.get("goals")),
            "tasks": self._string_list(data.get("tasks"), limit=40),
            "owners": self._string_list(data.get("owners")),
            "start_date": self._clean(data.get("start_date"), 10) or None,
            "end_date": self._clean(data.get("end_date"), 10) or None,
            "review_checklist": [
                "Confirm each sprint goal is met or carried over.",
                "Review blocked items and their owners.",
                "Capture learnings and next-sprint adjustments.",
            ],
            "status": "planned",
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.sprints_file, sprint)
        self._log("team_sprint_created", f"Created sprint: {sprint['name']}.")
        return sprint

    def list_sprints(self, limit: int = 20) -> list[dict]:
        return list(reversed(self.storage.read_list(self.sprints_file)[-limit:]))

    def get_sprint(self, sprint_id: str) -> dict | None:
        return next((s for s in self.storage.read_list(self.sprints_file) if s.get("sprint_id") == sprint_id), None)

    def create_review(self, sprint_id: str, data: dict) -> dict:
        sprint = self.get_sprint(sprint_id)
        if sprint is None:
            raise ValueError("Sprint not found")
        analytics = self.analytics()
        review = {
            "review_id": str(uuid4()),
            "sprint_id": sprint_id,
            "sprint_name": sprint.get("name"),
            "summary": self._clean(data.get("summary"), 2000)
            or f"Reviewed {sprint.get('name')}: {analytics['completed_tasks']} completed, {analytics['blocked_tasks']} blocked.",
            "completed_count": analytics["completed_tasks"],
            "blocked_count": analytics["blocked_tasks"],
            "carry_over": self._string_list(data.get("carry_over")),
            "learnings": self._string_list(data.get("learnings")),
            "created_at": self._now(),
        }
        self.storage.append(self.reviews_file, review)
        # Mark sprint reviewed.
        sprints = self.storage.read_list(self.sprints_file)
        for item in sprints:
            if item.get("sprint_id") == sprint_id:
                item["status"] = "reviewed"
                item["updated_at"] = self._now()
        self.storage.write_list(self.sprints_file, sprints)
        self._log("team_sprint_reviewed", f"Created review for sprint {sprint_id}.")
        return review

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------
    def analytics(self) -> dict:
        assignments = self.list_assignments()
        members = self.list_members()
        member_type = {m.get("member_id"): m.get("member_type") for m in members}
        completed = sum(1 for a in assignments if a.get("status") == "done")
        blocked = sum(1 for a in assignments if a.get("status") == "blocked")
        overdue = sum(1 for a in assignments if a.get("status") not in {"done", "archived"} and (self._days_until(a.get("due_date")) or 0) < 0)
        ai_tasks = sum(1 for a in assignments if member_type.get(a.get("owner_id")) == "ai_agent")
        human_tasks = sum(1 for a in assignments if member_type.get(a.get("owner_id")) == "human")
        workload = Counter(a.get("owner_name") or "Unassigned" for a in assignments if a.get("status") not in {"done", "archived"})
        return {
            "total_assignments": len(assignments),
            "completed_tasks": completed,
            "blocked_tasks": blocked,
            "overdue_tasks": overdue,
            "ai_tasks": ai_tasks,
            "human_tasks": human_tasks,
            "completion_rate": round((completed / len(assignments)) * 100, 2) if assignments else 0,
            "workload_by_owner": [{"owner": owner, "open_tasks": count} for owner, count in workload.most_common(12)],
        }

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard(self) -> dict:
        members = self.list_members()
        analytics = self.analytics()
        recent_standups = self.list_standups(limit=1)
        return {
            "member_count": len(members),
            "ai_member_count": sum(1 for m in members if m.get("member_type") == "ai_agent"),
            "human_member_count": sum(1 for m in members if m.get("member_type") == "human"),
            "analytics": analytics,
            "sprint_count": len(self.storage.read_list(self.sprints_file)),
            "latest_standup": recent_standups[0] if recent_standups else None,
            "recommended_next_action": (
                "Add team members and assignments, then generate a standup."
                if not members
                else "Generate a standup or plan the next sprint."
            ),
        }
