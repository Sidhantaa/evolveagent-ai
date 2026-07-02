from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

CATEGORIES = ["development", "productivity", "knowledge", "browser", "desktop", "custom"]
STATUSES = ["not_configured", "configured", "available", "unavailable", "disabled", "error"]
MODES = ["read_only", "approval_required", "disabled"]
RISK_LEVELS = ["low", "medium", "high"]
SERVER_TYPES = ["stdio", "http", "local_mock", "external"]
WORKSPACE_SCOPES = ["global", "workspace"]


# ----------------------------------------------------------------------
# Default connector templates (Part 3). These describe planned, governed
# connections — none of them execute real MCP servers in this version.
# ----------------------------------------------------------------------
DEFAULT_TEMPLATES: list[dict] = [
    {
        "slug": "filesystem",
        "name": "Filesystem MCP",
        "description": "Plan governed read/propose access to approved project files through MCP.",
        "category": "development",
        "risk_level": "high",
        "mode": "approval_required",
        "server_type": "local_mock",
        "env_keys_required": [],
        "capabilities": ["read approved project files", "list approved project directories", "propose file edits", "list directory (read-only)", "file metadata (read-only)"],
        "allowed_actions": ["read_approved_file", "list_approved_directory", "propose_file_edit", "fs_list_directory", "fs_file_metadata"],
        "blocked_actions": ["read .env", "read home directory", "delete files", "unrestricted write"],
        "enabled": False,
    },
    {
        "slug": "git",
        "name": "Git MCP",
        "description": "Plan governed local git inspection and approval-gated commits through MCP.",
        "category": "development",
        "risk_level": "medium",
        "mode": "approval_required",
        "server_type": "local_mock",
        "env_keys_required": [],
        "capabilities": ["git status", "git diff", "branch info", "commit with approval", "current branch (read-only)", "list branches (read-only)"],
        "allowed_actions": ["git_status", "git_diff", "branch_info", "commit_with_approval", "git_current_branch", "git_list_branches"],
        "blocked_actions": ["force push", "delete branches", "reset hard", "arbitrary shell"],
        "enabled": False,
    },
    {
        "slug": "github",
        "name": "GitHub MCP",
        "description": "Plan governed access to GitHub repositories, issues, and pull requests through MCP.",
        "category": "development",
        "risk_level": "medium",
        "mode": "approval_required",
        "server_type": "external",
        "env_keys_required": ["GITHUB_TOKEN"],
        "capabilities": ["read repo metadata", "list issues", "list pull requests", "draft PR comments"],
        "allowed_actions": ["read_repo_metadata", "list_issues", "list_pull_requests", "draft_pr_comment"],
        "blocked_actions": ["merge PR without approval", "delete repo", "expose token"],
        "enabled": False,
    },
    {
        "slug": "linear",
        "name": "Linear MCP",
        "description": "Plan governed access to Linear issues and status updates through MCP.",
        "category": "productivity",
        "risk_level": "medium",
        "mode": "approval_required",
        "server_type": "external",
        "env_keys_required": ["LINEAR_API_KEY"],
        "capabilities": ["list issues", "sync issue", "draft comments", "update status with approval"],
        "allowed_actions": ["list_issues", "sync_issue", "draft_comment", "update_status_with_approval"],
        "blocked_actions": ["close/delete without approval", "expose token"],
        "enabled": False,
    },
    {
        "slug": "context7",
        "name": "Context7 MCP",
        "description": "Plan read-only access to current library documentation for coding context through MCP.",
        "category": "knowledge",
        "risk_level": "low",
        "mode": "read_only",
        "server_type": "external",
        "env_keys_required": [],
        "capabilities": ["fetch current library docs", "provide coding documentation context"],
        "allowed_actions": ["fetch_library_docs", "provide_doc_context"],
        "blocked_actions": ["execute code", "modify files"],
        "enabled": False,
    },
    {
        "slug": "playwright",
        "name": "Playwright MCP",
        "description": "Plan governed local frontend inspection and UI checks through MCP.",
        "category": "browser",
        "risk_level": "high",
        "mode": "approval_required",
        "server_type": "local_mock",
        "env_keys_required": [],
        "capabilities": ["inspect local frontend", "run UI checks", "capture screenshots"],
        "allowed_actions": ["inspect_local_frontend", "run_ui_check", "capture_screenshot"],
        "blocked_actions": ["browse arbitrary websites", "submit forms", "use credentials", "make purchases"],
        "enabled": False,
    },
    {
        "slug": "slack",
        "name": "Slack MCP",
        "description": "Plan governed drafting and approval-gated posting of Slack updates through MCP.",
        "category": "productivity",
        "risk_level": "high",
        "mode": "approval_required",
        "server_type": "external",
        "env_keys_required": ["SLACK_BOT_TOKEN"],
        "capabilities": ["draft messages", "post approved updates"],
        "allowed_actions": ["draft_message", "post_approved_update"],
        "blocked_actions": ["post without approval", "expose token", "read private channels unless configured"],
        "enabled": False,
    },
    {
        "slug": "notion",
        "name": "Notion MCP",
        "description": "Plan governed report export and approval-gated page creation through MCP.",
        "category": "knowledge",
        "risk_level": "medium",
        "mode": "approval_required",
        "server_type": "external",
        "env_keys_required": ["NOTION_API_KEY"],
        "capabilities": ["export approved reports", "create pages with approval"],
        "allowed_actions": ["export_approved_report", "create_page_with_approval"],
        "blocked_actions": ["overwrite pages without approval", "expose token"],
        "enabled": False,
    },
    {
        "slug": "desktop-commander",
        "name": "Desktop Commander MCP",
        "description": "Plan governed desktop actions for approved project tools through MCP. Disabled by default.",
        "category": "desktop",
        "risk_level": "high",
        "mode": "disabled",
        "server_type": "local_mock",
        "env_keys_required": [],
        "capabilities": ["plan desktop actions", "open approved project tools"],
        "allowed_actions": ["plan_desktop_action", "open_approved_project_tool"],
        "blocked_actions": [
            "unrestricted PC control",
            "banking/payment apps",
            "password managers",
            "personal folders",
            "arbitrary terminal",
        ],
        "enabled": False,
    },
]


