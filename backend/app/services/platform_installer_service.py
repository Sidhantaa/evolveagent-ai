from __future__ import annotations

import os

from app.config import BACKEND_DIR, settings

PLATFORM_NAME = "EvolveAgent OS"
PLATFORM_VERSION = "v15.0"


class PlatformInstallerService:
    """EVO-320 Unified Platform Installer.

    Generates local setup/readiness instructions for the whole platform. It is
    read-only: it never installs packages, writes files, or runs commands. It
    only inspects which configuration files exist and which recommended
    environment variables are present, then returns guidance.
    """

    def __init__(self) -> None:
        self.backend_dir = BACKEND_DIR
        self.repo_root = os.path.dirname(BACKEND_DIR)
        self.frontend_dir = os.path.join(self.repo_root, "frontend")

    def _exists(self, *parts: str) -> bool:
        return os.path.exists(os.path.join(*parts))

    def installer(self) -> dict:
        requirements_present = self._exists(self.backend_dir, "requirements.txt")
        package_present = self._exists(self.frontend_dir, "package.json")
        env_example_present = self._exists(self.backend_dir, ".env.example")

        missing: list[str] = []
        if not getattr(settings, "anthropic_api_key", None) and not getattr(settings, "openai_api_key", None):
            missing.append("ANTHROPIC_API_KEY or OPENAI_API_KEY (at least one model provider key is recommended)")
        if not self._exists(self.backend_dir, ".env"):
            missing.append("backend/.env (copy backend/.env.example and fill in keys)")

        return {
            "platform": PLATFORM_NAME,
            "version": PLATFORM_VERSION,
            "backend_steps": [
                "cd backend",
                "python -m venv venv",
                "source venv/bin/activate  # Windows: venv\\Scripts\\activate",
                "pip install -r requirements.txt",
                "cp .env.example .env  # then add your provider API key(s)",
                "./venv/bin/uvicorn app.main:app --reload",
            ],
            "frontend_steps": [
                "cd frontend",
                "npm install",
                "npm run dev",
            ],
            "environment_variables": [
                {"name": "ANTHROPIC_API_KEY", "required": False, "purpose": "Anthropic Claude model access"},
                {"name": "OPENAI_API_KEY", "required": False, "purpose": "OpenAI model access"},
                {"name": "GEMINI_API_KEY", "required": False, "purpose": "Google Gemini model access"},
                {"name": "MISTRAL_API_KEY", "required": False, "purpose": "Mistral model access"},
            ],
            "optional_integrations": [
                {"name": "LINEAR_API_KEY", "purpose": "Linear issue sync"},
                {"name": "SLACK_WEBHOOK_URL", "purpose": "Slack notifications"},
                {"name": "NOTION_API_KEY", "purpose": "Notion exports"},
                {"name": "CODEX_CLI_COMMAND", "purpose": "Local Codex worker integration"},
            ],
            "verification_commands": [
                "cd backend && ./venv/bin/pytest -q",
                "cd frontend && npm run build",
            ],
            "readiness": {
                "backend_requirements_present": requirements_present,
                "frontend_package_present": package_present,
                "env_example_present": env_example_present,
                "missing_recommended_config": missing,
            },
            "safety_notes": [
                "EvolveAgent OS is local-first; this installer only prints guidance and never installs or runs anything.",
                "No secrets are written or committed by the installer.",
                "Provider API keys are optional for local exploration but required for live model calls.",
            ],
        }
