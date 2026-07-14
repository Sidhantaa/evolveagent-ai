from typing import Any, Callable

from app.config import DATA_DIR, settings
from app.storage.backend import StorageBackend
from app.storage.json_backend import JsonBackend


def _select_backend(data_dir: str) -> StorageBackend:
    """Pick the storage backend from settings. Defaults to JSON (current behavior);
    uses Postgres only when explicitly requested AND a DATABASE_URL is configured."""
    from app.storage.cached_backend import maybe_wrap_with_redis
    if settings.storage_backend.lower() == "postgres" and settings.database_url:
        from app.storage.postgres_backend import PostgresBackend
        return maybe_wrap_with_redis(PostgresBackend(settings.database_url), settings.redis_url)
    return maybe_wrap_with_redis(JsonBackend(data_dir), settings.redis_url)


class StorageService:
    """Facade over a pluggable :class:`StorageBackend` (JSON today; Postgres later).

    The public interface (``read_list`` / ``append`` / ``write_list``) is
    unchanged, so the 140+ services built on it are untouched. Swap the backend
    via the constructor; ``data_dir`` is retained for backward compatibility
    (some services list files under it directly).
    """

    def __init__(self, data_dir: str = DATA_DIR, backend: StorageBackend | None = None):
        self.data_dir = data_dir
        self.backend: StorageBackend = backend or _select_backend(data_dir)
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
            "self_healing_checks.json",
            "self_healing_findings.json",
            "self_healing_repairs.json",
            "company_brain_reports.json",
            "company_brain_decisions.json",
            "company_brain_strategy.json",
            "device_operator_sessions.json",
            "device_operator_actions.json",
            "device_operator_audit.json",
            "training_datasets.json",
            "training_examples.json",
            "training_exports.json",
            "training_runs.json",
            "training_comparisons.json",
            "avatar_personas.json",
            "voice_response_settings.json",
            "meeting_voice_sessions.json",
            "persona_consent_records.json",
            "life_schedule_items.json",
            "life_tasks.json",
            "life_reminders.json",
            "life_deadlines.json",
            "life_plans.json",
            "universal_operator_sessions.json",
            "universal_workflows.json",
            "universal_actions.json",
            "universal_handoffs.json",
            "universal_operator_audit.json",
            "saas_projects.json",
            "saas_validations.json",
            "saas_roadmaps.json",
            "saas_architecture_plans.json",
            "saas_launch_assets.json",
            "saas_feedback_items.json",
            "business_workflows.json",
            "business_approval_items.json",
            "business_reports.json",
            "business_kpi_snapshots.json",
            "business_audit_records.json",
            "compliance_intel_policies.json",
            "compliance_scans.json",
            "sensitive_data_findings.json",
            "contract_reviews.json",
            "compliance_checklists.json",
            "audit_packages.json",
            "executive_board_sessions.json",
            "executive_board_votes.json",
            "executive_board_reports.json",
            "executive_board_recommendations.json",
            "innovation_research_items.json",
            "innovation_competitors.json",
            "innovation_trends.json",
            "innovation_ideas.json",
            "innovation_experiments.json",
            "innovation_prototypes.json",
            "innovation_reports.json",
            "simulation_worlds.json",
            "simulation_scenarios.json",
            "simulation_personas.json",
            "simulation_events.json",
            "simulation_outcomes.json",
            "simulation_reports.json",
            "organizations.json",
            "organization_members.json",
            "organization_roles.json",
            "organization_permissions.json",
            "organization_workspaces.json",
            "organization_activity.json",
            "hardware_devices.json",
            "companion_sessions.json",
            "wake_mode_settings.json",
            "companion_readiness_checks.json",
            "companion_audit.json",
            "operating_layer_snapshots.json",
            "operating_layer_capabilities.json",
            "operating_layer_recommendations.json",
            "operating_layer_audit.json",
            "mcp_connectors.json",
            "mcp_connector_events.json",
            "mcp_execution_requests.json",
            "mcp_execution_results.json",
            "mcp_policies.json",
            "mcp_replay_records.json",
            "mcp_secret_refs.json",
            "health_snapshots.json",
            "usage_ledger_entries.json",
            "usage_budgets.json",
            "retrieval_documents.json",
            "retrieval_queries.json",
            "eval_suites.json",
            "eval_runs.json",
            "playbooks.json",
            "playbook_runs.json",
            "operating_layer_v2_snapshots.json",
            "notifications.json",
            "workspace_templates.json",
            "scheduled_tasks.json",
            "scheduled_task_runs.json",
            "data_export_log.json",
            "os2_snapshots.json",
            "master_agent_runs.json",
            "git_repos.json",
            "agent_profiles.json",
            "voice_console_settings.json",
            "voice_console_events.json",
            "durable_workflow_defs.json",
            "durable_workflow_runs.json",
            "durable_workflow_effects.json",
            "marketplace_hub_listings.json",
            "marketplace_hub_installs.json",
            "design_agent_analyses.json",
            "repo_finder_searches.json",
            "adaptive_learning_items.json",
            "permission_profiles.json",
            "imported_records.json",
            "marketplace_plugins.json",
            "qa_results.json",
            "demo_seed_log.json",
            "settings_center.json",
            "provider_control.json",
            "notifications_inbox.json",
            "team_members.json",
            "team_assignments.json",
            "team_standups.json",
            "team_sprints.json",
            "team_reviews.json",
            "team_manager_reports.json",
            "agent_governance_policies.json",
            "system_events.json",
            "event_subscriptions.json",
        ):
            self.backend.ensure(filename)

    def read_list(self, filename: str) -> list[dict[str, Any]]:
        return self.backend.read_list(filename)

    def append(self, filename: str, item: dict[str, Any]) -> None:
        self.backend.append(filename, item)

    def write_list(self, filename: str, items: list[dict[str, Any]]) -> None:
        self.backend.write_list(filename, items)

    def update_list(self, filename: str, mutator: Callable[[list[dict[str, Any]]], Any]) -> Any:
        """Atomic find-mutate-persist -- use this instead of a separate
        read_list() + write_list() pair whenever the write depends on the
        read, to avoid a lost-update race with a concurrent append()/
        write_list()/update_list() on the same collection."""
        return self.backend.update_list(filename, mutator)

    def backend_kind(self) -> str:
        inner = getattr(self.backend, "inner", self.backend)  # unwrap cache decorator
        return "postgres" if type(inner).__name__ == "PostgresBackend" else "json"

    def status(self) -> dict[str, Any]:
        """Read-only storage status for the Dev Console / /api/system/storage-status."""
        try:
            stats = self.backend.stats()
        except Exception as exc:  # never fail the status endpoint
            stats = {"kind": self.backend_kind(), "collections": None, "total_documents": None, "error": type(exc).__name__}
        return {
            "backend": stats.get("kind", self.backend_kind()),
            "collections": stats.get("collections"),
            "total_documents": stats.get("total_documents"),
            "postgres_ready": bool(settings.database_url),
            "redis_ready": bool(settings.redis_url),
            "cache": stats.get("cache", "none"),
        }
