from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.agents.prompt_injection_firewall_agent import PromptInjectionFirewallAgent
from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.secret_scanner import SecretScanner
from app.services.storage_service import StorageService


class AppBuilderService:
    filename = "app_builder_projects.json"

    templates = [
        {
            "stack_id": "fastapi-react",
            "name": "FastAPI + React",
            "description": "Full-stack app with FastAPI API routes and a Vite React frontend.",
            "files": ["backend/app/main.py", "backend/app/api/routes.py", "frontend/src/App.jsx", "frontend/package.json"],
            "preview_commands": ["pytest", "npm run build"],
            "best_for": ["dashboards", "AI workspaces", "CRUD apps", "portfolio demos"],
        },
        {
            "stack_id": "nextjs",
            "name": "Next.js App",
            "description": "React-first app structure for server-rendered or static product experiences.",
            "files": ["package.json", "app/page.jsx", "app/layout.jsx", "README.md"],
            "preview_commands": ["npm run build"],
            "best_for": ["landing pages", "SaaS UI", "content apps"],
        },
        {
            "stack_id": "python-cli",
            "name": "Python CLI",
            "description": "Small command-line tool with a main module, README, and tests.",
            "files": ["src/main.py", "tests/test_main.py", "README.md"],
            "preview_commands": ["pytest"],
            "best_for": ["automation scripts", "data utilities", "developer tools"],
        },
    ]

    def __init__(
        self,
        storage: StorageService,
        governance_service: GovernanceService,
        project_root: str | Path | None = None,
        secret_scanner: SecretScanner | None = None,
        firewall: PromptInjectionFirewallAgent | None = None,
    ):
        self.storage = storage
        self.governance_service = governance_service
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parents[3]
        self.output_root = self.project_root / "backend" / ".logs" / "app_builder"
        self.secret_scanner = secret_scanner or SecretScanner()
        self.firewall = firewall or PromptInjectionFirewallAgent()

    def list_templates(self) -> list[dict]:
        return self.templates

    def get_template(self, stack_id: str) -> dict:
        return next((template for template in self.templates if template["stack_id"] == stack_id), self.templates[0])

    def create_plan(self, prompt: str, stack_id: str = "fastapi-react", workspace_id: str | None = None) -> dict:
        redacted_prompt, secret_scan = self.secret_scanner.redact(prompt)
        injection = self.firewall.scan(redacted_prompt)
        if secret_scan.secrets_detected or not injection.safe_to_use_context:
            plan = self._blocked_plan(redacted_prompt, stack_id, workspace_id, secret_scan.model_dump(), injection.model_dump())
            self._save_plan(plan)
            self._log("app_builder_plan_blocked", plan, blocked=True, risk_score=max(80, injection.risk_score))
            return plan

        template = self.get_template(stack_id)
        app_name = self._app_name(redacted_prompt)
        features = self._features(redacted_prompt)
        files = self._planned_files(template["stack_id"], app_name)
        plan = {
            "plan_id": str(uuid4()),
            "workspace_id": workspace_id,
            "app_name": app_name,
            "prompt": redacted_prompt,
            "stack": template,
            "features": features,
            "files_to_create": files,
            "wizard_steps": self._wizard_steps(template["stack_id"], features),
            "preview_stub": {
                "type": "local_preview",
                "commands": template["preview_commands"],
                "note": "Preview commands are suggestions. They are not run automatically by App Builder.",
            },
            "risk_level": "medium" if len(files) > 5 else "low",
            "requires_approval": True,
            "status": "planned",
            "governance": {
                "secret_scan": secret_scan.model_dump(),
                "prompt_injection": injection.model_dump(),
                "safe_to_scaffold": True,
                "notes": [
                    "Scaffold output is written only to backend/.logs/app_builder after explicit approval.",
                    "No .env files, secrets, package installs, or destructive operations are generated.",
                ],
            },
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        self._save_plan(plan)
        self._log("app_builder_plan_created", plan, risk_score=25)
        return plan

    def update_wizard(self, payload: dict) -> dict:
        plan_id = payload.get("plan_id")
        plan = self.get_plan(plan_id) if plan_id else None
        if not plan:
            prompt = payload.get("notes") or payload.get("app_name") or "Build a new app"
            plan = self.create_plan(prompt=prompt, stack_id=payload.get("stack_id") or "fastapi-react")

        if payload.get("app_name"):
            plan["app_name"] = self._safe_slug(payload["app_name"])
        if payload.get("stack_id"):
            plan["stack"] = self.get_template(payload["stack_id"])
            plan["files_to_create"] = self._planned_files(plan["stack"]["stack_id"], plan["app_name"])
        if payload.get("features"):
            plan["features"] = [self._clean_feature(feature) for feature in payload["features"] if feature.strip()]
            plan["wizard_steps"] = self._wizard_steps(plan["stack"]["stack_id"], plan["features"])
        plan["updated_at"] = datetime.now(UTC).isoformat()
        self._replace_plan(plan)
        self._log("app_builder_wizard_updated", plan, risk_score=15)
        return plan

    def scaffold(self, plan_id: str, approved: bool) -> dict:
        plan = self.get_plan(plan_id)
        if not plan:
            return {"success": False, "requires_approval": True, "errors": ["App builder plan not found."]}
        if not approved:
            self._log("app_builder_scaffold_rejected", plan, blocked=True, risk_score=10)
            return {
                "success": False,
                "requires_approval": True,
                "errors": [],
                "summary": "Scaffold was not created because approval was not provided.",
                "plan": plan,
            }
        if not plan.get("governance", {}).get("safe_to_scaffold", False):
            self._log("app_builder_scaffold_blocked", plan, blocked=True, risk_score=85)
            return {
                "success": False,
                "requires_approval": True,
                "errors": ["Plan failed governance checks and cannot be scaffolded."],
                "plan": plan,
            }

        app_dir = self.output_root / plan["plan_id"]
        created_files: list[str] = []
        for relative_path in plan.get("files_to_create", []):
            safe_path = self._validate_scaffold_path(relative_path)
            output_path = app_dir / safe_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(self._file_content(plan, safe_path), encoding="utf-8")
            created_files.append(output_path.relative_to(self.project_root).as_posix())

        plan["status"] = "scaffolded"
        plan["scaffold_path"] = app_dir.relative_to(self.project_root).as_posix()
        plan["created_files"] = created_files
        plan["updated_at"] = datetime.now(UTC).isoformat()
        self._replace_plan(plan)
        self._log("app_builder_scaffold_created", plan, approved=True, risk_score=30)
        return {
            "success": True,
            "requires_approval": False,
            "plan": plan,
            "created_files": created_files,
            "summary": f"Created {len(created_files)} scaffold file(s) in {plan['scaffold_path']}.",
            "preview_stub": plan.get("preview_stub"),
        }

    def get_plan(self, plan_id: str | None) -> dict | None:
        if not plan_id:
            return None
        return next((item for item in self.storage.read_list(self.filename) if item.get("plan_id") == plan_id), None)

    def list_plans(self, workspace_id: str | None = None) -> list[dict]:
        plans = self.storage.read_list(self.filename)
        if workspace_id:
            plans = [plan for plan in plans if plan.get("workspace_id") == workspace_id]
        return list(reversed(plans))

    def _blocked_plan(self, prompt: str, stack_id: str, workspace_id: str | None, secret_scan: dict, injection: dict) -> dict:
        return {
            "plan_id": str(uuid4()),
            "workspace_id": workspace_id,
            "app_name": "blocked-app-builder-request",
            "prompt": prompt,
            "stack": self.get_template(stack_id),
            "features": [],
            "files_to_create": [],
            "wizard_steps": [],
            "preview_stub": None,
            "risk_level": "high",
            "requires_approval": True,
            "status": "blocked",
            "governance": {
                "secret_scan": secret_scan,
                "prompt_injection": injection,
                "safe_to_scaffold": False,
                "notes": ["Request was blocked because it may contain secrets or unsafe embedded instructions."],
            },
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }

    def _save_plan(self, plan: dict) -> None:
        self.storage.append(self.filename, plan)

    def _replace_plan(self, plan: dict) -> None:
        plans = self.storage.read_list(self.filename)
        next_plans = [plan if item.get("plan_id") == plan.get("plan_id") else item for item in plans]
        self.storage.write_list(self.filename, next_plans)

    def _log(self, action_type: str, plan: dict, approved: bool = False, blocked: bool = False, risk_score: int = 0) -> None:
        self.governance_service.log_event(
            GovernanceEvent(
                workspace_id=plan.get("workspace_id"),
                task_type="app_builder",
                agent_name="App Builder Service",
                action_type=action_type,
                tool_used="app_builder",
                files_accessed=plan.get("files_to_create", []),
                permission_level="approve_to_edit" if "scaffold" in action_type else "plan_only",
                approved=approved,
                blocked=blocked,
                risk_score=risk_score,
                reason=f"App Builder action for {plan.get('app_name')}",
            )
        )

    def _app_name(self, prompt: str) -> str:
        lowered = prompt.lower()
        patterns = [
            r"build (?:an? )?(.+?) app",
            r"create (?:an? )?(.+?) app",
            r"make (?:an? )?(.+?) app",
        ]
        for pattern in patterns:
            match = re.search(pattern, lowered)
            if match:
                return self._safe_slug(match.group(1))
        words = re.findall(r"[a-z0-9]+", lowered)[:4]
        return self._safe_slug("-".join(words) or "generated-app")

    def _features(self, prompt: str) -> list[str]:
        lowered = prompt.lower()
        features = []
        for keyword, label in (
            ("login", "Authentication screen"),
            ("dashboard", "Dashboard view"),
            ("upload", "File upload flow"),
            ("resume", "Resume analysis workflow"),
            ("chat", "Chat interface"),
            ("analytics", "Analytics panel"),
            ("admin", "Admin controls"),
        ):
            if keyword in lowered:
                features.append(label)
        return features or ["Main user flow", "Responsive UI", "Basic API health route"]

    def _planned_files(self, stack_id: str, app_name: str) -> list[str]:
        if stack_id == "nextjs":
            return [f"{app_name}/package.json", f"{app_name}/app/page.jsx", f"{app_name}/app/layout.jsx", f"{app_name}/README.md"]
        if stack_id == "python-cli":
            return [f"{app_name}/src/main.py", f"{app_name}/tests/test_main.py", f"{app_name}/README.md"]
        return [
            f"{app_name}/backend/app/main.py",
            f"{app_name}/backend/app/api/routes.py",
            f"{app_name}/frontend/src/App.jsx",
            f"{app_name}/frontend/package.json",
            f"{app_name}/README.md",
        ]

    def _wizard_steps(self, stack_id: str, features: list[str]) -> list[dict]:
        return [
            {"step": 1, "title": "Confirm stack", "value": stack_id},
            {"step": 2, "title": "Confirm features", "value": ", ".join(features)},
            {"step": 3, "title": "Review generated files", "value": "Scaffold preview only until approved."},
            {"step": 4, "title": "Approve scaffold", "value": "Writes to ignored preview folder."},
        ]

    def _validate_scaffold_path(self, relative_path: str) -> Path:
        normalized = relative_path.replace("\\", "/").strip()
        if not normalized or normalized.startswith("../") or "/../" in normalized:
            raise ValueError(f"Unsafe scaffold path: {relative_path}")
        blocked = {".env", ".git", "node_modules", "venv", "__pycache__"}
        if any(part in blocked for part in normalized.split("/")):
            raise ValueError(f"Blocked scaffold path: {relative_path}")
        return Path(normalized)

    def _file_content(self, plan: dict, relative_path: Path) -> str:
        app_title = plan["app_name"].replace("-", " ").title()
        features = "\n".join(f"- {feature}" for feature in plan.get("features", []))
        suffix = relative_path.as_posix()
        if suffix.endswith("package.json"):
            return '{\n  "scripts": { "build": "vite build" },\n  "dependencies": {},\n  "devDependencies": {}\n}\n'
        if suffix.endswith("main.py"):
            return 'from fastapi import FastAPI\n\napp = FastAPI(title="' + app_title + '")\n\n@app.get("/health")\ndef health():\n    return {"status": "ok"}\n'
        if suffix.endswith("routes.py"):
            return 'from fastapi import APIRouter\n\nrouter = APIRouter()\n\n@router.get("/summary")\ndef summary():\n    return {"app": "' + app_title + '", "status": "planned"}\n'
        if suffix.endswith("App.jsx") or suffix.endswith("page.jsx"):
            return f"export default function App() {{\n  return <main><h1>{app_title}</h1><p>Generated scaffold preview.</p></main>\n}}\n"
        if suffix.endswith("layout.jsx"):
            return "export default function RootLayout({ children }) {\n  return <html><body>{children}</body></html>\n}\n"
        if suffix.endswith("test_main.py"):
            return "def test_scaffold_placeholder():\n    assert True\n"
        return f"# {app_title}\n\nGenerated App Builder scaffold preview.\n\n## Planned features\n{features}\n"

    def _safe_slug(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug[:80] or "generated-app"

    def _clean_feature(self, value: str) -> str:
        return re.sub(r"\s+", " ", value.strip())[:120]
