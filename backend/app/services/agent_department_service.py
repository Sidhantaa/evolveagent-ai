from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.permission_service import PermissionService
from app.services.storage_service import StorageService

# Permission levels mirror the plugin SDK / governance vocabulary.
PERMISSION_LEVELS = ["read_only", "plan_only", "approve_to_edit", "approve_to_run", "blocked"]

# Risk and approval are derived from the department permission level.
_RISK_BY_PERMISSION = {
    "read_only": "low",
    "plan_only": "low",
    "approve_to_edit": "medium",
    "approve_to_run": "high",
    "blocked": "high",
}
_APPROVAL_PERMISSIONS = {"approve_to_edit", "approve_to_run", "blocked"}

# Default AI "company" department templates. Tools stay declarative and safe:
# no real external sending, no unrestricted shell, no destructive operations.
DEFAULT_DEPARTMENTS = [
    {
        "name": "Engineering",
        "description": "Builds and reviews application changes through governed, approval-gated automation planning.",
        "manager_agent": "Engineering Manager Agent",
        "worker_agents": ["Coder Agent", "Bug Fix Agent", "Test Generation Agent"],
        "reviewer_agents": ["Code Review Agent"],
        "auditor_agents": ["Security Governance Layer"],
        "allowed_tools": ["knowledge_search", "build_run", "test_run"],
        "permission_level": "approve_to_run",
    },
    {
        "name": "Research",
        "description": "Gathers context, evaluates evidence, and produces governed research reports.",
        "manager_agent": "Research Manager Agent",
        "worker_agents": ["Research Agent", "Logic Agent"],
        "reviewer_agents": ["Judge Agent"],
        "auditor_agents": ["Compliance Auditor Agent"],
        "allowed_tools": ["knowledge_search", "research_search"],
        "permission_level": "read_only",
    },
    {
        "name": "Document",
        "description": "Analyzes uploaded documents and drafts written summaries and outputs.",
        "manager_agent": "Document Manager Agent",
        "worker_agents": ["File Analysis Agent", "Writing Agent"],
        "reviewer_agents": ["Judge Agent"],
        "auditor_agents": ["Security Governance Layer"],
        "allowed_tools": ["file_analysis", "knowledge_search"],
        "permission_level": "read_only",
    },
    {
        "name": "Pharmacy PA",
        "description": "Drafts prior-authorization support content for human review. Decision support only, not medical advice.",
        "manager_agent": "Pharmacy PA Manager Agent",
        "worker_agents": ["Pharmacy PA Agent"],
        "reviewer_agents": ["Judge Agent"],
        "auditor_agents": ["Compliance Auditor Agent"],
        "allowed_tools": ["knowledge_search"],
        "permission_level": "plan_only",
    },
    {
        "name": "Sales/Email",
        "description": "Drafts outreach and email copy. Drafts only — no real external sending.",
        "manager_agent": "Sales Manager Agent",
        "worker_agents": ["Writing Agent", "Strategy Agent"],
        "reviewer_agents": ["Judge Agent"],
        "auditor_agents": ["Compliance Auditor Agent"],
        "allowed_tools": ["knowledge_search"],
        "permission_level": "approve_to_edit",
    },
    {
        "name": "Finance/Cost",
        "description": "Estimates costs and analyzes financial trade-offs using safe local calculation tools.",
        "manager_agent": "Finance Manager Agent",
        "worker_agents": ["Logic Agent", "Strategy Agent"],
        "reviewer_agents": ["Judge Agent"],
        "auditor_agents": ["Compliance Auditor Agent"],
        "allowed_tools": ["calculate", "knowledge_search"],
        "permission_level": "read_only",
    },
    {
        "name": "Compliance",
        "description": "Reviews work for policy, safety, and governance alignment across departments.",
        "manager_agent": "Compliance Manager Agent",
        "worker_agents": ["Risk Agent"],
        "reviewer_agents": ["Judge Agent"],
        "auditor_agents": ["Security Governance Layer", "Compliance Auditor Agent"],
        "allowed_tools": ["knowledge_search"],
        "permission_level": "read_only",
    },
]


