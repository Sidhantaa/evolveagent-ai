from datetime import UTC, datetime
from collections import Counter
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse

from app.agents.learning_agent import LearningAgent
from app.agents.master_agent import MasterOrchestratorAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.test_generation_agent import TestGenerationAgent
from app.models.request_models import (
    AgentJobActionRequest,
    AgentPackInstallRequest,
    AgentTeamCreateRequest,
    AgentTeamImportRequest,
    AgentTeamRatingRequest,
    AgentTeamUpdateRequest,
    AppBuilderPlanRequest,
    AppBuilderScaffoldRequest,
    AppBuilderWizardRequest,
    ApprovalDecisionRequest,
    AutomationApplyRequest,
    AutopilotCheckpointDecisionRequest,
    AutopilotRunControlRequest,
    AutopilotRunCreateRequest,
    AutopilotSettingsUpdateRequest,
    AssistantCommandRequest,
    BusinessDocumentCreateRequest,
    BusinessDocumentUpdateRequest,
    BusinessLeadCreateRequest,
    BusinessLeadUpdateRequest,
    BusinessMarketingItemCreateRequest,
    BusinessMarketingItemUpdateRequest,
    BusinessProposalCreateRequest,
    BusinessProposalUpdateRequest,
    BusinessSupportCaseCreateRequest,
    BusinessSupportCaseUpdateRequest,
    ChiefFollowupCreateRequest,
    ChiefFollowupUpdateRequest,
    ChiefPlanRequest,
    SimulationScenarioCreateRequest,
    SimulationScenarioUpdateRequest,
    MultimodalItemCreateRequest,
    MultimodalAnalyzeRequest,
    CreateAgentJobRequest,
    CreateKnowledgeLinkRequest,
    CreateChatRequest,
    CreateCustomAgentRequest,
    CreateGoalRequest,
    CreateGoalTaskRequest,
    CreateWorkspaceMemoryRequest,
    CreateWorkspaceRequest,
    DebateConsensusRequest,
    DebateCreateRequest,
    DepartmentCollaborationRequest,
    DepartmentCreateRequest,
    DepartmentRunRequest,
    DepartmentUpdateRequest,
    DigitalTwinUpdateRequest,
    EvaluationABTestRequest,
    PluginManifestValidateRequest,
    PortfolioReportRequest,
    ProjectReportRequest,
    ProjectRiskRequest,
    ProjectRiskUpdateRequest,
    EvaluationRunRequest,
    FeedbackRequest,
    GitBranchRequest,
    GitCommitRequest,
    GitPushRequest,
    ImageSmokeTestRequest,
    PiiScanRequest,
    PromptDecisionRequest,
    PromptProposalRequest,
    QualityLinearSummaryRequest,
    RealApiErrorDecodeRequest,
    ProviderSmokeTestRequest,
    QualityRunRequest,
    RenameChatRequest,
    ResearchCitationCreateRequest,
    ResearchSessionCreateRequest,
    ResearchSourceCreateRequest,
    ResearchSearchRequest,
    RetentionPolicyRequest,
    RunRequest,
    SimulationCreateRequest,
    SlackTestNotificationRequest,
    TestSuggestionRequest,
    TranscriptionSmokeTestRequest,
    UpdateCustomAgentRequest,
    UpdateGoalRequest,
    UpdateGoalTaskRequest,
    UpdateWorkspaceMemoryRequest,
    UpdateWorkspaceRequest,
    LinearCommentRequest,
    LinearCursorVerifyRequest,
    MemoryConsolidationJobRequest,
    MemoryConsolidateRequest,
    NotionExportRequest,
    RegisterToolRequest,
    UpdateSystemPromptRequest,
)
from app.models.response_models import AutomationApplyResult, GovernanceEvent, ProviderStatus, RunResponse
from app.services.governance_service import GovernanceService
from app.services.custom_agent_service import CustomAgentService
from app.services.agent_marketplace_service import AgentMarketplaceService
from app.services.goal_service import GoalService
from app.services.llm_router import llm_router
from app.services.permission_service import PermissionService
from app.services.file_service import FileService
from app.services.image_service import ImageService
from app.services.prompt_version_service import PromptVersionService
from app.services.recording_service import RecordingService
from app.services.real_api_control_service import RealApiControlService
from app.services.research_session_service import ResearchSessionService
from app.services.research_search_service import ResearchSearchService
from app.services.safe_command_runner import SafeCommandRunner
from app.services.safe_file_editor import SafeFileEditor
from app.services.storage_service import StorageService
from app.services.workspace_service import WorkspaceService
from app.services.memory_intelligence_service import MemoryIntelligenceService
from app.services.knowledge_service import KnowledgeService
from app.services.assistant_command_service import AssistantCommandService
from app.services.app_builder_service import AppBuilderService
from app.services.approval_service import ApprovalService
from app.services.autopilot_service import AutopilotService
from app.services.agent_scheduler_service import AgentSchedulerService
from app.services.kernel_service import KernelService
from app.services.plugin_loader_service import PluginLoaderService
from app.services.system_prompt_registry_service import SystemPromptRegistryService
from app.services.test_quality_service import TestQualityService
from app.services.tool_execution_service import ToolExecutionService
from app.services.tool_registry_service import ToolRegistryService
from app.services.user_preference_service import UserPreferenceService
from app.services.workflow_strategy_service import WorkflowStrategyService
from app.services.linear_service import LinearService, LinearServiceError
from app.services.linear_link_service import LinearLinkService
from app.services.linear_orchestration_service import LinearOrchestrationService
from app.services.linear_poll_worker import LinearPollWorker
from app.services.git_service import GitService
from app.services.codex_job_service import CodexJobService
from app.services.codex_worker_service import CodexWorkerService, CodexWorkerError
from app.services.debate_simulation_service import DebateSimulationService
from app.services.digital_twin_service import DigitalTwinService
from app.services.evaluation_lab_service import EvaluationLabService
from app.services.os_scheduler_service import OSSchedulerService
from app.services.platform_installer_service import PlatformInstallerService
from app.services.plugin_sdk_service import PluginSDKService
from app.services.agent_department_service import AgentDepartmentService
from app.services.business_operator_service import BusinessOperatorService
from app.services.chief_of_staff_service import ChiefOfStaffService
from app.services.business_simulator_service import BusinessSimulatorService
from app.services.multimodal_agent_service import MultimodalAgentService
from app.services.portfolio_service import PortfolioService
from app.services.project_manager_service import ProjectManagerService
from app.services.sla_monitoring_service import SLAMonitoringService
from app.services.secret_scanner import SecretScanner
from app.services.compliance_service import ComplianceService
from app.services.slack_notification_service import SlackNotificationService
from app.services.notion_export_service import NotionExportService

router = APIRouter()
storage = StorageService()
memory_agent = MemoryAgent(storage)
master_agent = MasterOrchestratorAgent(storage=storage, memory_agent=memory_agent)
file_service = FileService(storage)
image_service = ImageService()
recording_service = RecordingService(storage)
real_api_control_service = RealApiControlService(llm_router, image_service, recording_service.transcription)
safe_file_editor = SafeFileEditor()
safe_command_runner = SafeCommandRunner()
permission_service = PermissionService()
governance_service = GovernanceService(storage)
approval_service = ApprovalService(storage, governance_service)
prompt_versions = PromptVersionService(storage)
system_prompt_registry = SystemPromptRegistryService(storage, prompt_versions)
learning_agent = LearningAgent(storage)
workflow_strategy = WorkflowStrategyService(storage)
user_preferences = UserPreferenceService(storage)
goal_service = GoalService(storage)
custom_agent_service = CustomAgentService(storage)
workspace_service = WorkspaceService(storage)
agent_marketplace_service = AgentMarketplaceService(storage, custom_agent_service, workspace_service, governance_service)
autopilot_service = AutopilotService(storage, permission_service, governance_service)
memory_intelligence_service = MemoryIntelligenceService(storage)
knowledge_service = KnowledgeService(storage, workspace_service)
assistant_commands = AssistantCommandService(workspace_service, knowledge_service)
tool_registry = ToolRegistryService(storage, permission_service)
tool_execution_service = ToolExecutionService(storage)
plugin_loader = PluginLoaderService(storage, tool_registry, governance_service)
plugin_loader.load_plugins()
agent_scheduler = AgentSchedulerService(storage, governance_service, workspace_service)
kernel_service = KernelService(master_agent, agent_scheduler)
linear_service = LinearService(SecretScanner())
linear_link_service = LinearLinkService(storage)
git_service = GitService()
test_quality_service = TestQualityService(
    storage=storage,
    command_runner=safe_command_runner,
    git_service=git_service,
    governance_service=governance_service,
    test_generation_agent=TestGenerationAgent(),
)
app_builder_service = AppBuilderService(storage, governance_service)
debate_simulation_service = DebateSimulationService(storage, governance_service)
research_session_service = ResearchSessionService(storage, workspace_service, governance_service)
research_search_service = ResearchSearchService(
    storage=storage,
    workspace_service=workspace_service,
    governance_service=governance_service,
    research_session_service=research_session_service,
)
digital_twin_service = DigitalTwinService(storage, workspace_service, governance_service)
evaluation_lab_service = EvaluationLabService(storage, governance_service)
project_manager_service = ProjectManagerService(storage, goal_service, governance_service)
portfolio_service = PortfolioService(storage, workspace_service, governance_service)
agent_department_service = AgentDepartmentService(storage, governance_service, permission_service)
business_operator_service = BusinessOperatorService(storage, governance_service)
chief_of_staff_service = ChiefOfStaffService(storage, governance_service)
business_simulator_service = BusinessSimulatorService(storage, governance_service)
multimodal_agent_service = MultimodalAgentService(storage, governance_service)
platform_installer_service = PlatformInstallerService()
plugin_sdk_service = PluginSDKService()
sla_monitoring_service = SLAMonitoringService(storage)
os_scheduler_service = OSSchedulerService(storage)
compliance_service = ComplianceService(storage, governance_service)
slack_notifications = SlackNotificationService(storage, governance_service)
notion_exports = NotionExportService(storage, governance_service)
linear_orchestration = LinearOrchestrationService(
    storage=storage,
    linear_service=linear_service,
    link_service=linear_link_service,
    goal_service=goal_service,
    governance_service=governance_service,
    master_agent=master_agent,
    workspace_service=workspace_service,
    git_service=git_service,
    command_runner=safe_command_runner,
)
codex_job_service = CodexJobService(storage)
codex_worker_service = CodexWorkerService(
    job_service=codex_job_service,
    git_service=git_service,
    command_runner=safe_command_runner,
    linear_orchestration=linear_orchestration,
)
linear_poll_worker = LinearPollWorker(linear_service, linear_orchestration, codex_worker=codex_worker_service)


def filter_by_workspace(items: list[dict], workspace_id: str | None = None) -> list[dict]:
    if not workspace_id:
        return items
    return [item for item in items if item.get("workspace_id") == workspace_id]


@router.get("/git/status")
def get_git_status() -> dict:
    status = git_service.git_status()
    return {
        **status,
        "branch": git_service.current_branch(),
        "changed_files": git_service.list_changed_files(),
        "diff_summary": git_service.diff_summary(),
    }


