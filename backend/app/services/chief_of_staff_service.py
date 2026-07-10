from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

FOLLOWUP_SOURCES = ["manual", "goal", "business", "support", "approval", "risk"]
FOLLOWUP_PRIORITIES = ["low", "medium", "high"]
FOLLOWUP_STATUSES = ["open", "done", "snoozed", "archived"]
SEVERITY_ORDER = {"high": 3, "medium": 2, "low": 1}

# v180 — real external signal (opt-in). Comma-separated "owner/name" repos the
# Chief of Staff watches for open PRs/issues via the already-real, read-only
# GitHubConnectorService. No repos configured => no GitHub items, not an error.
GITHUB_REPOS_ENV = "CHIEF_OF_STAFF_GITHUB_REPOS"


class ChiefOfStaffService:
    """v19.0 AI Chief of Staff.

    Turns existing local data (goals, tasks, business leads/support cases,
    project risks, approvals, and its own follow-ups) into daily plans, weekly
    plans, ranked priorities, and follow-up tracking. It only reads and ranks —
    it never sends reminders, writes to a calendar/email, or executes actions.
    Every stateful action is logged through governance.

    v180: when a GitHubConnectorService is wired and CHIEF_OF_STAFF_GITHUB_REPOS
    names one or more real repos, rank_priorities() also folds in real open pull
    requests and issues from those repos (read-only, governance-logged by the
    connector itself) — genuine external signal, not another internal-only
    heuristic. Without either precondition, GitHub simply contributes no items;
    every other priority source is completely unaffected.
    """

    daily_file = "chief_daily_plans.json"
    weekly_file = "chief_weekly_plans.json"
    followups_file = "chief_followups.json"
    priority_file = "chief_priority_scores.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, github=None):
        self.storage = storage
        self.governance = governance_service
        self.github = github

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _today(self) -> date:
        return datetime.now(UTC).date()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _enum(self, value, allowed: list[str], default: str) -> str:
        candidate = str(value or "").strip().lower()
        return candidate if candidate in allowed else default

    def _filter_workspace(self, items: list[dict], workspace_id: str | None) -> list[dict]:
        if not workspace_id:
            return items
        return [item for item in items if item.get("workspace_id") == workspace_id]

    def _parse_date(self, value: str | None) -> date | None:
        if not value:
            return None
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def _days_until(self, due: str | None) -> int | None:
        parsed = self._parse_date(due)
        if parsed is None:
            return None
        return (parsed - self._today()).days

    @staticmethod
    def _age_days(iso_ts: str | None) -> int | None:
        if not iso_ts:
            return None
        try:
            parsed = datetime.fromisoformat(str(iso_ts).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return max(0, (datetime.now(UTC) - parsed).days)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _github_repos() -> list[str]:
        raw = os.environ.get(GITHUB_REPOS_ENV, "")
        return [r.strip() for r in raw.split(",") if r.strip()][:10]

    def _github_items(self) -> list[dict]:
        """Real, opt-in, read-only signal from GitHubConnectorService. Never
        raises — a connector-level failure or a not-configured precondition
        just means zero GitHub items, not an error surfaced to the caller."""
        if self.github is None:
            return []
        repos = self._github_repos()
        if not repos:
            return []
        items: list[dict] = []
        for repo in repos:
            try:
                pulls = self.github.list_pull_requests(repo, state="open", limit=20)
            except Exception:
                pulls = {"degraded": True, "pull_requests": []}
            if not pulls.get("degraded"):
                for pr in pulls.get("pull_requests", []):
                    age_days = self._age_days(pr.get("created_at"))
                    score = 20
                    reasons = [f"Open PR in {repo}."]
                    if pr.get("draft"):
                        score -= 10
                        reasons.append("Draft.")
                    if age_days is not None and age_days >= 7:
                        score += 20
                        reasons.append(f"Open {age_days}+ days — needs review.")
                    elif age_days is not None and age_days >= 3:
                        score += 10
                        reasons.append(f"Open {age_days} days.")
                    items.append(self._priority_item(
                        "github_pr", pr.get("number"), f"{repo}#{pr.get('number')}: {pr.get('title')}",
                        max(score, 5), " ".join(reasons), "Review and merge or request changes.",
                    ))

            try:
                issues = self.github.list_issues(repo, state="open", limit=20)
            except Exception:
                issues = {"degraded": True, "issues": []}
            if not issues.get("degraded"):
                for issue in issues.get("issues", []):
                    age_days = self._age_days(issue.get("created_at"))
                    score = 15
                    reasons = [f"Open issue in {repo}."]
                    if age_days is not None and age_days >= 14:
                        score += 15
                        reasons.append(f"Open {age_days}+ days.")
                    items.append(self._priority_item(
                        "github_issue", issue.get("number"), f"{repo}#{issue.get('number')}: {issue.get('title')}",
                        score, " ".join(reasons), "Triage or close this issue.",
                    ))
        return items

    def status(self) -> dict:
        return {
            "available": True,
            "github_wired": self.github is not None,
            "github_repos_env": GITHUB_REPOS_ENV,
            "github_repos_configured": self._github_repos(),
            "note": "Reads real open PRs/issues from configured GitHub repos (read-only, opt-in via "
                    f"{GITHUB_REPOS_ENV} + GITHUB_TOKEN) and folds them into priority ranking and daily "
                    "plans alongside internal goals/tasks/leads/risks/approvals/follow-ups. No repos "
                    "configured means no GitHub items — not an error.",
        }

    def _log(self, action_type: str, workspace_id: str | None, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                workspace_id=workspace_id,
                task_type="chief_of_staff",
                agent_name="AI Chief of Staff",
                action_type=action_type,
                tool_used="ChiefOfStaffService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    def _tasks_for(self, goal_id: str) -> list[dict]:
        graph = next(
            (item for item in self.storage.read_list("task_graphs.json") if item.get("goal_id") == goal_id),
            None,
        )
        return graph.get("tasks", []) if graph else []

    # ------------------------------------------------------------------
    # Priority ranking
    # ------------------------------------------------------------------
    def rank_priorities(self, workspace_id: str | None = None, log: bool = False) -> list[dict]:
        items: list[dict] = []

        goals = self._filter_workspace(self.storage.read_list("goals.json"), workspace_id)
        for goal in goals:
            if goal.get("status") in {"archived", "completed"}:
                continue
            score = 30
            reasons = ["Active goal."]
            if goal.get("risk_level") == "high":
                score += 30
                reasons.append("High risk.")
            if (goal.get("progress_percent") or 0) < 30:
                score += 10
                reasons.append("Low progress.")
            items.append(
                self._priority_item(
                    "goal",
                    goal.get("goal_id"),
                    goal.get("title") or "Untitled goal",
                    score,
                    " ".join(reasons),
                    "Advance the next task or add human checkpoints.",
                )
            )
            for task in self._tasks_for(goal.get("goal_id")):
                if task.get("status") in {"done", "archived", "canceled"}:
                    continue
                task_score = 15
                task_reasons = ["Open task."]
                if task.get("status") == "blocked":
                    task_score += 30
                    task_reasons.append("Blocked.")
                items.append(
                    self._priority_item(
                        "task",
                        task.get("task_id"),
                        task.get("title") or "Untitled task",
                        task_score,
                        " ".join(task_reasons),
                        "Unblock or schedule this task.",
                    )
                )

        leads = self._filter_workspace(self.storage.read_list("business_leads.json"), workspace_id)
        for lead in leads:
            status = lead.get("status")
            if status in {"won", "lost"}:
                continue
            score = 10
            reason = "Lead in pipeline."
            if status in {"qualified", "proposal_sent"}:
                score += 25
                reason = "Qualified lead — close to conversion."
            items.append(
                self._priority_item(
                    "lead",
                    lead.get("lead_id"),
                    lead.get("name") or lead.get("company") or "Lead",
                    score,
                    reason,
                    lead.get("next_step") or "Follow up with this lead.",
                )
            )

        cases = self._filter_workspace(self.storage.read_list("business_support_cases.json"), workspace_id)
        for case in cases:
            if case.get("status") == "resolved":
                continue
            score = 20
            reasons = ["Open support case."]
            if case.get("priority") == "high":
                score += 35
                reasons.append("High priority.")
            if case.get("status") == "escalated":
                score += 15
                reasons.append("Escalated.")
            items.append(
                self._priority_item(
                    "support_case",
                    case.get("case_id"),
                    case.get("subject") or "Support case",
                    score,
                    " ".join(reasons),
                    "Respond to or escalate this case.",
                )
            )

        risks = self._filter_workspace(self.storage.read_list("project_risks.json"), workspace_id)
        for risk in risks:
            if risk.get("status") == "resolved":
                continue
            score = 15 + SEVERITY_ORDER.get(risk.get("severity", "low"), 1) * 10
            items.append(
                self._priority_item(
                    "risk",
                    risk.get("risk_id"),
                    risk.get("title") or "Risk",
                    score,
                    f"{risk.get('severity', 'low').capitalize()} severity risk.",
                    risk.get("mitigation") or "Review and mitigate this risk.",
                )
            )

        approvals = self._filter_workspace(self.storage.read_list("approval_chains.json"), workspace_id)
        for approval in approvals:
            if approval.get("status") != "pending":
                continue
            items.append(
                self._priority_item(
                    "approval",
                    approval.get("approval_id"),
                    approval.get("summary") or approval.get("title") or "Pending approval",
                    40,
                    "Approval is waiting for a decision.",
                    "Review and approve or reject.",
                )
            )

        for followup in self._open_followups(workspace_id):
            score = 15 + SEVERITY_ORDER.get(followup.get("priority", "low"), 1) * 10
            days = self._days_until(followup.get("due_date"))
            reason = "Open follow-up."
            if days is not None and days <= 0:
                score += 25
                reason = "Follow-up due today or overdue."
            elif days is not None and days <= 2:
                score += 10
                reason = "Follow-up due soon."
            items.append(
                self._priority_item(
                    "followup",
                    followup.get("followup_id"),
                    followup.get("title") or "Follow-up",
                    score,
                    reason,
                    "Complete or snooze this follow-up.",
                )
            )

        # v180: real external signal (open PRs/issues on configured repos), not
        # workspace-scoped — a user's open GitHub work is relevant regardless of
        # which internal workspace they're currently focused on.
        items.extend(self._github_items())

        items.sort(key=lambda item: item["priority_score"], reverse=True)
        if log:
            self._log("chief_priorities_ranked", workspace_id, f"Ranked {len(items)} priority item(s).")
        return items

    @staticmethod
    def _priority_item(item_type: str, source_id, title: str, score: int, reason: str, action: str) -> dict:
        return {
            "item_id": f"{item_type}:{source_id}",
            "item_type": item_type,
            "title": title,
            "priority_score": score,
            "reason": reason,
            "recommended_action": action,
            "source_id": source_id,
        }

    # ------------------------------------------------------------------
    # Follow-ups
    # ------------------------------------------------------------------
    def list_followups(self, workspace_id: str | None = None) -> list[dict]:
        return self._filter_workspace(self.storage.read_list(self.followups_file), workspace_id)

    def _open_followups(self, workspace_id: str | None = None) -> list[dict]:
        return [item for item in self.list_followups(workspace_id) if item.get("status") in {"open", "snoozed"}]

    def overdue_followups(self, workspace_id: str | None = None) -> list[dict]:
        overdue = []
        for followup in self._open_followups(workspace_id):
            days = self._days_until(followup.get("due_date"))
            if days is not None and days < 0:
                overdue.append(followup)
        return overdue

    def followups_due_today(self, workspace_id: str | None = None) -> list[dict]:
        due = []
        for followup in self._open_followups(workspace_id):
            days = self._days_until(followup.get("due_date"))
            if days is not None and days <= 0:
                due.append(followup)
        return due

    def create_followup(self, data: dict) -> dict:
        followup = {
            "followup_id": str(uuid4()),
            "workspace_id": data.get("workspace_id"),
            "title": self._clean(data.get("title"), 200),
            "description": self._clean(data.get("description"), 2000),
            "source_type": self._enum(data.get("source_type"), FOLLOWUP_SOURCES, "manual"),
            "source_id": self._clean(data.get("source_id"), 120) or None,
            "due_date": self._clean(data.get("due_date"), 10) or None,
            "priority": self._enum(data.get("priority"), FOLLOWUP_PRIORITIES, "medium"),
            "status": self._enum(data.get("status"), FOLLOWUP_STATUSES, "open"),
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.followups_file, followup)
        self._log("chief_followup_created", followup["workspace_id"], f"Created follow-up: {followup['title'] or followup['followup_id']}.")
        return followup

    def update_followup(self, followup_id: str, updates: dict) -> dict:
        records = self.storage.read_list(self.followups_file)
        record = next((item for item in records if item.get("followup_id") == followup_id), None)
        if record is None:
            raise ValueError("Follow-up not found")
        if updates.get("title") is not None:
            record["title"] = self._clean(updates["title"], 200)
        if updates.get("description") is not None:
            record["description"] = self._clean(updates["description"], 2000)
        if updates.get("source_type") is not None:
            record["source_type"] = self._enum(updates["source_type"], FOLLOWUP_SOURCES, "manual")
        if updates.get("source_id") is not None:
            record["source_id"] = self._clean(updates["source_id"], 120) or None
        if updates.get("due_date") is not None:
            record["due_date"] = self._clean(updates["due_date"], 10) or None
        if updates.get("priority") is not None:
            record["priority"] = self._enum(updates["priority"], FOLLOWUP_PRIORITIES, "medium")
        if updates.get("status") is not None:
            record["status"] = self._enum(updates["status"], FOLLOWUP_STATUSES, "open")
        record["updated_at"] = self._now()
        self.storage.write_list(self.followups_file, records)
        self._log("chief_followup_updated", record.get("workspace_id"), f"Updated follow-up {followup_id}.")
        return record

    # ------------------------------------------------------------------
    # Blocked / risk views
    # ------------------------------------------------------------------
    def _blocked_items(self, workspace_id: str | None = None) -> list[dict]:
        blocked = []
        for goal in self._filter_workspace(self.storage.read_list("goals.json"), workspace_id):
            if goal.get("status") in {"archived", "completed"}:
                continue
            for task in self._tasks_for(goal.get("goal_id")):
                if task.get("status") == "blocked":
                    blocked.append({"type": "task", "title": task.get("title"), "goal": goal.get("title")})
        for case in self._filter_workspace(self.storage.read_list("business_support_cases.json"), workspace_id):
            if case.get("status") == "escalated":
                blocked.append({"type": "support_case", "title": case.get("subject"), "status": "escalated"})
        return blocked

    def _risk_summary(self, workspace_id: str | None = None) -> dict:
        risks = [r for r in self._filter_workspace(self.storage.read_list("project_risks.json"), workspace_id) if r.get("status") != "resolved"]
        counts = {"high": 0, "medium": 0, "low": 0}
        for risk in risks:
            severity = risk.get("severity", "low")
            if severity in counts:
                counts[severity] += 1
        return {"open_risk_count": len(risks), "severity_counts": counts}

    # ------------------------------------------------------------------
    # Daily plan
    # ------------------------------------------------------------------
    def generate_daily_plan(self, workspace_id: str | None = None) -> dict:
        priorities = self.rank_priorities(workspace_id)
        top = priorities[:5]
        due_today = self.followups_due_today(workspace_id)
        risks = [
            {"title": r.get("title"), "severity": r.get("severity")}
            for r in self._filter_workspace(self.storage.read_list("project_risks.json"), workspace_id)
            if r.get("status") != "resolved" and r.get("severity") in {"high", "medium"}
        ]
        schedule_blocks = []
        for index, item in enumerate(top):
            schedule_blocks.append(
                {
                    "block": ["Morning focus", "Late morning", "Early afternoon", "Afternoon", "End of day"][index],
                    "item_type": item["item_type"],
                    "title": item["title"],
                    "recommended_action": item["recommended_action"],
                }
            )
        plan = {
            "plan_id": str(uuid4()),
            "workspace_id": workspace_id,
            "date": self._today().isoformat(),
            "summary": (
                f"{len(top)} top priorities, {len(due_today)} follow-up(s) due, "
                f"{len(risks)} open risk(s) to watch."
            ),
            "top_priorities": top,
            "schedule_blocks": schedule_blocks,
            "followups_due": due_today,
            "risks": risks,
            "recommended_next_actions": [item["recommended_action"] for item in top],
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.daily_file, plan)
        self._log("chief_daily_plan_created", workspace_id, f"Generated daily plan for {plan['date']}.")
        return plan

    def list_daily_plans(self, workspace_id: str | None = None, limit: int = 20) -> list[dict]:
        return list(reversed(self._filter_workspace(self.storage.read_list(self.daily_file), workspace_id)[-limit:]))

    # ------------------------------------------------------------------
    # Weekly plan
    # ------------------------------------------------------------------
    def generate_weekly_plan(self, workspace_id: str | None = None) -> dict:
        today = self._today()
        week_start = today - timedelta(days=today.weekday())
        priorities = self.rank_priorities(workspace_id)
        goals = [g for g in self._filter_workspace(self.storage.read_list("goals.json"), workspace_id) if g.get("status") not in {"archived"}]
        milestones = [
            {"title": g.get("title"), "progress_percent": g.get("progress_percent", 0), "risk_level": g.get("risk_level", "low")}
            for g in goals
        ][:8]
        theme_counts: dict[str, int] = {}
        for item in priorities:
            theme_counts[item["item_type"]] = theme_counts.get(item["item_type"], 0) + 1
        priority_themes = [
            {"theme": theme, "count": count}
            for theme, count in sorted(theme_counts.items(), key=lambda kv: kv[1], reverse=True)
        ]
        blocked = self._blocked_items(workspace_id)
        plan = {
            "plan_id": str(uuid4()),
            "workspace_id": workspace_id,
            "week_start": week_start.isoformat(),
            "summary": (
                f"{len(milestones)} milestone(s), {len(priority_themes)} priority theme(s), "
                f"{len(blocked)} blocked item(s)."
            ),
            "milestones": milestones,
            "priority_themes": priority_themes,
            "blocked_items": blocked,
            "recommended_focus": [item["title"] for item in priorities[:5]],
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.weekly_file, plan)
        self._log("chief_weekly_plan_created", workspace_id, f"Generated weekly plan for week of {plan['week_start']}.")
        return plan

    def list_weekly_plans(self, workspace_id: str | None = None, limit: int = 20) -> list[dict]:
        return list(reversed(self._filter_workspace(self.storage.read_list(self.weekly_file), workspace_id)[-limit:]))

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard(self, workspace_id: str | None = None) -> dict:
        priorities = self.rank_priorities(workspace_id)
        latest_daily = self.list_daily_plans(workspace_id, limit=1)
        latest_weekly = self.list_weekly_plans(workspace_id, limit=1)
        open_followups = self._open_followups(workspace_id)
        overdue = self.overdue_followups(workspace_id)
        recommended = priorities[0]["recommended_action"] if priorities else "No outstanding priorities. Plan ahead or review goals."
        return {
            "today": self._today().isoformat(),
            "daily_plan": latest_daily[0] if latest_daily else None,
            "weekly_plan": latest_weekly[0] if latest_weekly else None,
            "priority_items": priorities[:10],
            "github_items_count": sum(1 for p in priorities if p["item_type"] in ("github_pr", "github_issue")),
            "open_followups": open_followups,
            "overdue_followups": overdue,
            "blocked_items": self._blocked_items(workspace_id),
            "risk_summary": self._risk_summary(workspace_id),
            "recommended_next_action": recommended,
        }

    def analytics_summary(self) -> dict:
        return {
            "chief_of_staff_daily_plans": len(self.storage.read_list(self.daily_file)),
            "chief_of_staff_weekly_plans": len(self.storage.read_list(self.weekly_file)),
            "chief_of_staff_open_followups": len(self._open_followups()),
            "chief_of_staff_github_repos_configured": len(self._github_repos()),
        }