class MCPConnectorService:
    """v41.0 MCP Connector Hub.

    Registers, configures, inspects, and safely *plans* tool connections through
    MCP-style connector records. This version is **planning-first**: it does NOT
    run real MCP servers, make external/paid calls, run shell, control the
    desktop, or expose secrets. Status checks are dry/mock and only report whether
    required env keys are set (true/false) — never their values. Every stateful
    action is governance-logged and recorded as a connector event.
    """

    connectors_file = "mcp_connectors.json"
    events_file = "mcp_connector_events.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, policy_service=None):
        self.storage = storage
        self.governance = governance_service
        # v45: optional tighten-only policy engine, evaluated before planning checks.
        # When None (default), behaviour is unchanged.
        self.policy_service = policy_service

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

    def _string_list(self, values, limit: int = 40, item_max: int = 200) -> list[str]:
        cleaned: list[str] = []
        for value in values or []:
            text = str(value).strip()[:item_max]
            if text and text not in cleaned:
                cleaned.append(text)
            if len(cleaned) >= limit:
                break
        return cleaned

    def _risk_score(self, risk_level: str) -> int:
        return {"low": 3, "medium": 6, "high": 9}.get(risk_level, 5)

    def _log_governance(self, action_type: str, reason: str, risk_level: str, blocked: bool, approved: bool) -> str:
        event = self.governance.log_event(
            GovernanceEvent(
                task_type="mcp_connector_management",
                agent_name="MCP Connector Hub",
                action_type=action_type,
                tool_used="MCPConnectorService",
                permission_level="read_only",
                approved=approved,
                blocked=blocked,
                risk_score=self._risk_score(risk_level),
                reason=reason,
            )
        )
        # GovernanceEvent.created_at is set by the logger; fall back to a fresh id-like marker.
        return getattr(event, "created_at", None) or self._now()

    def _record_event(self, connector_id: str, event_type: str, message: str, risk_level: str = "low", metadata: dict | None = None) -> dict:
        event = {
            "event_id": str(uuid4()),
            "connector_id": connector_id,
            "event_type": event_type,
            "message": message,
            "risk_level": self._enum(risk_level, RISK_LEVELS, "low"),
            "created_at": self._now(),
            "metadata": metadata or {},
        }
        self.storage.append(self.events_file, event)
        return event

    def _sanitize_connector(self, connector: dict) -> dict:
        """Return a connector record safe for API/UI/logs.

        Only the *names* of required env keys are exposed, plus a boolean of
        whether each is set in the environment — never the value, and never a
        `command`/`env` payload that could leak a secret.
        """
        safe = dict(connector)
        safe.pop("env", None)  # never expose any env value map
        env_keys = connector.get("env_keys_required", []) or []
        safe["env_keys_required"] = list(env_keys)
        safe["env_keys_status"] = {key: self._env_key_set(key) for key in env_keys}
        return safe

    @staticmethod
    def _env_key_set(key: str) -> bool:
        value = os.environ.get(key)
        return bool(value and value.strip())

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------
    def get_default_mcp_templates(self) -> list[dict]:
        return [dict(template) for template in DEFAULT_TEMPLATES]

    def _template_for_slug(self, slug: str) -> dict | None:
        return next((dict(t) for t in DEFAULT_TEMPLATES if t["slug"] == slug), None)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def list_connectors(self) -> list[dict]:
        return [self._sanitize_connector(c) for c in self.storage.read_list(self.connectors_file)]

    def _raw_connectors(self) -> list[dict]:
        return self.storage.read_list(self.connectors_file)

    def get_connector(self, connector_id: str) -> dict | None:
        connector = next((c for c in self._raw_connectors() if c.get("connector_id") == connector_id), None)
        return self._sanitize_connector(connector) if connector else None

    def create_connector(self, payload: dict) -> dict:
        payload = payload or {}
        template = self._template_for_slug(self._clean(payload.get("slug"), 60).lower()) if payload.get("slug") else None
        base = template or {}
        risk_level = self._enum(payload.get("risk_level", base.get("risk_level")), RISK_LEVELS, "medium")
        # Desktop / high-risk connectors are never auto-enabled at creation.
        requested_enabled = bool(payload.get("enabled", base.get("enabled", False)))
        mode = self._enum(payload.get("mode", base.get("mode")), MODES, "approval_required")
        enabled = requested_enabled and mode != "disabled" and risk_level != "high"
        connector = {
            "connector_id": str(uuid4()),
            "name": self._clean(payload.get("name", base.get("name")), 120) or "MCP Connector",
            "slug": self._clean(payload.get("slug", base.get("slug")), 60).lower() or "custom",
            "description": self._clean(payload.get("description", base.get("description")), 600),
            "category": self._enum(payload.get("category", base.get("category")), CATEGORIES, "custom"),
            "status": "configured" if requested_enabled else "not_configured",
            "enabled": enabled,
            "mode": mode,
            "risk_level": risk_level,
            "server_type": self._enum(payload.get("server_type", base.get("server_type")), SERVER_TYPES, "local_mock"),
            "command": None,  # never store/echo a runnable command in this version
            "args": self._string_list(payload.get("args", base.get("args", []))),
            "env_keys_required": self._string_list(payload.get("env_keys_required", base.get("env_keys_required", [])), limit=20, item_max=80),
            "capabilities": self._string_list(payload.get("capabilities", base.get("capabilities", []))),
            "allowed_actions": self._string_list(payload.get("allowed_actions", base.get("allowed_actions", []))),
            "blocked_actions": self._string_list(payload.get("blocked_actions", base.get("blocked_actions", []))),
            "workspace_scope": self._enum(payload.get("workspace_scope"), WORKSPACE_SCOPES, "global"),
            "created_at": self._now(),
            "updated_at": self._now(),
            "last_checked_at": None,
            "last_error": None,
        }
        self.storage.append(self.connectors_file, connector)
        self._record_event(connector["connector_id"], "created", f"Connector '{connector['name']}' created.", risk_level)
        self._log_governance("mcp_connector_created", f"Created MCP connector {connector['slug']} ({risk_level} risk).", risk_level, blocked=False, approved=True)
        return self._sanitize_connector(connector)

    def update_connector(self, connector_id: str, payload: dict) -> dict:
        connectors = self._raw_connectors()
        connector = next((c for c in connectors if c.get("connector_id") == connector_id), None)
        if connector is None:
            raise ValueError("Connector not found")
        payload = payload or {}
        if payload.get("name") is not None:
            connector["name"] = self._clean(payload["name"], 120) or connector["name"]
        if payload.get("description") is not None:
            connector["description"] = self._clean(payload["description"], 600)
        if payload.get("category") is not None:
            connector["category"] = self._enum(payload["category"], CATEGORIES, connector["category"])
        if payload.get("mode") is not None:
            connector["mode"] = self._enum(payload["mode"], MODES, connector["mode"])
        if payload.get("risk_level") is not None:
            connector["risk_level"] = self._enum(payload["risk_level"], RISK_LEVELS, connector["risk_level"])
        if payload.get("server_type") is not None:
            connector["server_type"] = self._enum(payload["server_type"], SERVER_TYPES, connector["server_type"])
        if payload.get("workspace_scope") is not None:
            connector["workspace_scope"] = self._enum(payload["workspace_scope"], WORKSPACE_SCOPES, connector["workspace_scope"])
        for list_field in ("args", "capabilities", "allowed_actions", "blocked_actions"):
            if payload.get(list_field) is not None:
                connector[list_field] = self._string_list(payload[list_field])
        if payload.get("env_keys_required") is not None:
            connector["env_keys_required"] = self._string_list(payload["env_keys_required"], limit=20, item_max=80)
        # Disabling via mode forces enabled False; high-risk can never be enabled by update.
        if connector["mode"] == "disabled" or connector["risk_level"] == "high":
            connector["enabled"] = False
        connector["updated_at"] = self._now()
        self.storage.write_list(self.connectors_file, connectors)
        self._record_event(connector_id, "updated", f"Connector '{connector['name']}' updated.", connector["risk_level"])
        self._log_governance("mcp_connector_updated", f"Updated MCP connector {connector_id}.", connector["risk_level"], blocked=False, approved=True)
        return self._sanitize_connector(connector)

    # ------------------------------------------------------------------
    # Enable / disable
    # ------------------------------------------------------------------
    def enable_connector(self, connector_id: str) -> dict:
        connectors = self._raw_connectors()
        connector = next((c for c in connectors if c.get("connector_id") == connector_id), None)
        if connector is None:
            raise ValueError("Connector not found")
        if connector.get("mode") == "disabled":
            self._record_event(connector_id, "action_blocked", "Cannot enable a connector whose mode is 'disabled'.", connector.get("risk_level", "high"))
            self._log_governance("mcp_connector_action_blocked", f"Blocked enable of disabled-mode connector {connector_id}.", connector.get("risk_level", "high"), blocked=True, approved=False)
            raise ValueError("Connector mode is 'disabled' and cannot be enabled")
        if connector.get("risk_level") == "high":
            # High-risk connectors require explicit human approval — enabling is recorded but the
            # connector stays in approval_required posture and is not auto-activated for actions.
            connector["enabled"] = True
            connector["mode"] = "approval_required"
            connector["status"] = "configured"
            connector["updated_at"] = self._now()
            self.storage.write_list(self.connectors_file, connectors)
            self._record_event(connector_id, "enabled", "High-risk connector enabled in approval-required mode.", "high")
            self._log_governance("mcp_connector_enabled", f"Enabled high-risk MCP connector {connector_id} (approval-required).", "high", blocked=False, approved=True)
            return self._sanitize_connector(connector)
        connector["enabled"] = True
        connector["status"] = "configured"
        connector["updated_at"] = self._now()
        self.storage.write_list(self.connectors_file, connectors)
        self._record_event(connector_id, "enabled", f"Connector '{connector['name']}' enabled.", connector.get("risk_level", "low"))
        self._log_governance("mcp_connector_enabled", f"Enabled MCP connector {connector_id}.", connector.get("risk_level", "low"), blocked=False, approved=True)
        return self._sanitize_connector(connector)

    def disable_connector(self, connector_id: str) -> dict:
        connectors = self._raw_connectors()
        connector = next((c for c in connectors if c.get("connector_id") == connector_id), None)
        if connector is None:
            raise ValueError("Connector not found")
        connector["enabled"] = False
        connector["status"] = "disabled"
        connector["updated_at"] = self._now()
        self.storage.write_list(self.connectors_file, connectors)
        self._record_event(connector_id, "disabled", f"Connector '{connector['name']}' disabled.", connector.get("risk_level", "low"))
        self._log_governance("mcp_connector_disabled", f"Disabled MCP connector {connector_id}.", connector.get("risk_level", "low"), blocked=False, approved=True)
        return self._sanitize_connector(connector)

    # ------------------------------------------------------------------
    # Status check (dry / mock by default)
    # ------------------------------------------------------------------
    def check_connector_status(self, connector_id: str) -> dict:
        connectors = self._raw_connectors()
        connector = next((c for c in connectors if c.get("connector_id") == connector_id), None)
        if connector is None:
            raise ValueError("Connector not found")
        env_keys = connector.get("env_keys_required", []) or []
        env_status = {key: self._env_key_set(key) for key in env_keys}
        all_keys_set = all(env_status.values()) if env_keys else True
        if connector.get("mode") == "disabled":
            status = "disabled"
        elif not all_keys_set:
            status = "not_configured"
        else:
            # Dry check only — we never open a real connection in this version.
            status = "available" if connector.get("enabled") else "configured"
        connector["status"] = status
        connector["last_checked_at"] = self._now()
        connector["last_error"] = None
        connector["updated_at"] = self._now()
        self.storage.write_list(self.connectors_file, connectors)
        self._record_event(connector_id, "status_checked", f"Dry status check → {status}.", connector.get("risk_level", "low"), {"check_type": "dry"})
        self._log_governance("mcp_connector_status_checked", f"Dry status check for {connector_id} → {status}.", connector.get("risk_level", "low"), blocked=False, approved=True)
        return {
            "connector_id": connector_id,
            "status": status,
            "check_type": "dry",
            "env_keys_status": env_status,  # booleans only — never values
            "all_required_keys_set": all_keys_set,
            "last_checked_at": connector["last_checked_at"],
            "note": "Dry/mock status check — no real MCP connection or external call was made.",
        }

    # ------------------------------------------------------------------
    # Action planning (Part 4) — enforces risk/approval rules
    # ------------------------------------------------------------------
    def plan_connector_action(self, connector_id: str, action_name: str, payload: dict | None = None, workspace_id: str | None = None) -> dict:
        connectors = self._raw_connectors()
        connector = next((c for c in connectors if c.get("connector_id") == connector_id), None)
        if connector is None:
            raise ValueError("Connector not found")
        action = self._clean(action_name, 80)
        risk_level = connector.get("risk_level", "medium")
        blocked_actions = [a.lower() for a in connector.get("blocked_actions", [])]
        allowed_actions = connector.get("allowed_actions", [])

        # 0) v45 tighten-only policy engine — deny before any other check. Policies can
        #    only add blocks; when none match (or no engine is wired), planning is unchanged.
        if self.policy_service is not None:
            decision = self.policy_service.evaluate_and_log(connector, action)
            if not decision.get("allowed", True):
                return self._blocked_plan(connector_id, action, risk_level, decision.get("reason", "Blocked by policy."))

        # 1) Disabled-mode connectors plan nothing.
        if connector.get("mode") == "disabled":
            return self._blocked_plan(connector_id, action, risk_level, "Connector mode is 'disabled'; no actions can be planned.")

        # 2) Explicitly blocked actions (substring match against the block list).
        if any(action.lower() == b or action.lower() in b or b in action.lower() for b in blocked_actions):
            return self._blocked_plan(connector_id, action, risk_level, f"Action '{action}' is on the connector's blocked list.")

        # 3) If the connector declares an allow-list, the action must be on it.
        if allowed_actions and action not in allowed_actions:
            return self._blocked_plan(connector_id, action, risk_level, f"Action '{action}' is not in the connector's allowed actions.")

        # Determine approval requirement: read_only low-risk actions are auto-allowed;
        # everything else requires approval and is never auto-executed.
        read_only = connector.get("mode") == "read_only"
        requires_approval = not (read_only and risk_level == "low")

        plan_steps = [
            f"Validate connector '{connector.get('name')}' is enabled and configured.",
            f"Confirm action '{action}' is within allowed capabilities.",
            "Run a dry/mock check (no real external call in this version).",
        ]
        if requires_approval:
            plan_steps.append("Pause for explicit human approval before any real execution.")
        else:
            plan_steps.append("Return read-only result (planning/mock only — no write performed).")

        event_type = "approval_required" if requires_approval else "action_planned"
        gov_id = self._log_governance(
            "mcp_connector_action_planned" if not requires_approval else "mcp_connector_action_requires_approval",
            f"Planned MCP action '{action}' on {connector_id} (approval={'yes' if requires_approval else 'no'}).",
            risk_level,
            blocked=False,
            approved=not requires_approval,
        )
        self._record_event(connector_id, event_type, f"Planned action '{action}'.", risk_level, {"requires_approval": requires_approval})
        return {
            "planned": True,
            "connector_id": connector_id,
            "action_name": action,
            "requires_approval": requires_approval,
            "risk_level": risk_level,
            "allowed": True,
            "blocked_reason": None,
            "plan": plan_steps,
            "governance_event_id": gov_id,
        }

    def _blocked_plan(self, connector_id: str, action: str, risk_level: str, reason: str) -> dict:
        self._record_event(connector_id, "action_blocked", reason, risk_level, {"action_name": action})
        self._log_governance("mcp_connector_action_blocked", f"Blocked MCP action '{action}' on {connector_id}: {reason}", risk_level, blocked=True, approved=False)
        return {
            "planned": False,
            "connector_id": connector_id,
            "action_name": action,
            "allowed": False,
            "blocked_reason": reason,
            "risk_level": risk_level,
        }

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def list_connector_events(self, connector_id: str | None = None, limit: int = 100) -> list[dict]:
        events = self.storage.read_list(self.events_file)
        if connector_id:
            events = [e for e in events if e.get("connector_id") == connector_id]
        return list(reversed(events[-limit:]))

    # ------------------------------------------------------------------
    # Summary (Part 4) + analytics (Part 8)
    # ------------------------------------------------------------------
    def summarize_mcp_hub(self) -> dict:
        connectors = self._raw_connectors()
        desktop_enabled = any(c.get("category") == "desktop" and c.get("enabled") for c in connectors)
        return {
            "total_connectors": len(connectors),
            "enabled_connectors": sum(1 for c in connectors if c.get("enabled")),
            "available_connectors": sum(1 for c in connectors if c.get("status") == "available"),
            "high_risk_connectors": sum(1 for c in connectors if c.get("risk_level") == "high"),
            "approval_required_connectors": sum(1 for c in connectors if c.get("mode") == "approval_required"),
            "read_only_connectors": sum(1 for c in connectors if c.get("mode") == "read_only"),
            "recent_events": self.list_connector_events(limit=10),
            "safety_summary": {
                "secrets_exposed": False,
                "unrestricted_shell_allowed": False,
                "desktop_control_enabled": desktop_enabled,
                "external_send_requires_approval": True,
            },
        }

    def analytics_summary(self) -> dict:
        connectors = self._raw_connectors()
        events = self.storage.read_list(self.events_file)
        planned = sum(1 for e in events if e.get("event_type") in ("action_planned", "approval_required"))
        blocked = sum(1 for e in events if e.get("event_type") == "action_blocked")
        # Most-used connector by event volume.
        usage: dict[str, int] = {}
        id_to_name = {c.get("connector_id"): c.get("name") for c in connectors}
        for e in events:
            cid = e.get("connector_id")
            if cid:
                usage[cid] = usage.get(cid, 0) + 1
        most_used_id = max(usage, key=usage.get) if usage else None
        return {
            "mcp_total_connectors": len(connectors),
            "mcp_enabled_connectors": sum(1 for c in connectors if c.get("enabled")),
            "mcp_actions_planned": planned,
            "mcp_actions_blocked": blocked,
            "mcp_high_risk_connectors": sum(1 for c in connectors if c.get("risk_level") == "high"),
            "mcp_most_used_connector": id_to_name.get(most_used_id) if most_used_id else None,
        }

    def learning_recommendations(self) -> dict:
        """Lightweight learning hooks (Part 8): recommended connectors + recurring blocks."""
        connectors = self._raw_connectors()
        events = self.storage.read_list(self.events_file)
        existing_slugs = {c.get("slug") for c in connectors}
        recommended = [
            {"slug": t["slug"], "name": t["name"], "risk_level": t["risk_level"], "mode": t["mode"]}
            for t in DEFAULT_TEMPLATES
            if t["slug"] not in existing_slugs
        ][:5]
        blocked_counts: dict[str, int] = {}
        for e in events:
            if e.get("event_type") == "action_blocked":
                action = (e.get("metadata") or {}).get("action_name") or e.get("message", "")
                blocked_counts[action] = blocked_counts.get(action, 0) + 1
        recurring_blocked = sorted(blocked_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
        return {
            "recommended_mcp_connectors": recommended,
            "recurring_blocked_actions": [{"action": a, "count": n} for a, n in recurring_blocked],
            "connector_safety_recommendations": [
                "Keep high-risk connectors (Filesystem, Playwright, Desktop Commander) in approval-required or disabled mode.",
                "Only enable connectors whose required env keys are set; status checks report readiness without exposing values.",
                "Review blocked-action events to refine allowed/blocked lists per connector.",
            ],
        }
