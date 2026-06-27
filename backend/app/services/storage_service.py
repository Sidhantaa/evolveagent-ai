import json
import os
from threading import Lock
from typing import Any
from uuid import uuid4

from app.config import DATA_DIR


class StorageService:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self._lock = Lock()
        os.makedirs(self.data_dir, exist_ok=True)
        for filename in (
            "tasks.json",
            "memory.json",
            "evolution_logs.json",
            "chat_sessions.json",
            "messages.json",
            "files.json",
            "agent_analytics.json",
            "feedback.json",
            "automation_runs.json",
            "automation_logs.json",
            "approval_chains.json",
            "approval_audit.json",
            "learning_memory.json",
            "prompt_versions.json",
            "workflow_strategies.json",
            "model_performance.json",
            "user_preferences.json",
            "recordings.json",
            "governance_log.json",
            "goals.json",
            "task_graphs.json",
            "custom_agents.json",
            "workspaces.json",
            "workspace_memory.json",
            "memory_vectors.json",
            "memory_consolidation_jobs.json",
            "knowledge_links.json",
            "tool_registry.json",
            "tool_execution_history.json",
            "plugin_manifests.json",
            "linear_links.json",
            "codex_jobs.json",
            "agent_jobs.json",
            "system_prompt_registry.json",
            "quality_runs.json",
            "app_builder_projects.json",
            "debate_sessions.json",
            "simulation_runs.json",
            "research_sessions.json",
            "research_sources.json",
            "research_citations.json",
            "digital_twin_profiles.json",
            "compliance_policies.json",
            "compliance_reports.json",
            "slack_notifications.json",
            "notion_exports.json",
            "autopilot_runs.json",
            "autopilot_actions.json",
            "autopilot_settings.json",
            "autopilot_checkpoints.json",
            "evaluation_benchmarks.json",
            "evaluation_runs.json",
            "evaluation_ab_tests.json",
            "evaluation_regressions.json",
            "project_risks.json",
            "project_status_reports.json",
            "portfolio_reports.json",
            "agent_marketplace_teams.json",
            "agent_marketplace_ratings.json",
            "agent_marketplace_installs.json",
            "agent_departments.json",
            "department_runs.json",
            "department_collaboration.json",
            "business_leads.json",
            "business_support_cases.json",
            "business_documents.json",
            "business_proposals.json",
            "business_marketing_calendar.json",
            "business_kpis.json",
            "chief_daily_plans.json",
            "chief_weekly_plans.json",
            "chief_followups.json",
            "chief_priority_scores.json",
            "business_simulations.json",
            "business_simulation_scenarios.json",
            "business_simulation_results.json",
            "multimodal_items.json",
            "multimodal_analyses.json",
            "industry_modes.json",
            "industry_mode_runs.json",
            "agent_network_contracts.json",
            "agent_network_handoffs.json",
            "agent_network_audits.json",
        ):
            self._ensure_file(filename)

    def _path(self, filename: str) -> str:
        return os.path.join(self.data_dir, filename)

    def _ensure_file(self, filename: str) -> None:
        path = self._path(filename)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as file:
                json.dump([], file)

    def read_list(self, filename: str) -> list[dict[str, Any]]:
        self._ensure_file(filename)
        with self._lock:
            with open(self._path(filename), "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = []
        return data if isinstance(data, list) else []

    def append(self, filename: str, item: dict[str, Any]) -> None:
        with self._lock:
            self._ensure_file(filename)
            with open(self._path(filename), "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = []
            if not isinstance(data, list):
                data = []
            data.append(item)
            self._atomic_write(filename, data)

    def write_list(self, filename: str, items: list[dict[str, Any]]) -> None:
        with self._lock:
            self._ensure_file(filename)
            self._atomic_write(filename, items)

    def _atomic_write(self, filename: str, items: list[dict[str, Any]]) -> None:
        path = self._path(filename)
        temp_path = f"{path}.{uuid4().hex}.tmp"
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(items, file, indent=2)
        os.replace(temp_path, path)