@router.post("/git/branch")
def create_or_checkout_git_branch(request: GitBranchRequest) -> dict:
    return git_service.create_branch(request.branch_name)


@router.post("/git/stage-safe")
def stage_safe_git_files() -> dict:
    return git_service.add_safe_files()


@router.post("/git/commit")
def commit_git_changes(request: GitCommitRequest) -> dict:
    return git_service.commit(request.message)


@router.post("/git/push")
def push_git_branch(request: GitPushRequest | None = None) -> dict:
    payload = request or GitPushRequest()
    return git_service.push(remote=payload.remote, branch=payload.branch)


@router.get("/quality/status")
def get_quality_status() -> dict:
    return test_quality_service.summary()


@router.post("/quality/suggest-tests")
def suggest_quality_tests(request: TestSuggestionRequest) -> dict:
    files = request.changed_files or git_service.list_changed_files()
    return test_quality_service.suggest_tests(files)


@router.post("/quality/run")
def run_quality_checks(request: QualityRunRequest | None = None) -> dict:
    payload = request or QualityRunRequest()
    commands = payload.commands or ["pytest", "npm run build"]
    if any(not safe_command_runner.is_allowed(command) for command in commands):
        raise HTTPException(status_code=400, detail="Quality checks can only run allowlisted commands.")
    return test_quality_service.run_quality_checks(commands=commands, issue_id=payload.issue_id)


@router.get("/quality/flaky-tests")
def get_flaky_tests() -> dict:
    return {"flaky_tests": test_quality_service.detect_flaky_tests()}


@router.get("/quality/gate")
def get_quality_gate() -> dict:
    latest = test_quality_service.latest_run()
    if not latest:
        return {
            "passed": False,
            "blocked": True,
            "reason": "No quality run has been recorded yet.",
            "latest_run": None,
        }
    return {**latest.get("quality_gate", {}), "latest_run": latest}


@router.post("/quality/linear-summary")
def post_quality_linear_summary(request: QualityLinearSummaryRequest) -> dict:
    runs = test_quality_service.list_runs(100)
    run = None
    if request.quality_run_id:
        run = next((item for item in runs if item.get("quality_run_id") == request.quality_run_id), None)
    else:
        run = test_quality_service.latest_run()
    if not run:
        raise HTTPException(status_code=404, detail="Quality run not found")
    try:
        comment = linear_service.add_linear_comment(request.issue_id, run.get("regression_summary", "Quality run completed."))
    except LinearServiceError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"posted": True, "issue_id": request.issue_id, "quality_run_id": run.get("quality_run_id"), "comment": comment}


@router.get("/app-builder/templates")
def list_app_builder_templates() -> list[dict]:
    return app_builder_service.list_templates()


@router.get("/app-builder/plans")
def list_app_builder_plans(workspace_id: str | None = Query(default=None)) -> list[dict]:
    return app_builder_service.list_plans(workspace_id)


@router.get("/app-builder/plans/{plan_id}")
def get_app_builder_plan(plan_id: str) -> dict:
    plan = app_builder_service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="App builder plan not found")
    return plan


@router.post("/app-builder/plan")
def create_app_builder_plan(request: AppBuilderPlanRequest) -> dict:
    return app_builder_service.create_plan(
        prompt=request.prompt,
        stack_id=request.stack_id,
        workspace_id=request.workspace_id,
    )


@router.post("/app-builder/wizard")
def update_app_builder_wizard(request: AppBuilderWizardRequest) -> dict:
    return app_builder_service.update_wizard(request.model_dump())


@router.post("/app-builder/scaffold")
def scaffold_app_builder_plan(request: AppBuilderScaffoldRequest) -> dict:
    return app_builder_service.scaffold(plan_id=request.plan_id, approved=request.approved)


@router.get("/debate/summary")
def get_debate_simulation_summary(workspace_id: str | None = Query(default=None)) -> dict:
    return debate_simulation_service.summary(workspace_id)


@router.get("/debate/sessions")
def list_debate_sessions(workspace_id: str | None = Query(default=None)) -> list[dict]:
    return debate_simulation_service.list_debates(workspace_id)


@router.get("/debate/sessions/{debate_id}")
def get_debate_session(debate_id: str) -> dict:
    debate = debate_simulation_service.get_debate(debate_id)
    if not debate:
        raise HTTPException(status_code=404, detail="Debate session not found")
    return debate


@router.post("/debate/sessions")
def create_debate_session(request: DebateCreateRequest) -> dict:
    return debate_simulation_service.create_debate(
        prompt=request.prompt,
        workspace_id=request.workspace_id,
        agents=request.agents,
    )


@router.post("/debate/consensus")
def select_debate_consensus(request: DebateConsensusRequest) -> dict:
    result = debate_simulation_service.consensus_for(request.debate_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Debate session not found"))
    return result


@router.get("/simulations")
def list_simulation_runs(workspace_id: str | None = Query(default=None)) -> list[dict]:
    return debate_simulation_service.list_simulations(workspace_id)


@router.get("/simulations/{simulation_id}")
def get_simulation_run(simulation_id: str) -> dict:
    simulation = debate_simulation_service.get_simulation(simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    return simulation


@router.post("/simulations")
def create_simulation_run(request: SimulationCreateRequest) -> dict:
    return debate_simulation_service.create_simulation(
        prompt=request.prompt,
        scenario=request.scenario,
        workspace_id=request.workspace_id,
    )


@router.get("/research/sessions")
def list_research_sessions(workspace_id: str | None = Query(default=None)) -> list[dict]:
    return research_session_service.list_sessions(workspace_id)


@router.post("/research/sessions")
def create_research_session(request: ResearchSessionCreateRequest) -> dict:
    return research_session_service.create_session(
        query=request.query,
        workspace_id=request.workspace_id,
        require_approval=request.require_approval,
        notes=request.notes,
    )


@router.get("/research/sessions/{research_id}")
def get_research_session(research_id: str) -> dict:
    session = research_session_service.get_session(research_id)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")
    return session


@router.post("/research/sessions/{research_id}/approve")
def approve_research_session(research_id: str) -> dict:
    session = research_session_service.approve_session(research_id, approved=True)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")
    return session


@router.post("/research/sessions/{research_id}/reject")
def reject_research_session(research_id: str) -> dict:
    session = research_session_service.approve_session(research_id, approved=False)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")
    return session


@router.post("/research/sessions/{research_id}/sources")
def add_research_source(research_id: str, request: ResearchSourceCreateRequest) -> dict:
    source = research_session_service.add_source(research_id, request.model_dump())
    if not source:
        raise HTTPException(status_code=404, detail="Research session not found")
    return source


@router.get("/research/sessions/{research_id}/sources")
def list_research_sources(research_id: str) -> list[dict]:
    if not research_session_service.get_session(research_id):
        raise HTTPException(status_code=404, detail="Research session not found")
    return research_session_service.list_sources(research_id)


@router.post("/research/sessions/{research_id}/citations")
def add_research_citation(research_id: str, request: ResearchCitationCreateRequest) -> dict:
    citation = research_session_service.add_citation(research_id, request.model_dump())
    if not citation:
        raise HTTPException(status_code=404, detail="Research session or source not found")
    return citation


@router.get("/research/sessions/{research_id}/citations")
def list_research_citations(research_id: str) -> list[dict]:
    if not research_session_service.get_session(research_id):
        raise HTTPException(status_code=404, detail="Research session not found")
    return research_session_service.list_citations(research_id)


@router.get("/research/sessions/{research_id}/report")
def get_research_report(research_id: str) -> dict:
    report = research_session_service.generate_report(research_id)
    if not report:
        raise HTTPException(status_code=404, detail="Research session not found")
    return report


@router.post("/research/search")
def run_controlled_search(request: ResearchSearchRequest) -> dict:
    return research_search_service.search(
        query=request.query,
        workspace_id=request.workspace_id,
        max_results=request.max_results,
    )


@router.post("/research/sessions/{research_id}/search")
def run_session_controlled_search(research_id: str, request: ResearchSearchRequest) -> dict:
    session = research_session_service.get_session(research_id)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    search_res = research_search_service.search(
        query=request.query,
        workspace_id=request.workspace_id,
        max_results=request.max_results,
    )

    added_sources = []
    for item in search_res["results"]:
        payload = {
            "title": item["title"],
            "url": item["url"],
            "publisher": item["publisher"],
            "snippet": item["snippet"],
            "fetched": True,
        }
        source = research_session_service.add_source(research_id, payload)
        if source:
            added_sources.append(source)

    research_search_service.log_sources_added(
        research_id=research_id,
        query=request.query,
        workspace_id=session.get("workspace_id"),
        num_sources=len(search_res["results"]),
    )

    updated_session = research_session_service.get_session(research_id)
    if not updated_session:
        raise HTTPException(status_code=404, detail="Research session not found")
    return {
        **updated_session,
        "search_result": search_res,
        "sources_added": added_sources,
    }


@router.post("/workspaces")
def create_workspace(request: CreateWorkspaceRequest) -> dict:
    return workspace_service.create_workspace(request.model_dump())


@router.get("/workspaces")
def list_workspaces(include_archived: bool = Query(default=False)) -> list[dict]:
    return workspace_service.list_workspaces(include_archived=include_archived)


@router.get("/workspaces/{workspace_id}")
def get_workspace(workspace_id: str) -> dict:
    workspace = workspace_service.get_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {**workspace, "summary": workspace_service.summarize_workspace(workspace_id)}


@router.patch("/workspaces/{workspace_id}")
def update_workspace(workspace_id: str, request: UpdateWorkspaceRequest) -> dict:
    workspace = workspace_service.update_workspace(workspace_id, request.model_dump(exclude_unset=True))
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.delete("/workspaces/{workspace_id}")
def archive_workspace(workspace_id: str) -> dict:
    workspace = workspace_service.archive_workspace(workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"archived": workspace.get("status") == "archived", "workspace": workspace}


@router.post("/workspaces/{workspace_id}/memory")
def create_workspace_memory(workspace_id: str, request: CreateWorkspaceMemoryRequest) -> dict:
    return workspace_service.create_memory(workspace_id, request.model_dump())


@router.get("/workspaces/{workspace_id}/memory")
def list_workspace_memory(
    workspace_id: str,
    q: str | None = Query(default=None),
    memory_type: str | None = Query(default=None),
    tier: str | None = Query(default=None, pattern="^(hot|warm|archived)$"),
    include_archived: bool = Query(default=True),
) -> list[dict]:
    return workspace_service.list_memory(
        workspace_id,
        query=q,
        memory_type=memory_type,
        tier=tier,
        include_archived=include_archived,
    )


@router.get("/workspaces/{workspace_id}/memory/intelligence")
def get_workspace_memory_intelligence(workspace_id: str) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id)
    return memory_intelligence_service.summary(resolved)


@router.post("/workspaces/{workspace_id}/memory/re-score")
def rescore_workspace_memory(workspace_id: str) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id)
    return memory_intelligence_service.rescore_workspace(resolved)