class AgentDepartmentService:
    """v16.0 Multi-Agent Organization layer.

    Models EvolveAgent as an AI company: departments with manager / worker /
    reviewer / auditor roles, governed department run plans, and cross-department
    collaboration plans. It plans and persists records only — it never executes
    unsafe tools, and every stateful action is logged through governance and
    constrained by the permission service.
    """

    departments_file = "agent_departments.json"
    runs_file = "department_runs.json"
    collaboration_file = "department_collaboration.json"

    def __init__(
        self,
        storage: StorageService,
        governance_service: GovernanceService,
        permission_service: PermissionService,
    ):
        self.storage = storage
        self.governance = governance_service
        self.permission = permission_service

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _normalize_permission(self, level: str | None) -> str:
        candidate = (level or "").strip().lower()
        return candidate if candidate in PERMISSION_LEVELS else "read_only"

    def _safe_tools(self, tools: list[str] | None) -> list[str]:
        """Keep only declarative tool names; drop anything that reads as an unsafe command/path."""
        cleaned: list[str] = []
        for tool in tools or []:
            name = str(tool).strip()
            if not name or len(name) > 80:
                continue
            if self.permission.is_unsafe_command(name) or self.permission.is_unsafe_path(name):
                continue
            if name not in cleaned:
                cleaned.append(name)
        return cleaned

    def _string_list(self, values: list[str] | None, limit: int = 20) -> list[str]:
        cleaned: list[str] = []
        for value in values or []:
            name = str(value).strip()
            if name and len(name) <= 120 and name not in cleaned:
                cleaned.append(name)
            if len(cleaned) >= limit:
                break
        return cleaned

    def _log(self, action_type: str, reason: str, permission_level: str = "read_only", risk_score: int = 5) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="agent_organization",
                agent_name="Agent Organization Layer",
                action_type=action_type,
                tool_used="AgentDepartmentService",
                permission_level=permission_level,
                approved=True,
                blocked=False,
                risk_score=risk_score,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Department CRUD
    # ------------------------------------------------------------------
    def list_departments(self, include_archived: bool = False) -> list[dict]:
        departments = self.storage.read_list(self.departments_file)
        if include_archived:
            return departments
        return [item for item in departments if item.get("active", True)]

    def get_department(self, department_id: str) -> dict | None:
        return next(
            (item for item in self.storage.read_list(self.departments_file) if item.get("department_id") == department_id),
            None,
        )

    def create_department(
        self,
        name: str,
        description: str = "",
        manager_agent: str | None = None,
        worker_agents: list[str] | None = None,
        reviewer_agents: list[str] | None = None,
        auditor_agents: list[str] | None = None,
        allowed_tools: list[str] | None = None,
        permission_level: str = "read_only",
    ) -> dict:
        now = self._now()
        department = {
            "department_id": str(uuid4()),
            "name": name.strip(),
            "description": (description or "").strip(),
            "manager_agent": (manager_agent or "Department Manager Agent").strip(),
            "worker_agents": self._string_list(worker_agents),
            "reviewer_agents": self._string_list(reviewer_agents),
            "auditor_agents": self._string_list(auditor_agents),
            "allowed_tools": self._safe_tools(allowed_tools),
            "permission_level": self._normalize_permission(permission_level),
            "active": True,
            "created_at": now,
            "updated_at": now,
        }
        self.storage.append(self.departments_file, department)
        self._log("department_created", f"Created department: {department['name']}.")
        return department

    def update_department(self, department_id: str, updates: dict) -> dict:
        departments = self.storage.read_list(self.departments_file)
        department = next((item for item in departments if item.get("department_id") == department_id), None)
        if department is None:
            raise ValueError("Department not found")
        if updates.get("name") is not None:
            department["name"] = str(updates["name"]).strip() or department["name"]
        if updates.get("description") is not None:
            department["description"] = str(updates["description"]).strip()
        if updates.get("manager_agent") is not None:
            department["manager_agent"] = str(updates["manager_agent"]).strip() or department["manager_agent"]
        for role in ("worker_agents", "reviewer_agents", "auditor_agents"):
            if updates.get(role) is not None:
                department[role] = self._string_list(updates[role])
        if updates.get("allowed_tools") is not None:
            department["allowed_tools"] = self._safe_tools(updates["allowed_tools"])
        if updates.get("permission_level") is not None:
            department["permission_level"] = self._normalize_permission(updates["permission_level"])
        if updates.get("active") is not None:
            department["active"] = bool(updates["active"])
        department["updated_at"] = self._now()
        self.storage.write_list(self.departments_file, departments)
        self._log("department_updated", f"Updated department {department_id}.")
        return department

    def archive_department(self, department_id: str) -> dict:
        departments = self.storage.read_list(self.departments_file)
        department = next((item for item in departments if item.get("department_id") == department_id), None)
        if department is None:
            raise ValueError("Department not found")
        department["active"] = False
        department["updated_at"] = self._now()
        self.storage.write_list(self.departments_file, departments)
        self._log("department_archived", f"Archived department {department_id}.")
        return department

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------
    def templates(self) -> list[dict]:
        return [dict(template) for template in DEFAULT_DEPARTMENTS]

    def seed_templates(self) -> dict:
        existing_names = {item.get("name", "").lower() for item in self.storage.read_list(self.departments_file)}
        created: list[dict] = []
        for template in DEFAULT_DEPARTMENTS:
            if template["name"].lower() in existing_names:
                continue
            created.append(
                self.create_department(
                    name=template["name"],
                    description=template["description"],
                    manager_agent=template["manager_agent"],
                    worker_agents=template["worker_agents"],
                    reviewer_agents=template["reviewer_agents"],
                    auditor_agents=template["auditor_agents"],
                    allowed_tools=template["allowed_tools"],
                    permission_level=template["permission_level"],
                )
            )
        self._log("department_templates_seeded", f"Seeded {len(created)} default department(s).")
        return {
            "seeded_count": len(created),
            "skipped_existing": len(DEFAULT_DEPARTMENTS) - len(created),
            "departments": created,
        }

    # ------------------------------------------------------------------
    # Department run plans
    # ------------------------------------------------------------------
    def _build_workflow_plan(self, department: dict, task: str) -> list[dict]:
        plan: list[dict] = []
        step = 1
        plan.append(
            {
                "step": step,
                "role": "manager",
                "agent": department.get("manager_agent"),
                "action": f"Scope and delegate: {task}",
            }
        )
        for worker in department.get("worker_agents", []):
            step += 1
            plan.append({"step": step, "role": "worker", "agent": worker, "action": "Execute assigned subtask (planning only)."})
        for reviewer in department.get("reviewer_agents", []):
            step += 1
            plan.append({"step": step, "role": "reviewer", "agent": reviewer, "action": "Review worker output for quality."})
        for auditor in department.get("auditor_agents", []):
            step += 1
            plan.append({"step": step, "role": "auditor", "agent": auditor, "action": "Audit for policy, safety, and governance."})
        return plan

    def plan_run(self, department_id: str, task: str) -> dict:
        department = self.get_department(department_id)
        if department is None:
            raise ValueError("Department not found")
        permission_level = self._normalize_permission(department.get("permission_level"))
        risk_level = _RISK_BY_PERMISSION.get(permission_level, "low")
        requires_approval = permission_level in _APPROVAL_PERMISSIONS
        status = "blocked" if permission_level == "blocked" else "planned"
        run = {
            "department_run_id": str(uuid4()),
            "department_id": department_id,
            "department_name": department.get("name"),
            "task": task.strip(),
            "manager_agent": department.get("manager_agent"),
            "worker_agents": department.get("worker_agents", []),
            "reviewer_agents": department.get("reviewer_agents", []),
            "auditor_agents": department.get("auditor_agents", []),
            "allowed_tools": department.get("allowed_tools", []),
            "permission_level": permission_level,
            "workflow_plan": self._build_workflow_plan(department, task),
            "requires_approval": requires_approval,
            "risk_level": risk_level,
            "status": status,
            "created_at": self._now(),
        }
        self.storage.append(self.runs_file, run)
        self._log(
            "department_run_planned",
            f"Planned run for department {department.get('name')}: {task[:80]}",
            permission_level=permission_level,
            risk_score=70 if risk_level == "high" else 35 if risk_level == "medium" else 5,
        )
        return run

    def list_runs(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.runs_file)[-limit:]))

    # ------------------------------------------------------------------
    # Cross-department collaboration plans
    # ------------------------------------------------------------------
    def plan_collaboration(
        self,
        goal: str,
        departments: list[str] | None = None,
        lead_department: str | None = None,
    ) -> dict:
        known = self.storage.read_list(self.departments_file)
        by_id = {item.get("department_id"): item for item in known}
        by_name = {item.get("name", "").lower(): item for item in known}

        resolved: list[dict] = []
        for ref in departments or []:
            match = by_id.get(ref) or by_name.get(str(ref).strip().lower())
            if match and match not in resolved:
                resolved.append(match)

        lead = None
        if lead_department:
            lead = by_id.get(lead_department) or by_name.get(str(lead_department).strip().lower())
        if lead is None and resolved:
            lead = resolved[0]

        ordered = resolved if resolved else ([lead] if lead else [])
        handoffs = []
        for index in range(len(ordered) - 1):
            handoffs.append(
                {
                    "from_department": ordered[index].get("name"),
                    "to_department": ordered[index + 1].get("name"),
                    "artifact": "Reviewed work package",
                }
            )
        review_steps = [
            {"department": dept.get("name"), "reviewer_agents": dept.get("reviewer_agents", [])}
            for dept in ordered
        ]
        approval_points = [
            {"department": dept.get("name"), "permission_level": dept.get("permission_level")}
            for dept in ordered
            if self._normalize_permission(dept.get("permission_level")) in _APPROVAL_PERMISSIONS
        ]
        collaboration = {
            "collaboration_id": str(uuid4()),
            "goal": goal.strip(),
            "departments": [dept.get("name") for dept in ordered],
            "department_ids": [dept.get("department_id") for dept in ordered],
            "lead_department": lead.get("name") if lead else None,
            "handoffs": handoffs,
            "review_steps": review_steps,
            "approval_points": approval_points,
            "status": "planned",
            "created_at": self._now(),
        }
        self.storage.append(self.collaboration_file, collaboration)
        self._log("department_collaboration_planned", f"Planned cross-department collaboration: {goal[:80]}")
        return collaboration

    def list_collaborations(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.collaboration_file)[-limit:]))

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------
    def analytics_summary(self) -> dict:
        departments = self.storage.read_list(self.departments_file)
        active = [item for item in departments if item.get("active", True)]
        return {
            "total_departments": len(departments),
            "active_departments": len(active),
            "department_runs": len(self.storage.read_list(self.runs_file)),
            "collaboration_count": len(self.storage.read_list(self.collaboration_file)),
        }

    def overview(self) -> dict:
        """Combined snapshot for the Developer Mode Agent Organization panel."""
        departments = self.list_departments(include_archived=True)
        permission_counts = Counter(item.get("permission_level", "read_only") for item in departments)
        summary = self.analytics_summary()
        return {
            "departments": departments,
            "recent_runs": self.list_runs(limit=10),
            "recent_collaborations": self.list_collaborations(limit=10),
            "permission_levels": PERMISSION_LEVELS,
            "permission_level_counts": dict(permission_counts),
            **summary,
        }
