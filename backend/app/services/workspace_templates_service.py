from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


class WorkspaceTemplatesService:
    """v57.0 Workspace Templates & Cloning (local records only).

    Define reusable **workspace templates** (name, description, tags, and a
    preset of local settings) and **instantiate** them to spin up a new local
    workspace preconfigured from the template. This is local structure only — no
    production provisioning, no auth. Template creation and instantiation are
    governance-logged.
    """

    templates_file = "workspace_templates.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, workspace_service):
        self.storage = storage
        self.governance = governance_service
        self.workspaces = workspace_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _string_list(self, values, limit: int = 20, item_max: int = 60) -> list[str]:
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
                task_type="workspace_templates",
                agent_name="Workspace Templates",
                action_type=action_type,
                tool_used="WorkspaceTemplatesService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=3,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------
    def create_template(self, data: dict) -> dict:
        data = data or {}
        preset = data.get("preset") if isinstance(data.get("preset"), dict) else {}
        template = {
            "template_id": str(uuid4()),
            "name": self._clean(data.get("name"), 160) or "Workspace template",
            "description": self._clean(data.get("description"), 1000),
            "default_tags": self._string_list(data.get("default_tags")),
            "preset": {k: str(v)[:200] for k, v in list(preset.items())[:20]},
            "instantiation_count": 0,
            "created_at": self._now(),
        }
        self.storage.append(self.templates_file, template)
        self._log("workspace_template_created", f"Created workspace template '{template['name']}'.")
        return template

    def list_templates(self) -> list[dict]:
        return self.storage.read_list(self.templates_file)

    def get_template(self, template_id: str) -> dict | None:
        return next((t for t in self.list_templates() if t.get("template_id") == template_id), None)

    # ------------------------------------------------------------------
    # Instantiate (create a real local workspace from the template)
    # ------------------------------------------------------------------
    def instantiate(self, template_id: str, data: dict | None = None) -> dict:
        templates = self.list_templates()
        template = next((t for t in templates if t.get("template_id") == template_id), None)
        if template is None:
            raise ValueError("Template not found")
        data = data or {}
        name = self._clean(data.get("name"), 160) or f"{template['name']} workspace"
        workspace = self.workspaces.create_workspace({
            "name": name,
            "description": template.get("description", ""),
            "tags": template.get("default_tags", []),
        })
        template["instantiation_count"] = template.get("instantiation_count", 0) + 1
        self.storage.write_list(self.templates_file, templates)
        self._log("workspace_template_instantiated", f"Instantiated template {template_id} → workspace {workspace.get('workspace_id')}.")
        return {
            "template_id": template_id,
            "workspace_id": workspace.get("workspace_id"),
            "workspace_name": workspace.get("name"),
            "preset_applied": template.get("preset", {}),
            "note": "Created a local workspace from the template — local record only, no production provisioning.",
            "created_at": self._now(),
        }

    # ------------------------------------------------------------------
    # Summary + analytics
    # ------------------------------------------------------------------
    def summary(self) -> dict:
        templates = self.list_templates()
        return {
            "template_count": len(templates),
            "total_instantiations": sum(t.get("instantiation_count", 0) for t in templates),
            "note": "Local workspace templates and clones only — no production provisioning or auth.",
        }

    def analytics_summary(self) -> dict:
        templates = self.list_templates()
        return {
            "workspace_templates": len(templates),
            "workspace_template_instantiations": sum(t.get("instantiation_count", 0) for t in templates),
        }