@router.post("/workspaces/{workspace_id}/memory/tiers/maintain")
def maintain_workspace_memory_tiers(workspace_id: str) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id)
    return memory_intelligence_service.maintain_tiers(resolved)


@router.post("/workspaces/{workspace_id}/memory/index/rebuild")
def rebuild_workspace_memory_index(workspace_id: str) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id)
    return memory_intelligence_service.rebuild_index(resolved)


@router.get("/workspaces/{workspace_id}/memory/search")
def semantic_search_workspace_memory(
    workspace_id: str,
    q: str = Query(default=""),
    limit: int = Query(default=10, ge=1, le=50),
    include_archived: bool = Query(default=False),
) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id)
    return memory_intelligence_service.semantic_search(resolved, q, limit=limit, include_archived=include_archived)


@router.post("/workspaces/{workspace_id}/memory/consolidate")
def consolidate_workspace_memory(workspace_id: str, request: MemoryConsolidateRequest) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id)
    return memory_intelligence_service.consolidate(resolved, approved=request.approved)


@router.post("/workspaces/{workspace_id}/memory/consolidation-jobs")
def create_memory_consolidation_job(workspace_id: str, request: MemoryConsolidationJobRequest) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id)
    return memory_intelligence_service.create_consolidation_job(resolved, apply=request.apply)


@router.get("/workspaces/{workspace_id}/memory/consolidation-jobs")
def list_memory_consolidation_jobs(
    workspace_id: str,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    resolved = workspace_service.resolve_workspace_id(workspace_id)
    return memory_intelligence_service.list_consolidation_jobs(resolved, limit=limit)


@router.get("/workspaces/{workspace_id}/memory/consolidation-jobs/{job_id}")
def get_memory_consolidation_job(workspace_id: str, job_id: str) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id)
    job = memory_intelligence_service.get_consolidation_job(resolved, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Memory consolidation job not found")
    return job


@router.post("/workspaces/{workspace_id}/memory/consolidation-jobs/{job_id}/apply")
def apply_memory_consolidation_job(workspace_id: str, job_id: str) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id)
    job = memory_intelligence_service.apply_consolidation_job(resolved, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Memory consolidation job not found")
    return job


@router.get("/workspaces/{workspace_id}/memory/{memory_id}")
def get_workspace_memory(workspace_id: str, memory_id: str) -> dict:
    memory = workspace_service.get_memory(workspace_id, memory_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Workspace memory not found")
    return memory


@router.patch("/workspaces/{workspace_id}/memory/{memory_id}")
def update_workspace_memory(workspace_id: str, memory_id: str, request: UpdateWorkspaceMemoryRequest) -> dict:
    memory = workspace_service.update_memory(workspace_id, memory_id, request.model_dump(exclude_unset=True))
    if memory is None:
        raise HTTPException(status_code=404, detail="Workspace memory not found")
    return memory


@router.delete("/workspaces/{workspace_id}/memory/{memory_id}")
def delete_workspace_memory(workspace_id: str, memory_id: str) -> dict[str, bool]:
    if not workspace_service.delete_memory(workspace_id, memory_id):
        raise HTTPException(status_code=404, detail="Workspace memory not found")
    return {"deleted": True}


@router.post("/workspaces/{workspace_id}/memory/{memory_id}/pin")
def pin_workspace_memory(workspace_id: str, memory_id: str) -> dict:
    memory = workspace_service.update_memory(workspace_id, memory_id, {"pinned": True})
    if memory is None:
        raise HTTPException(status_code=404, detail="Workspace memory not found")
    return memory


@router.post("/workspaces/{workspace_id}/memory/{memory_id}/unpin")
def unpin_workspace_memory(workspace_id: str, memory_id: str) -> dict:
    memory = workspace_service.update_memory(workspace_id, memory_id, {"pinned": False})
    if memory is None:
        raise HTTPException(status_code=404, detail="Workspace memory not found")
    return memory


@router.post("/workspaces/{workspace_id}/memory/{memory_id}/archive")
def archive_workspace_memory_item(workspace_id: str, memory_id: str) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id)
    memory = memory_intelligence_service.archive_memory(resolved, memory_id, archived=True)
    if memory is None:
        raise HTTPException(status_code=404, detail="Workspace memory not found")
    return memory


@router.post("/workspaces/{workspace_id}/memory/{memory_id}/restore")
def restore_workspace_memory_item(workspace_id: str, memory_id: str) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id)
    memory = memory_intelligence_service.archive_memory(resolved, memory_id, archived=False)
    if memory is None:
        raise HTTPException(status_code=404, detail="Workspace memory not found")
    return memory


@router.get("/workspaces/{workspace_id}/knowledge")
def get_workspace_knowledge(workspace_id: str) -> dict:
    return knowledge_service.summary(workspace_id)


@router.get("/workspaces/{workspace_id}/knowledge/search")
def search_workspace_knowledge(
    workspace_id: str,
    q: str = Query(default=""),
    source_type: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    return knowledge_service.search(workspace_id, query=q, source_type=source_type, limit=limit)


@router.get("/workspaces/{workspace_id}/knowledge/export", response_model=None)
def export_workspace_knowledge(
    workspace_id: str,
    format: str = Query(default="markdown", pattern="^(markdown|json)$"),
):
    if format == "json":
        return knowledge_service.export_json(workspace_id)
    return PlainTextResponse(
        knowledge_service.export_markdown(workspace_id),
        media_type="text/markdown",
    )


@router.post("/workspaces/{workspace_id}/knowledge/links")
def create_knowledge_link(workspace_id: str, request: CreateKnowledgeLinkRequest) -> dict:
    try:
        return knowledge_service.create_link(workspace_id, request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/workspaces/{workspace_id}/knowledge/links")
def list_knowledge_links(
    workspace_id: str,
    record_type: str | None = Query(default=None),
    record_id: str | None = Query(default=None),
) -> list[dict]:
    return knowledge_service.list_links(workspace_id, record_type=record_type, record_id=record_id)


@router.delete("/workspaces/{workspace_id}/knowledge/links/{link_id}")
def delete_knowledge_link(workspace_id: str, link_id: str) -> dict[str, bool]:
    if not knowledge_service.delete_link(workspace_id, link_id):
        raise HTTPException(status_code=404, detail="Knowledge link not found")
    return {"deleted": True}


@router.get("/assistant/commands")
def list_assistant_commands() -> list[dict]:
    return assistant_commands.list_commands()


@router.post("/assistant/commands/{command_name}")
def run_assistant_command(command_name: str, request: AssistantCommandRequest) -> dict:
    return assistant_commands.run(
        command_name,
        input_text=request.input_text,
        workspace_id=request.workspace_id,
    )


@router.get("/tools")
def list_tools(include_disabled: bool = Query(default=False)) -> list[dict]:
    plugin_loader.load_plugins()
    return tool_registry.list_tools(include_disabled=include_disabled)


@router.get("/tools/history")
def list_tool_execution_history(
    workspace_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict]:
    return tool_execution_service.list_history(workspace_id=workspace_id, limit=limit)


@router.get("/tools/summary")
def get_tool_execution_summary(workspace_id: str | None = Query(default=None)) -> dict:
    return tool_execution_service.summary(workspace_id=workspace_id)


@router.get("/tools/history/{execution_id}")
def get_tool_execution(execution_id: str) -> dict:
    execution = tool_execution_service.get(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Tool execution not found")
    return execution


@router.post("/tools/register")
def register_tool(request: RegisterToolRequest) -> dict:
    try:
        return tool_registry.register_tool(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tools/{name}")
def get_tool(name: str) -> dict:
    tool = tool_registry.get_tool(name)
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.get("/plugins")
def list_plugins() -> list[dict]:
    return plugin_loader.load_plugins()


@router.get("/integrations/slack/status")
def get_slack_integration_status() -> dict:
    return slack_notifications.status()


@router.get("/integrations/slack/notifications")
def list_slack_notifications(limit: int = Query(default=50, ge=1, le=200)) -> list[dict]:
    return slack_notifications.list_notifications(limit=limit)


@router.post("/integrations/slack/test")
def send_slack_test_notification(request: SlackTestNotificationRequest) -> dict:
    resolved_workspace_id = workspace_service.resolve_workspace_id(request.workspace_id) if request.workspace_id else None
    return slack_notifications.send_test_message(
        text=request.text,
        channel=request.channel,
        workspace_id=resolved_workspace_id,
    )


@router.get("/integrations/notion/status")
def get_notion_integration_status() -> dict:
    return notion_exports.status()


@router.get("/integrations/notion/exports")
def list_notion_exports(limit: int = Query(default=50, ge=1, le=200)) -> list[dict]:
    return notion_exports.list_exports(limit=limit)


@router.post("/integrations/notion/export")
def export_to_notion(request: NotionExportRequest) -> dict:
    resolved_workspace_id = workspace_service.resolve_workspace_id(request.workspace_id) if request.workspace_id else None
    return notion_exports.export_page(
        title=request.title,
        content=request.content,
        workspace_id=resolved_workspace_id,
    )


@router.get("/autopilot/settings")
def get_autopilot_settings() -> dict:
    return autopilot_service.get_settings()


@router.patch("/autopilot/settings")
def update_autopilot_settings(request: AutopilotSettingsUpdateRequest) -> dict:
    try:
        return autopilot_service.update_settings(request.model_dump(exclude_none=True))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/autopilot/runs")
def create_autopilot_run(request: AutopilotRunCreateRequest) -> dict:
    return autopilot_service.create_run(
        prompt=request.prompt,
        workspace_id=request.workspace_id,
        mode=request.mode,
        actions=[action.model_dump() for action in request.actions],
    )


@router.get("/autopilot/runs")
def list_autopilot_runs(workspace_id: str | None = Query(default=None)) -> list[dict]:
    return autopilot_service.list_runs(workspace_id)


@router.get("/autopilot/runs/{run_id}")
def get_autopilot_run(run_id: str) -> dict:
    run = autopilot_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Autopilot run not found")
    return run


@router.post("/autopilot/runs/{run_id}/start")
def start_autopilot_run(run_id: str) -> dict:
    try:
        return autopilot_service.start_run(run_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/autopilot/runs/{run_id}/stop")
def stop_autopilot_run(run_id: str, request: AutopilotRunControlRequest | None = None) -> dict:
    try:
        return autopilot_service.stop_run(run_id, reason=request.reason if request else None)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/autopilot/actions")
def list_autopilot_actions(
    run_id: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
) -> list[dict]:
    return autopilot_service.list_actions(run_id=run_id, workspace_id=workspace_id)


@router.get("/autopilot/checkpoints")
def list_autopilot_checkpoints(
    run_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
) -> list[dict]:
    return autopilot_service.list_checkpoints(run_id=run_id, status=status, workspace_id=workspace_id)


@router.post("/autopilot/checkpoints/{checkpoint_id}/decision")
def decide_autopilot_checkpoint(checkpoint_id: str, request: AutopilotCheckpointDecisionRequest) -> dict:
    try:
        return autopilot_service.decide_checkpoint(checkpoint_id, request.decision, request.comment)
    except ValueError as error:
        status_code = 404 if "not found" in str(error).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(error)) from error


@router.post("/run", response_model=RunResponse)
def run_workflow(request: RunRequest) -> RunResponse:
    response = kernel_service.run_workflow(request)
    slack_notifications.notify_run_completed(response)
    notion_exports.export_run_completed(response)
    return response


@router.post("/agent-jobs")
def create_agent_job(request: CreateAgentJobRequest) -> dict:
    return agent_scheduler.create_job(request.model_dump())


@router.get("/agent-jobs")
def list_agent_jobs(
    status: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
) -> list[dict]:
    return agent_scheduler.list_jobs(status=status, workspace_id=workspace_id)


@router.get("/agent-jobs/health")
def agent_jobs_health() -> dict:
    return agent_scheduler.health()


@router.post("/agent-jobs/start-next")
def start_next_agent_job() -> dict:
    job = agent_scheduler.start_next()
    if job is None:
        return {"started": False, "reason": "No queued job is available or concurrency limit is reached."}
    return {"started": True, "job": job}


@router.get("/agent-jobs/{job_id}")
def get_agent_job(job_id: str) -> dict:
    job = agent_scheduler.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Agent job not found")
    return job


@router.post("/agent-jobs/{job_id}/pause")
def pause_agent_job(job_id: str, request: AgentJobActionRequest) -> dict:
    try:
        return agent_scheduler.pause(job_id, request.reason)
    except ValueError as error:
        raise HTTPException(status_code=404 if "not found" in str(error).lower() else 400, detail=str(error)) from error


@router.post("/agent-jobs/{job_id}/resume")
def resume_agent_job(job_id: str, request: AgentJobActionRequest) -> dict:
    try:
        return agent_scheduler.resume(job_id, request.reason)
    except ValueError as error:
        raise HTTPException(status_code=404 if "not found" in str(error).lower() else 400, detail=str(error)) from error


@router.post("/agent-jobs/{job_id}/cancel")
def cancel_agent_job(job_id: str, request: AgentJobActionRequest) -> dict:
    try:
        return agent_scheduler.cancel(job_id, request.reason)
    except ValueError as error:
        raise HTTPException(status_code=404 if "not found" in str(error).lower() else 400, detail=str(error)) from error


@router.post("/agent-jobs/{job_id}/heartbeat")
def heartbeat_agent_job(job_id: str) -> dict:
    try:
        return agent_scheduler.heartbeat(job_id)
    except ValueError as error:
        raise HTTPException(status_code=404 if "not found" in str(error).lower() else 400, detail=str(error)) from error


@router.get("/system-prompts")
def list_system_prompts() -> list[dict]:
    return system_prompt_registry.list_prompts()


@router.get("/system-prompts/{agent_name}")
def get_system_prompt(agent_name: str) -> dict:
    prompt = system_prompt_registry.get_prompt(agent_name)
    if not prompt:
        raise HTTPException(status_code=404, detail="System prompt not found")
    return {"agent_name": agent_name, "prompt": prompt}


@router.post("/system-prompts")
def upsert_system_prompt(request: UpdateSystemPromptRequest) -> dict:
    return system_prompt_registry.upsert_prompt(request.agent_name, request.prompt, request.reason)


@router.post("/files/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    session_id: str | None = Form(default=None),
    workspace_id: str | None = Form(default=None),
) -> dict:
    resolved_workspace_id = workspace_service.resolve_workspace_id(workspace_id)
    return {
        "files": await file_service.process_uploads(
            files,
            session_id=session_id,
            workspace_id=resolved_workspace_id,
        )
    }


@router.post("/recordings/upload")
async def upload_recordings(
    files: list[UploadFile] = File(...),
    session_id: str | None = Form(default=None),
    workspace_id: str | None = Form(default=None),
) -> dict:
    resolved_workspace_id = workspace_service.resolve_workspace_id(workspace_id)
    return {
        "recordings": await recording_service.process_uploads(
            files,
            session_id=session_id,
            workspace_id=resolved_workspace_id,
        )
    }


@router.get("/history")
def get_history() -> list[dict]:
    tasks = storage.read_list("tasks.json")
    return [
        {
            "task_id": task.get("task_id"),
            "task_type": task.get("task_type"),
            "judge_score": task.get("judge_result", {}).get("overall_score"),
            "created_at": task.get("created_at"),
        }
        for task in reversed(tasks)
    ]


@router.get("/memory")
def get_memory() -> list[dict]:
    return memory_agent.get_memory()


@router.get("/evolution")
def get_evolution_logs() -> list[dict]:
    return storage.read_list("evolution_logs.json")


@router.post("/feedback")
def save_feedback(request: FeedbackRequest) -> dict:
    item = request.model_dump()
    item["workspace_id"] = workspace_service.resolve_workspace_id(item.get("workspace_id"))
    item["feedback_id"] = str(uuid4())
    item["created_at"] = datetime.now(UTC).isoformat()
    storage.append("feedback.json", item)
    workflow_strategy.update_feedback_stats(item)
    user_preferences.update_from_feedback(item)
    return {"saved": True, "feedback": item}


@router.post("/automation/apply", response_model=AutomationApplyResult)
def apply_automation(request: AutomationApplyRequest) -> AutomationApplyResult:
    runs = storage.read_list("automation_runs.json")
    run = next((item for item in runs if item.get("run_id") == request.run_id), None)
    if run is None:
        raise HTTPException(status_code=404, detail="Automation run not found")

    approval = approval_service.find_pending_for_run(request.run_id, "automation_apply")
    if approval is None:
        approval = approval_service.create_chain(
            run_id=request.run_id,
            session_id=run.get("session_id"),
            workspace_id=run.get("workspace_id"),
            task_type="app_automation",
            action_type="automation_apply",
            summary="Approve automation apply for safe file validation and allowlisted commands.",
            risk_level=(run.get("automation_plan") or {}).get("risk_level", "medium"),
            metadata={"source": "automation_apply_endpoint"},
        )

    if not request.approved:
        approval_service.decide(approval["approval_id"], "reject", "User rejected automation apply.")
        approval_service.mark_rolled_back(approval["approval_id"], "Rejected before any file validation or command execution.")
        run["status"] = "rejected"
        run["updated_at"] = datetime.now(UTC).isoformat()
        storage.write_list("automation_runs.json", runs)
        governance_service.log_event(
            GovernanceEvent(
                run_id=request.run_id,
                session_id=run.get("session_id"),
                workspace_id=run.get("workspace_id"),
                task_type="app_automation",
                agent_name="Safety Permission Agent",
                action_type="automation_rejected",
                tool_used="PermissionService",
                permission_level="approve_to_edit",
                approved=False,
                blocked=True,
                risk_score=0,
                reason="User rejected the automation plan. No files were changed and no commands were run.",
            )
        )
        result = AutomationApplyResult(
            success=False,
            changed_files=[],
            created_files=[],
            command_results=[],
            errors=[],
            summary="Automation was rejected. No files were changed and no commands were run.",
        )
        storage.append("automation_logs.json", {"run_id": request.run_id, "approved": False, "result": result.model_dump()})
        return result

    if approval.get("status") == "pending":
        approval = approval_service.decide(approval["approval_id"], "approve", "User approved automation apply.")
    if approval.get("status") != "approved":
        raise HTTPException(status_code=409, detail="Automation approval is not approved.")

    plan = run.get("automation_plan", {})
    from app.models.response_models import AutomationPlan

    automation_plan = AutomationPlan(**plan)
    governance_service.log_event(
        GovernanceEvent(
            run_id=request.run_id, 
            session_id=run.get("session_id"),
            workspace_id=run.get("workspace_id"),
            task_type="app_automation",
            agent_name="Safety Permission Agent",
            action_type="automation_approved",
            tool_used="PermissionService",
            permission_level="approve_to_edit",
            approved=True,
            blocked=False,
            risk_score=0,
            reason="User approved automation plan for conservative safety validation.",
        )
    )
    patches = [patch.model_dump() for patch in request.patches] if request.patches else run.get("file_patches", [])
    result = safe_file_editor.apply_patches(patches) if patches else safe_file_editor.apply_plan_conservatively(automation_plan)
    if result.errors:
        for error in result.errors:
            governance_service.log_event(
                GovernanceEvent(
                    run_id=request.run_id,
                    session_id=run.get("session_id"),
                    workspace_id=run.get("workspace_id"),
                    task_type="app_automation",
                    agent_name="Safe File Editor",
                    action_type="file_edit",
                    tool_used="SafeFileEditor",
                    permission_level="blocked",
                    approved=True,
                    blocked=True,
                    risk_score=80,
                    reason=error,
                )
            )
    if result.changed_files or result.created_files:
        governance_service.log_event(
            GovernanceEvent(
                run_id=request.run_id,
                session_id=run.get("session_id"),
                workspace_id=run.get("workspace_id"),
                task_type="app_automation",
                agent_name="Safe File Editor",
                action_type="file_patch_applied",
                tool_used="SafeFileEditor",
                files_accessed=result.changed_files + result.created_files,
                permission_level="approve_to_edit",
                approved=True,
                blocked=False,
                risk_score=25,
                reason=(
                    f"Applied {len(result.changed_files)} changed file(s) and "
                    f"{len(result.created_files)} created file(s) after approval."
                ),
            )
        )
    command_results = []
    if result.success:
        for command in automation_plan.commands_to_run:
            permission_level = permission_service.permission_for_action("command_run", command=command)
            command_result = safe_command_runner.run(command)
            command_results.append(command_result)
            governance_service.log_event(
                GovernanceEvent(
                    run_id=request.run_id,
                    session_id=run.get("session_id"),
                    workspace_id=run.get("workspace_id"),
                    task_type="app_automation",
                    agent_name="Safe Command Runner",
                    action_type="command_run",
                    tool_used="SafeCommandRunner",
                    command_requested=command,
                    permission_level=permission_level if command_result.success else "blocked",
                    approved=True,
                    blocked=not command_result.success,
                    risk_score=0 if command_result.success else 65,
                    reason=command_result.stderr or "Allowlisted command completed.",
                )
            )
        result.command_results = command_results
        if command_results and not all(item.success for item in command_results):
            result.success = False
            result.errors.append("One or more allowlisted commands failed. Review command output before applying further changes.")
            result.summary += " Command verification found failures."

    run["status"] = "applied" if result.success else "failed"
    run["apply_result"] = result.model_dump()
    run["updated_at"] = datetime.now(UTC).isoformat()
    storage.write_list("automation_runs.json", runs)
    storage.append("automation_logs.json", {"run_id": request.run_id, "approved": True, "result": result.model_dump()})
    return result


@router.get("/approvals")
def list_approvals(
    status: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
) -> list[dict]:
    return approval_service.list_chains(status=status, workspace_id=workspace_id)


@router.get("/approvals/audit")
def list_approval_audit(
    workspace_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=250),
) -> list[dict]:
    return approval_service.audit(limit=limit, workspace_id=workspace_id)


@router.get("/approvals/{approval_id}")
def get_approval(approval_id: str) -> dict:
    approval = approval_service.get_chain(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/approvals/{approval_id}/decision")
def decide_approval(approval_id: str, request: ApprovalDecisionRequest) -> dict:
    try:
        approval = approval_service.decide(approval_id, request.decision, request.comment)
    except ValueError as exc:
        message = str(exc)
        raise HTTPException(status_code=404 if "not found" in message.lower() else 400, detail=message) from exc
    if request.decision == "reject":
        approval_service.mark_rolled_back(approval_id, request.comment or "Rejected by user; no action was applied.")
        approval = approval_service.get_chain(approval_id) or approval
    return approval


@router.get("/learning/report")
def get_learning_report(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return learning_agent.report(workspace_id=resolved)


@router.get("/digital-twin/profile")
def get_digital_twin_profile(workspace_id: str | None = Query(default=None)) -> dict:
    return digital_twin_service.get_profile(workspace_id)


@router.post("/digital-twin/profile/refresh")
def refresh_digital_twin_profile(workspace_id: str | None = Query(default=None)) -> dict:
    return digital_twin_service.refresh_profile(workspace_id)


@router.patch("/digital-twin/profile")
def update_digital_twin_profile(request: DigitalTwinUpdateRequest) -> dict:
    return digital_twin_service.update_profile(
        workspace_id=request.workspace_id,
        updates=request.model_dump(exclude={"workspace_id"}, exclude_none=True),
    )


@router.get("/digital-twin/profile/export")
def export_digital_twin_profile(workspace_id: str | None = Query(default=None)) -> dict:
    return digital_twin_service.export_profile(workspace_id)


@router.post("/digital-twin/profile/reset")
def reset_digital_twin_profile(workspace_id: str | None = Query(default=None)) -> dict:
    return digital_twin_service.reset_profile(workspace_id)


@router.delete("/digital-twin/profile")
def delete_digital_twin_profile(workspace_id: str | None = Query(default=None)) -> dict:
    return digital_twin_service.delete_profile(workspace_id)


@router.get("/learning/prompt-versions")
def get_prompt_versions() -> list[dict]:
    return prompt_versions.list_versions()


@router.post("/learning/propose-prompt")
def propose_prompt(request: PromptProposalRequest) -> dict:
    return prompt_versions.propose(request.agent_name, request.reason, request.proposed_prompt)


@router.post("/learning/approve-prompt")
def approve_prompt(request: PromptDecisionRequest) -> dict:
    try:
        return prompt_versions.set_status(request.agent_name, request.version_id, "active")
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/learning/reject-prompt")
def reject_prompt(request: PromptDecisionRequest) -> dict:
    try:
        return prompt_versions.set_status(request.agent_name, request.version_id, "rejected")
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/learning/rollback-prompt")
def rollback_prompt(request: PromptDecisionRequest) -> dict:
    try:
        return prompt_versions.rollback(request.agent_name, request.version_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/analytics")
def get_analytics(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    runs = filter_by_workspace(storage.read_list("agent_analytics.json"), resolved)
    feedback = filter_by_workspace(storage.read_list("feedback.json"), resolved)
    goals = filter_by_workspace(storage.read_list("goals.json"), resolved)
    task_graphs = filter_by_workspace(storage.read_list("task_graphs.json"), resolved)
    custom_agents = filter_by_workspace(storage.read_list("custom_agents.json"), resolved)
    files = filter_by_workspace(storage.read_list("files.json"), resolved)
    recordings = filter_by_workspace(storage.read_list("recordings.json"), resolved)
    total_runs = len(runs)
    scores = [item.get("overall_judge_score", 0) for item in runs if item.get("overall_judge_score") is not None]
    latencies = [item.get("latency_ms", 0) for item in runs if item.get("latency_ms") is not None]
    task_counts = Counter(item.get("task_type", "unknown") for item in runs)
    agent_counts = Counter(agent for item in runs for agent in item.get("agents_used", []))
    feedback_counts = Counter(item.get("rating", "unknown") for item in feedback)
    goal_tasks = [task for graph in task_graphs for task in graph.get("tasks", [])]
    completed_goal_tasks = sum(1 for task in goal_tasks if task.get("status") == "done")
    active_goals = [goal for goal in goals if goal.get("status") == "active"]
    completed_goals = [goal for goal in goals if goal.get("status") == "completed"]
    custom_agent_counts = Counter(item.get("custom_agent_name") for item in runs if item.get("custom_agent_used"))
    linear_links = filter_by_workspace(storage.read_list("linear_links.json"), resolved)
    linear_runs = [item for item in runs if item.get("task_type") == "linear_task"]
    autopilot_summary = autopilot_service.summary(workspace_id=resolved)
    return {
        "total_runs": total_runs,
        "workspace_id": resolved,
        "average_judge_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "average_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
        "most_common_task_type": task_counts.most_common(1)[0][0] if task_counts else None,
        "most_used_agents": [{"agent_name": name, "count": count} for name, count in agent_counts.most_common(8)],
        "fallback_count": sum(1 for item in runs if item.get("fallback_used")),
        "file_task_count": sum(1 for item in runs if item.get("file_context_used")),
        "recording_task_count": sum(1 for item in runs if item.get("recording_context_used")),
        "image_task_count": sum(1 for item in runs if item.get("image_task")),
        "total_goals": len(goals),
        "active_goals": len(active_goals),
        "completed_goals": len(completed_goals),
        "total_goal_tasks": len(goal_tasks),
        "completed_goal_tasks": completed_goal_tasks,
        "blocked_goal_tasks": sum(1 for task in goal_tasks if task.get("status") == "blocked"),
        "custom_agents_count": len([item for item in custom_agents if item.get("enabled", True)]),
        "files_count": len(files),
        "recordings_count": len(recordings),
        "most_used_custom_agent": custom_agent_counts.most_common(1)[0][0] if custom_agent_counts else None,
        "task_completion_rate": round((completed_goal_tasks / len(goal_tasks)) * 100, 2) if goal_tasks else 0,
        "goal_success_rate": round((len(completed_goals) / len(goals)) * 100, 2) if goals else 0,
        "feedback_summary": {
            "helpful": feedback_counts.get("helpful", 0),
            "not_helpful": feedback_counts.get("not_helpful", 0),
            "saved": feedback_counts.get("saved", 0),
            "total": len(feedback),
        },
        "linear_issues_synced": len(linear_links),
        "linear_tasks_selected": sum(1 for item in linear_links if item.get("status") == "selected"),
        "linear_tasks_completed": sum(1 for item in linear_links if item.get("status") == "completed"),
        "linear_linked_commits": sum(len(item.get("commits", [])) for item in linear_links),
        "linear_pushes": sum(len(item.get("pushes", [])) for item in linear_links),
        "linear_failures": sum(1 for item in linear_links if item.get("status") == "failed"),
        "linear_task_runs": len(linear_runs),
        **autopilot_summary,
        **agent_department_service.analytics_summary(),
        "recent_runs": list(reversed(runs[-10:])),
    }


@router.get("/evaluation/benchmarks")
def get_evaluation_benchmarks(task_type: str | None = Query(default=None)) -> dict:
    benchmarks = evaluation_lab_service.list_benchmarks(task_type=task_type)
    return {"benchmarks": benchmarks, "count": len(benchmarks)}


@router.post("/evaluation/runs")
def create_evaluation_run(request: EvaluationRunRequest) -> dict:
    resolved = workspace_service.resolve_workspace_id(request.workspace_id) if request.workspace_id else None
    try:
        return evaluation_lab_service.create_run(
            benchmark_id=request.benchmark_id,
            task_type=request.task_type,
            workspace_id=resolved,
            notes=request.notes,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/evaluation/runs")
def get_evaluation_runs(
    workspace_id: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    runs = evaluation_lab_service.list_runs(workspace_id=resolved, limit=limit)
    return {"workspace_id": resolved, "runs": runs, "count": len(runs)}


@router.get("/evaluation/dashboard")
def get_evaluation_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return evaluation_lab_service.dashboard(workspace_id=resolved)


@router.post("/evaluation/ab-tests")
def create_evaluation_ab_test(request: EvaluationABTestRequest) -> dict:
    resolved = workspace_service.resolve_workspace_id(request.workspace_id) if request.workspace_id else None
    return evaluation_lab_service.create_ab_test(
        name=request.name,
        variant_a=request.variant_a,
        variant_b=request.variant_b,
        metric=request.metric,
        workspace_id=resolved,
    )


@router.get("/evaluation/ab-tests")
def get_evaluation_ab_tests(
    workspace_id: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    records = evaluation_lab_service.list_ab_tests(workspace_id=resolved, limit=limit)
    return {"workspace_id": resolved, "ab_tests": records, "count": len(records)}


@router.get("/evaluation/regressions")
def get_evaluation_regressions(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return evaluation_lab_service.regressions(workspace_id=resolved)


@router.get("/evaluation/export")
def export_evaluation_results(
    workspace_id: str | None = Query(default=None),
    format: str = Query(default="json", pattern="^(json|csv)$"),
) -> PlainTextResponse:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    content = evaluation_lab_service.export(workspace_id=resolved, format=format)
    media_type = "application/json" if format == "json" else "text/csv"
    extension = "json" if format == "json" else "csv"
    return PlainTextResponse(
        content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="evolveagent-evaluation.{extension}"'},
    )


@router.get("/project-manager/timeline")
def get_project_timeline(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return project_manager_service.timeline(workspace_id=resolved)


@router.get("/project-manager/resources")
def get_project_resources(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return project_manager_service.resource_allocation(workspace_id=resolved)


@router.get("/project-manager/risks")
def get_project_risks(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return project_manager_service.risk_register(workspace_id=resolved)


@router.post("/project-manager/risks")
def create_project_risk(request: ProjectRiskRequest) -> dict:
    resolved = workspace_service.resolve_workspace_id(request.workspace_id) if request.workspace_id else None
    return project_manager_service.create_risk(
        title=request.title,
        description=request.description,
        severity=request.severity,
        mitigation=request.mitigation,
        goal_id=request.goal_id,
        workspace_id=resolved,
    )


@router.patch("/project-manager/risks/{risk_id}")
def update_project_risk(risk_id: str, request: ProjectRiskUpdateRequest) -> dict:
    try:
        return project_manager_service.update_risk(
            risk_id, request.model_dump(exclude_none=True)
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/project-manager/reports")
def get_project_reports(workspace_id: str | None = Query(default=None)) -> list[dict]:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return project_manager_service.list_status_reports(workspace_id=resolved)


@router.post("/project-manager/reports")
def generate_project_report(request: ProjectReportRequest) -> dict:
    resolved = workspace_service.resolve_workspace_id(request.workspace_id) if request.workspace_id else None
    return project_manager_service.generate_status_report(workspace_id=resolved)


@router.get("/project-manager/dashboard")
def get_project_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return project_manager_service.dashboard(workspace_id=resolved)


@router.get("/portfolio/dashboard")
def get_portfolio_dashboard() -> dict:
    return portfolio_service.dashboard()


@router.get("/portfolio/analytics")
def get_portfolio_analytics() -> dict:
    return portfolio_service.analytics()


@router.get("/portfolio/health")
def get_portfolio_health() -> dict:
    return portfolio_service.health()


@router.post("/portfolio/reports")
def generate_portfolio_report(request: PortfolioReportRequest | None = None) -> dict:
    return portfolio_service.generate_executive_summary()


@router.get("/portfolio/reports")
def get_portfolio_reports() -> list[dict]:
    return portfolio_service.list_reports()


@router.get("/portfolio/export")
def export_portfolio(format: str = Query(default="json", pattern="^(json|markdown)$")) -> PlainTextResponse:
    content = portfolio_service.export(format=format)
    media_type = "application/json" if format == "json" else "text/markdown"
    extension = "json" if format == "json" else "md"
    return PlainTextResponse(
        content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="evolveagent-portfolio.{extension}"'},
    )


@router.get("/os/installer")
def get_os_installer() -> dict:
    return platform_installer_service.installer()


@router.get("/os/plugin-sdk")
def get_os_plugin_sdk() -> dict:
    return plugin_sdk_service.sdk()


@router.post("/os/plugin-sdk/validate")
def validate_os_plugin_manifest(request: PluginManifestValidateRequest) -> dict:
    return plugin_sdk_service.validate(request.manifest)


@router.get("/os/sla")
def get_os_sla() -> dict:
    return sla_monitoring_service.sla()


@router.get("/os/scheduler")
def get_os_scheduler() -> dict:
    return os_scheduler_service.overview()


@router.get("/os/summary")
def get_os_summary() -> dict:
    installer = platform_installer_service.installer()
    sla = sla_monitoring_service.sla()
    scheduler = os_scheduler_service.overview()
    return {
        "platform": "EvolveAgent OS",
        "version": "v15.0",
        "positioning": (
            "EvolveAgent OS is a local-first, workspace-aware multi-agent AI platform with governed "
            "automation, plugins, analytics, evaluation, and portfolio management."
        ),
        "installer_readiness": installer["readiness"],
        "plugin_sdk": plugin_sdk_service.summary(),
        "sla_rating": sla["sla_rating"],
        "uptime_proxy_score": sla["uptime_proxy_score"],
        "scheduler_health": scheduler["scheduler_health"],
        "safety_notes": installer["safety_notes"],
    }


# ----------------------------------------------------------------------
# v16.0 Multi-Agent Organization (departments / managers / workers / reviewers / auditors)
# ----------------------------------------------------------------------
@router.get("/departments")
def list_departments(include_archived: bool = Query(default=False)) -> dict:
    departments = agent_department_service.list_departments(include_archived=include_archived)
    return {"departments": departments, "count": len(departments), **agent_department_service.analytics_summary()}


@router.post("/departments")
def create_department(request: DepartmentCreateRequest) -> dict:
    return agent_department_service.create_department(
        name=request.name,
        description=request.description,
        manager_agent=request.manager_agent,
        worker_agents=request.worker_agents,
        reviewer_agents=request.reviewer_agents,
        auditor_agents=request.auditor_agents,
        allowed_tools=request.allowed_tools,
        permission_level=request.permission_level,
    )


@router.get("/departments/templates")
def get_department_templates() -> dict:
    templates = agent_department_service.templates()
    return {"templates": templates, "count": len(templates)}


@router.post("/departments/templates/seed")
def seed_department_templates() -> dict:
    return agent_department_service.seed_templates()


@router.get("/departments/runs")
def list_department_runs() -> dict:
    runs = agent_department_service.list_runs()
    return {"runs": runs, "count": len(runs)}


@router.get("/departments/collaborations")
def list_department_collaborations() -> dict:
    collaborations = agent_department_service.list_collaborations()
    return {"collaborations": collaborations, "count": len(collaborations)}


@router.post("/departments/collaborations")
def create_department_collaboration(request: DepartmentCollaborationRequest) -> dict:
    return agent_department_service.plan_collaboration(
        goal=request.goal,
        departments=request.departments,
        lead_department=request.lead_department,
    )


@router.get("/departments/{department_id}")
def get_department(department_id: str) -> dict:
    department = agent_department_service.get_department(department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


@router.patch("/departments/{department_id}")
def update_department(department_id: str, request: DepartmentUpdateRequest) -> dict:
    try:
        return agent_department_service.update_department(department_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/departments/{department_id}")
def archive_department(department_id: str) -> dict:
    try:
        return agent_department_service.archive_department(department_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/departments/{department_id}/runs")
def create_department_run(department_id: str, request: DepartmentRunRequest) -> dict:
    try:
        return agent_department_service.plan_run(department_id, request.task)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


# ----------------------------------------------------------------------
# v18.0 Real Business Automation Layer (Business Operator)
# ----------------------------------------------------------------------
@router.get("/business/dashboard")
def get_business_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    return business_operator_service.dashboard(workspace_id)


@router.get("/business/leads")
def list_business_leads(workspace_id: str | None = Query(default=None)) -> dict:
    leads = business_operator_service.list_leads(workspace_id)
    return {"leads": leads, "count": len(leads)}


@router.post("/business/leads")
def create_business_lead(request: BusinessLeadCreateRequest) -> dict:
    return business_operator_service.create_lead(request.model_dump())


@router.patch("/business/leads/{lead_id}")
def update_business_lead(lead_id: str, request: BusinessLeadUpdateRequest) -> dict:
    try:
        return business_operator_service.update_lead(lead_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Lead not found") from error


@router.get("/business/support-cases")
def list_business_support_cases(workspace_id: str | None = Query(default=None)) -> dict:
    cases = business_operator_service.list_support_cases(workspace_id)
    return {"support_cases": cases, "count": len(cases)}


@router.post("/business/support-cases")
def create_business_support_case(request: BusinessSupportCaseCreateRequest) -> dict:
    return business_operator_service.create_support_case(request.model_dump())


@router.patch("/business/support-cases/{case_id}")
def update_business_support_case(case_id: str, request: BusinessSupportCaseUpdateRequest) -> dict:
    try:
        return business_operator_service.update_support_case(case_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Support case not found") from error


@router.get("/business/documents")
def list_business_documents(workspace_id: str | None = Query(default=None)) -> dict:
    documents = business_operator_service.list_documents(workspace_id)
    return {"documents": documents, "count": len(documents)}


@router.post("/business/documents")
def create_business_document(request: BusinessDocumentCreateRequest) -> dict:
    return business_operator_service.process_document(request.model_dump())


@router.patch("/business/documents/{document_id}")
def update_business_document(document_id: str, request: BusinessDocumentUpdateRequest) -> dict:
    try:
        return business_operator_service.update_document(document_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Document not found") from error


@router.get("/business/proposals")
def list_business_proposals(workspace_id: str | None = Query(default=None)) -> dict:
    proposals = business_operator_service.list_proposals(workspace_id)
    return {"proposals": proposals, "count": len(proposals)}


@router.post("/business/proposals")
def create_business_proposal(request: BusinessProposalCreateRequest) -> dict:
    return business_operator_service.create_proposal(request.model_dump())


@router.patch("/business/proposals/{proposal_id}")
def update_business_proposal(proposal_id: str, request: BusinessProposalUpdateRequest) -> dict:
    try:
        return business_operator_service.update_proposal(proposal_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Proposal not found") from error


@router.get("/business/marketing-calendar")
def list_business_marketing_items(workspace_id: str | None = Query(default=None)) -> dict:
    items = business_operator_service.list_marketing_items(workspace_id)
    return {"marketing_items": items, "count": len(items)}


@router.post("/business/marketing-calendar")
def create_business_marketing_item(request: BusinessMarketingItemCreateRequest) -> dict:
    return business_operator_service.create_marketing_item(request.model_dump())


@router.patch("/business/marketing-calendar/{item_id}")
def update_business_marketing_item(item_id: str, request: BusinessMarketingItemUpdateRequest) -> dict:
    try:
        return business_operator_service.update_marketing_item(item_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Marketing item not found") from error


# ----------------------------------------------------------------------
# v19.0 AI Chief of Staff
# ----------------------------------------------------------------------
@router.get("/chief-of-staff/dashboard")
def get_chief_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    return chief_of_staff_service.dashboard(workspace_id)


@router.post("/chief-of-staff/daily-plan")
def create_chief_daily_plan(request: ChiefPlanRequest | None = None) -> dict:
    workspace_id = request.workspace_id if request else None
    return chief_of_staff_service.generate_daily_plan(workspace_id)


@router.get("/chief-of-staff/daily-plans")
def list_chief_daily_plans(workspace_id: str | None = Query(default=None)) -> dict:
    plans = chief_of_staff_service.list_daily_plans(workspace_id)
    return {"daily_plans": plans, "count": len(plans)}


@router.post("/chief-of-staff/weekly-plan")
def create_chief_weekly_plan(request: ChiefPlanRequest | None = None) -> dict:
    workspace_id = request.workspace_id if request else None
    return chief_of_staff_service.generate_weekly_plan(workspace_id)


@router.get("/chief-of-staff/weekly-plans")
def list_chief_weekly_plans(workspace_id: str | None = Query(default=None)) -> dict:
    plans = chief_of_staff_service.list_weekly_plans(workspace_id)
    return {"weekly_plans": plans, "count": len(plans)}


@router.get("/chief-of-staff/priorities")
def get_chief_priorities(workspace_id: str | None = Query(default=None)) -> dict:
    items = chief_of_staff_service.rank_priorities(workspace_id, log=True)
    return {"priority_items": items, "count": len(items)}


@router.get("/chief-of-staff/followups")
def list_chief_followups(workspace_id: str | None = Query(default=None)) -> dict:
    followups = chief_of_staff_service.list_followups(workspace_id)
    overdue = chief_of_staff_service.overdue_followups(workspace_id)
    return {"followups": followups, "count": len(followups), "overdue_count": len(overdue)}


@router.post("/chief-of-staff/followups")
def create_chief_followup(request: ChiefFollowupCreateRequest) -> dict:
    return chief_of_staff_service.create_followup(request.model_dump())


@router.patch("/chief-of-staff/followups/{followup_id}")
def update_chief_followup(followup_id: str, request: ChiefFollowupUpdateRequest) -> dict:
    try:
        return chief_of_staff_service.update_followup(followup_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Follow-up not found") from error


# ----------------------------------------------------------------------
# v20.0 Autonomous Business Simulator
# ----------------------------------------------------------------------
@router.get("/business-simulator/dashboard")
def get_business_simulator_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    return business_simulator_service.dashboard(workspace_id)


@router.get("/business-simulator/scenarios")
def list_business_simulator_scenarios(workspace_id: str | None = Query(default=None)) -> dict:
    scenarios = business_simulator_service.list_scenarios(workspace_id)
    return {"scenarios": scenarios, "count": len(scenarios)}


@router.post("/business-simulator/scenarios")
def create_business_simulator_scenario(request: SimulationScenarioCreateRequest) -> dict:
    return business_simulator_service.create_scenario(request.model_dump())


@router.get("/business-simulator/results")
def list_business_simulator_results(workspace_id: str | None = Query(default=None)) -> dict:
    results = business_simulator_service.list_results(workspace_id)
    return {"results": results, "count": len(results)}


@router.get("/business-simulator/results/{result_id}")
def get_business_simulator_result(result_id: str) -> dict:
    result = business_simulator_service.get_result(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.get("/business-simulator/scenarios/{scenario_id}")
def get_business_simulator_scenario(scenario_id: str) -> dict:
    scenario = business_simulator_service.get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.patch("/business-simulator/scenarios/{scenario_id}")
def update_business_simulator_scenario(scenario_id: str, request: SimulationScenarioUpdateRequest) -> dict:
    try:
        return business_simulator_service.update_scenario(scenario_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Scenario not found") from error


@router.post("/business-simulator/scenarios/{scenario_id}/run")
def run_business_simulator_scenario(scenario_id: str) -> dict:
    try:
        return business_simulator_service.run_simulation(scenario_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Scenario not found") from error


# ----------------------------------------------------------------------
# v21.0 Multi-Modal Real-World Agent
# ----------------------------------------------------------------------
@router.get("/multimodal/dashboard")
def get_multimodal_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    return multimodal_agent_service.dashboard(workspace_id)


@router.get("/multimodal/items")
def list_multimodal_items(workspace_id: str | None = Query(default=None)) -> dict:
    items = multimodal_agent_service.list_items(workspace_id)
    return {"items": items, "count": len(items)}


@router.post("/multimodal/items")
def create_multimodal_item(request: MultimodalItemCreateRequest) -> dict:
    return multimodal_agent_service.create_item(request.model_dump())


@router.get("/multimodal/analyses")
def list_multimodal_analyses(workspace_id: str | None = Query(default=None)) -> dict:
    analyses = multimodal_agent_service.list_analyses(workspace_id)
    return {"analyses": analyses, "count": len(analyses)}


@router.post("/multimodal/items/{item_id}/analyze")
def analyze_multimodal_item(item_id: str, request: MultimodalAnalyzeRequest | None = None) -> dict:
    analysis_type = request.analysis_type if request else None
    try:
        return multimodal_agent_service.analyze_item(item_id, analysis_type)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Item not found") from error


@router.get("/governance")
def get_governance(workspace_id: str | None = Query(default=None)) -> dict:
    summary = governance_service.summary()
    if not workspace_id:
        return summary
    resolved = workspace_service.resolve_workspace_id(workspace_id)
    events = filter_by_workspace(storage.read_list("governance_log.json"), resolved)
    blocked = [event for event in events if event.get("blocked")]
    return {
        **summary,
        "workspace_id": resolved,
        "total_events": len(events),
        "blocked_actions": len(blocked),
        "recent_events": list(reversed(events[-20:])),
    }


@router.get("/compliance/summary")
def get_compliance_summary(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return compliance_service.compliance_report(resolved)


@router.get("/compliance/admin-console")
def get_compliance_admin_console(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return compliance_service.admin_summary(resolved)


@router.get("/compliance/audit-log")
def get_compliance_audit_log(
    workspace_id: str | None = Query(default=None),
    action_type: str | None = Query(default=None),
    blocked: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    events = compliance_service.audit_events(resolved, action_type=action_type, blocked=blocked, limit=limit)
    return {"workspace_id": resolved, "events": events, "count": len(events)}


@router.get("/compliance/export")
def export_compliance_report(
    workspace_id: str | None = Query(default=None),
    format: str = Query(default="markdown", pattern="^(markdown|json)$"),
) -> PlainTextResponse:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    content = compliance_service.export_report(resolved, format=format)
    media_type = "application/json" if format == "json" else "text/markdown"
    return PlainTextResponse(content, media_type=media_type)


@router.get("/compliance/retention-policies")
def get_retention_policies(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return compliance_service.retention_review(resolved)


@router.patch("/compliance/retention-policies/{collection}")
def update_retention_policy(collection: str, request: RetentionPolicyRequest) -> dict:
    if "/" in collection or "\\" in collection or not collection.endswith(".json"):
        raise HTTPException(status_code=400, detail="Collection must be a safe JSON filename.")
    return compliance_service.upsert_policy(collection, request.model_dump(exclude_none=True))


@router.post("/compliance/pii-scan")
def scan_pii(request: PiiScanRequest) -> dict:
    result = compliance_service.scan_pii(request.text, redact=request.redact)
    if result["pii_detected"]:
        governance_service.log_event(
            GovernanceEvent(
                task_type="compliance",
                agent_name="Compliance Service",
                action_type="pii_redaction",
                tool_used="ComplianceService",
                permission_level="read_only",
                approved=False,
                blocked=False,
                risk_score=35,
                reason=f"Detected PII-like values: {', '.join(result['detected_types'])}",
            )
        )
    return result


@router.post("/goals")
def create_goal(request: CreateGoalRequest) -> dict:
    workspace_id = workspace_service.resolve_workspace_id(request.workspace_id)
    if request.prompt:
        _, planner_result = master_agent.goal_planner.run(request.prompt)
        if request.title:
            planner_result["goal_title"] = request.title
        if request.description:
            planner_result["goal_summary"] = request.description
        goal, task_graph = goal_service.create_from_plan(
            planner_result,
            source_session_id=request.source_session_id,
            source_message_id=request.source_message_id,
            tags=request.tags,
            workspace_id=workspace_id,
        )
    elif request.title:
        goal, task_graph = goal_service.create_manual(
            request.title,
            request.description or "",
            tags=request.tags,
            workspace_id=workspace_id,
        )
    else:
        raise HTTPException(status_code=422, detail="Provide either prompt or title.")
    governance_service.log_event(
        GovernanceEvent(
            run_id=None,
            session_id=request.source_session_id,
            workspace_id=workspace_id,
            task_type="goal_planning",
            agent_name="Mission Control",
            action_type="goal_created",
            tool_used="GoalService",
            permission_level="plan_only",
            approved=False,
            blocked=False,
            risk_score=0,
            reason=f"Goal {goal.goal_id} was created.",
        )
    )
    return {"goal": goal.model_dump(), "task_graph": task_graph.model_dump()}


@router.get("/goals")
def list_goals(workspace_id: str | None = Query(default=None)) -> list[dict]:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return goal_service.list_goals(workspace_id=resolved)


@router.get("/goals/{goal_id}")
def get_goal(goal_id: str) -> dict:
    result = goal_service.get_goal(goal_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    goal, task_graph = result
    return {"goal": goal, "task_graph": task_graph}


@router.patch("/goals/{goal_id}")
def update_goal(goal_id: str, request: UpdateGoalRequest) -> dict:
    goal = goal_service.update_goal(goal_id, request.model_dump(exclude_unset=True))
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.delete("/goals/{goal_id}")
def delete_goal(goal_id: str) -> dict:
    goal = goal_service.archive_goal(goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"archived": True, "goal": goal}


@router.post("/goals/{goal_id}/tasks")
def add_goal_task(goal_id: str, request: CreateGoalTaskRequest) -> dict:
    task = goal_service.add_task(goal_id, request.model_dump())
    if task is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return task.model_dump()


@router.patch("/goals/{goal_id}/tasks/{task_id}")
def update_goal_task(goal_id: str, task_id: str, request: UpdateGoalTaskRequest) -> dict:
    updates = request.model_dump(exclude_unset=True)
    task = goal_service.update_task(goal_id, task_id, updates)
    if task is None:
        raise HTTPException(status_code=404, detail="Goal task not found")
    linear_sync = None
    if updates.get("status") in {"done", "completed"}:
        try:
            linear_sync = linear_orchestration.on_goal_task_updated(
                goal_id,
                task_id,
                updates,
                completion_note=updates.get("completion_note"),
            )
        except LinearServiceError as error:
            linear_sync = {"completed": False, "error": str(error)}
    payload = task.model_dump()
    if linear_sync is not None:
        payload["linear_sync"] = linear_sync
    return payload


@router.post("/goals/{goal_id}/tasks/{task_id}/run", response_model=RunResponse)
def run_goal_task(goal_id: str, task_id: str) -> RunResponse:
    task = goal_service.get_task(goal_id, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Goal task not found")
    goal_service.update_task(goal_id, task_id, {"status": "running"})
    goal_record, _ = goal_service.get_goal(goal_id) or ({}, {})
    request = RunRequest(
        user_input=f"{task.get('title')}\n\n{task.get('description', '')}".strip(),
        task_type="auto",
        workspace_id=goal_record.get("workspace_id"),
        goal_id=goal_id,
        task_id=task_id,
    )
    response = master_agent.run(request)
    final_status = "needs_approval" if response.requires_approval else "done"
    goal_service.update_task(
        goal_id,
        task_id,
        {
            "status": final_status,
            "last_run_id": response.run_id,
            "last_result_summary": response.final_output[:240],
        },
    )
    if final_status == "done":
        try:
            linear_orchestration.on_goal_task_updated(goal_id, task_id, {"status": "done"})
        except LinearServiceError:
            pass
    governance_service.log_event(
        GovernanceEvent(
            run_id=response.run_id,
            session_id=response.session_id,
            workspace_id=response.workspace_id,
            task_type=response.task_type,
            agent_name="Mission Control",
            action_type="goal_task_run",
            tool_used="GoalService",
            permission_level="plan_only",
            approved=False,
            blocked=False,
            risk_score=response.security_report.risk_score,
            reason=f"Ran goal task {task_id} through the existing agent workflow.",
        )
    )
    return response


@router.get("/agents/templates")
def list_agent_templates() -> list[dict]:
    return custom_agent_service.templates()


@router.post("/agents/custom")
def create_custom_agent(request: CreateCustomAgentRequest) -> dict:
    data = request.model_dump()
    data["workspace_id"] = workspace_service.resolve_workspace_id(data.get("workspace_id"))
    agent = custom_agent_service.create(data)
    governance_service.log_event(
        GovernanceEvent(
            workspace_id=agent.workspace_id,
            agent_name="Custom Agent Builder",
            action_type="custom_agent_created",
            tool_used="CustomAgentService",
            permission_level=agent.approval_level,
            approved=False,
            blocked=False,
            reason=f"Custom agent {agent.name} was created.",
        )
    )
    return agent.model_dump()


@router.get("/agents/custom")
def list_custom_agents(workspace_id: str | None = Query(default=None)) -> list[dict]:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return custom_agent_service.list(workspace_id=resolved)


@router.get("/agents/custom/{agent_id}")
def get_custom_agent(agent_id: str) -> dict:
    agent = custom_agent_service.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Custom agent not found")
    return agent


@router.patch("/agents/custom/{agent_id}")
def update_custom_agent(agent_id: str, request: UpdateCustomAgentRequest) -> dict:
    agent = custom_agent_service.update(agent_id, request.model_dump(exclude_unset=True))
    if agent is None:
        raise HTTPException(status_code=404, detail="Custom agent not found")
    governance_service.log_event(
        GovernanceEvent(
            agent_name="Custom Agent Builder",
            workspace_id=agent.get("workspace_id"),
            action_type="custom_agent_edited",
            tool_used="CustomAgentService",
            permission_level=agent.get("approval_level", "read_only"),
            approved=False,
            blocked=False,
            reason=f"Custom agent {agent.get('name')} was updated.",
        )
    )
    return agent


@router.delete("/agents/custom/{agent_id}")
def delete_custom_agent(agent_id: str) -> dict:
    agent = custom_agent_service.delete(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Custom agent not found")
    return {"disabled": True, "agent": agent}


@router.get("/agent-marketplace/dashboard")
def get_agent_marketplace_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    return agent_marketplace_service.dashboard(workspace_id=workspace_id)


@router.get("/agent-marketplace/packs")
def list_agent_marketplace_packs() -> list[dict]:
    return agent_marketplace_service.list_packs()


@router.get("/agent-marketplace/packs/{pack_id}")
def get_agent_marketplace_pack(pack_id: str) -> dict:
    pack = agent_marketplace_service.get_pack(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="Agent skill pack not found")
    return pack


@router.get("/agent-marketplace/permission-profiles")
def list_agent_marketplace_permission_profiles() -> list[dict]:
    return agent_marketplace_service.permission_profiles()


@router.get("/agent-marketplace/teams")
def list_agent_marketplace_teams(workspace_id: str | None = Query(default=None)) -> list[dict]:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return agent_marketplace_service.list_teams(workspace_id=resolved)


@router.post("/agent-marketplace/teams")
def create_agent_marketplace_team(request: AgentTeamCreateRequest) -> dict:
    return agent_marketplace_service.create_team(request.model_dump())


@router.patch("/agent-marketplace/teams/{team_id}")
def update_agent_marketplace_team(team_id: str, request: AgentTeamUpdateRequest) -> dict:
    team = agent_marketplace_service.update_team(team_id, request.model_dump(exclude_unset=True))
    if team is None:
        raise HTTPException(status_code=404, detail="Agent team not found")
    return team


@router.post("/agent-marketplace/teams/import")
def import_agent_marketplace_team(request: AgentTeamImportRequest) -> dict:
    return agent_marketplace_service.import_team(request.payload, workspace_id=request.workspace_id)


@router.get("/agent-marketplace/teams/{team_id}/export")
def export_agent_marketplace_team(team_id: str) -> dict:
    exported = agent_marketplace_service.export_team(team_id)
    if exported is None:
        raise HTTPException(status_code=404, detail="Agent team not found")
    return exported


@router.post("/agent-marketplace/teams/{team_id}/rate")
def rate_agent_marketplace_team(team_id: str, request: AgentTeamRatingRequest) -> dict:
    try:
        return agent_marketplace_service.rate_team(
            team_id=team_id,
            rating=request.rating,
            review=request.review or "",
            workspace_id=request.workspace_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/agent-marketplace/packs/{pack_id}/install")
def install_agent_marketplace_pack(pack_id: str, request: AgentPackInstallRequest) -> dict:
    try:
        return agent_marketplace_service.install_pack(pack_id=pack_id, workspace_id=request.workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/providers/status", response_model=ProviderStatus)
def get_provider_status() -> ProviderStatus:
    return llm_router.status()


@router.post("/providers/smoke-test")
def provider_smoke_test(request: ProviderSmokeTestRequest) -> dict:
    return llm_router.smoke_test(provider=request.provider, live=request.live)


@router.get("/images/status")
def get_image_provider_status() -> dict:
    return image_service.status()


@router.post("/images/smoke-test")
def image_smoke_test(request: ImageSmokeTestRequest) -> dict:
    return image_service.smoke_test(live=request.live, prompt=request.prompt)


@router.get("/transcription/status")
def get_transcription_provider_status() -> dict:
    return recording_service.transcription.status()


@router.post("/transcription/smoke-test")
def transcription_smoke_test(request: TranscriptionSmokeTestRequest) -> dict:
    return recording_service.transcription.smoke_test(live=request.live)


@router.get("/real-api/summary")
def get_real_api_summary() -> dict:
    return real_api_control_service.summary()


@router.get("/real-api/live-warning/{capability}")
def get_real_api_live_warning(capability: str) -> dict:
    return real_api_control_service.live_warning(capability)


@router.post("/real-api/decode-error")
def decode_real_api_error(request: RealApiErrorDecodeRequest) -> dict:
    return real_api_control_service.decode_error(request.error)


@router.get("/chats")
def get_chats(workspace_id: str | None = Query(default=None)) -> list[dict]:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    sessions = filter_by_workspace(storage.read_list("chat_sessions.json"), resolved)
    messages = filter_by_workspace(storage.read_list("messages.json"), resolved)
    summaries = [
        {
            "session_id": session.get("session_id"),
            "workspace_id": session.get("workspace_id"),
            "title": session.get("title", "Untitled chat"),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at"),
            "message_count": len([message for message in messages if message.get("session_id") == session.get("session_id")])
            or len(session.get("messages", [])),
        }
        for session in sessions
    ]
    return sorted(summaries, key=lambda item: item.get("updated_at") or "", reverse=True)


@router.post("/chats")
def create_chat(request: CreateChatRequest | None = None) -> dict:
    now = datetime.now(UTC).isoformat()
    workspace_id = workspace_service.resolve_workspace_id(request.workspace_id if request else None)
    session = {
        "session_id": str(uuid4()),
        "workspace_id": workspace_id,
        "title": (request.title.strip() if request and request.title else "New Chat"),
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }
    sessions = storage.read_list("chat_sessions.json")
    sessions.append(session)
    storage.write_list("chat_sessions.json", sessions)
    return session


@router.get("/chats/{session_id}")
def get_chat(session_id: str) -> dict:
    session = next((item for item in storage.read_list("chat_sessions.json") if item.get("session_id") == session_id), None)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    messages = [
        message
        for message in storage.read_list("messages.json")
        if message.get("session_id") == session_id
    ]
    if not messages:
        messages = session.get("messages", [])
    session = {**session, "messages": sorted(messages, key=lambda item: item.get("created_at") or "")}
    return session


@router.patch("/chats/{session_id}")
def rename_chat(session_id: str, request: RenameChatRequest) -> dict:
    sessions = storage.read_list("chat_sessions.json")
    session = next((item for item in sessions if item.get("session_id") == session_id), None)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    session["title"] = request.title.strip()
    storage.write_list("chat_sessions.json", sessions)
    return session


@router.delete("/chats/{session_id}")
def delete_chat(session_id: str) -> dict[str, bool]:
    sessions = storage.read_list("chat_sessions.json")
    next_sessions = [item for item in sessions if item.get("session_id") != session_id]
    if len(next_sessions) == len(sessions):
        raise HTTPException(status_code=404, detail="Chat session not found")
    storage.write_list("chat_sessions.json", next_sessions)
    next_messages = [item for item in storage.read_list("messages.json") if item.get("session_id") != session_id]
    storage.write_list("messages.json", next_messages)
    return {"deleted": True}


@router.delete("/chats/{session_id}/messages/{message_id}")
def delete_message(session_id: str, message_id: str) -> dict[str, bool]:
    sessions = storage.read_list("chat_sessions.json")
    session = next((item for item in sessions if item.get("session_id") == session_id), None)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = storage.read_list("messages.json")
    next_messages = [
        item
        for item in messages
        if not (item.get("session_id") == session_id and item.get("message_id", item.get("id")) == message_id)
    ]
    embedded_messages = session.get("messages", [])
    next_embedded = [
        item for item in embedded_messages if item.get("message_id", item.get("id")) != message_id
    ]

    if len(next_messages) == len(messages) and len(next_embedded) == len(embedded_messages):
        raise HTTPException(status_code=404, detail="Message not found")

    session["messages"] = next_embedded
    session["updated_at"] = datetime.now(UTC).isoformat()
    storage.write_list("chat_sessions.json", sessions)
    storage.write_list("messages.json", next_messages)
    return {"deleted": True}


@router.get("/linear/status")
def get_linear_status() -> dict:
    return linear_service.get_linear_config()


@router.get("/linear/issues")
def list_linear_issues(status: str | None = Query(default=None)) -> list[dict]:
    try:
        return linear_service.list_linear_issues(status_filter=status)
    except LinearServiceError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/linear/issues/{issue_id}")
def get_linear_issue(issue_id: str) -> dict:
    try:
        issue = linear_service.get_linear_issue(issue_id)
        link = linear_link_service.get_link_by_issue(issue_id)
        return {"issue": issue, "link": link}
    except LinearServiceError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/linear/issues/{issue_id}/sync")
def sync_linear_issue(
    issue_id: str,
    workspace_id: str | None = Query(default=None),
) -> dict:
    try:
        return linear_orchestration.sync_issue(issue_id, workspace_id=workspace_id)
    except LinearServiceError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/linear/issues/{issue_id}/select")
def select_linear_issue(
    issue_id: str,
    workspace_id: str | None = Query(default=None),
) -> dict:
    try:
        return linear_orchestration.select_issue(issue_id, workspace_id=workspace_id)
    except LinearServiceError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/linear/issues/{issue_id}/run")
def run_linear_issue(
    issue_id: str,
    workspace_id: str | None = Query(default=None),
) -> dict:
    try:
        return linear_orchestration.run_issue(issue_id, workspace_id=workspace_id)
    except LinearServiceError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/linear/issues/{issue_id}/comment")
def comment_linear_issue(issue_id: str, request: LinearCommentRequest) -> dict:
    try:
        return linear_orchestration.add_comment(issue_id, request.body)
    except LinearServiceError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/linear/issues/{issue_id}/cursor-handoff")
def get_linear_cursor_handoff(issue_id: str) -> dict:
    try:
        return linear_orchestration.get_cursor_handoff(issue_id)
    except LinearServiceError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/linear/issues/{issue_id}/cursor-verify")
def verify_linear_cursor_work(issue_id: str, request: LinearCursorVerifyRequest | None = None) -> dict:
    payload = request or LinearCursorVerifyRequest()
    try:
        return linear_orchestration.verify_cursor_work(
            issue_id,
            completion_note=payload.completion_note,
            auto_commit=payload.auto_commit,
        )
    except LinearServiceError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/linear/issues/{issue_id}/complete")
def complete_linear_issue(issue_id: str) -> dict:
    try:
        return linear_orchestration.complete_linear_issue(issue_id)
    except LinearServiceError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/linear/links")
def list_linear_links(workspace_id: str | None = Query(default=None)) -> list[dict]:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return linear_link_service.list_links(resolved)


@router.get("/linear/poll/status")
def get_linear_poll_status() -> dict:
    return linear_poll_worker.status()


@router.post("/linear/poll/run-once")
def run_linear_poll_once() -> dict:
    processed = linear_poll_worker.poll_once()
    return {"processed": processed, **linear_poll_worker.status()}


@router.post("/linear/issues/{issue_id}/codex-run")
def run_codex_for_linear_issue(issue_id: str) -> dict:
    try:
        return codex_worker_service.run_for_issue(issue_id)
    except CodexWorkerError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except LinearServiceError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/codex/jobs")
def list_codex_jobs() -> list[dict]:
    return codex_job_service.list_jobs()


@router.get("/codex/jobs/{job_id}")
def get_codex_job(job_id: str) -> dict:
    job = codex_job_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Codex job not found")
    return job
