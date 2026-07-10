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
    IndustryModeUpdateRequest,
    IndustryModeRunRequest,
    AgentContractCreateRequest,
    AgentContractUpdateRequest,
    AgentHandoffCreateRequest,
    SelfHealingCheckRequest,
    SelfHealingVerifyRequest,
    CompanyStrategyRequest,
    CompanyDecisionRequest,
    CompanyReportRequest,
    DeviceSessionCreateRequest,
    DevicePlanRequest,
    DeviceConfirmActionRequest,
    TrainingDatasetCreateRequest,
    TrainingExampleCreateRequest,
    TrainingExampleUpdateRequest,
    TrainingRunCreateRequest,
    TrainingComparisonRequest,
    AvatarPersonaUpdateRequest,
    AvatarVoiceSettingsUpdateRequest,
    AvatarMeetingSessionRequest,
    AvatarConsentRequest,
    AvatarImageRequest,
    LifeScheduleCreateRequest,
    LifeTaskCreateRequest,
    LifeTaskUpdateRequest,
    LifeReminderCreateRequest,
    LifeDeadlineCreateRequest,
    LifeDailyPlanRequest,
    UniversalSessionCreateRequest,
    UniversalWorkflowCreateRequest,
    UniversalActionDecisionRequest,
    UniversalHandoffCreateRequest,
    SaaSProjectCreateRequest,
    SaaSFeedbackCreateRequest,
    BusinessWorkflowCreateRequest,
    BusinessReportCreateRequest,
    BusinessApprovalCreateRequest,
    BusinessApprovalDecisionRequest,
    CompliancePolicyCreateRequest,
    CompliancePolicyUpdateRequest,
    ComplianceScanRequest,
    ComplianceContractReviewRequest,
    ComplianceChecklistRequest,
    ComplianceAuditPackageRequest,
    ExecutiveBoardSessionCreateRequest,
    ExecutiveBoardVoteRequest,
    InnovationResearchRequest,
    InnovationCompetitorRequest,
    InnovationTrendRequest,
    InnovationIdeaRequest,
    InnovationExperimentRequest,
    InnovationPrototypeRequest,
    InnovationReportRequest,
    SimulationWorldCreateRequest,
    SimulationPersonaCreateRequest,
    SimWorldScenarioCreateRequest,
    SimulationCompareRequest,
    SimulationReportRequest,
    OrganizationCreateRequest,
    OrganizationMemberCreateRequest,
    OrganizationMemberUpdateRequest,
    OrganizationRoleCreateRequest,
    OrganizationWorkspaceLinkRequest,
    HardwareDeviceCreateRequest,
    HardwareDeviceUpdateRequest,
    CompanionSettingsUpdateRequest,
    CompanionReadinessCheckRequest,
    CompanionSessionCreateRequest,
    MCPConnectorCreateRequest,
    MCPConnectorUpdateRequest,
    MCPPlanActionRequest,
    MCPExecuteRequest,
    MCPPolicyCreateRequest,
    MCPPolicyUpdateRequest,
    MCPPolicyEvaluateRequest,
    MCPReplayRequest,
    MCPSecretRefCreateRequest,
    MCPSecretRefUpdateRequest,
    ApprovalDecisionRequest,
    UsageRecordRequest,
    UsageBudgetRequest,
    RetrievalIndexRequest,
    RetrievalQueryRequest,
    EvalSuiteCreateRequest,
    PlaybookCreateRequest,
    MCPSuggestRequest,
    MasterAgentRouteRequest,
    GitDiscoverRequest,
    AgentProfileRequest,
    AgentTestRequest,
    AgentImportRequest,
    AgentRollbackRequest,
    VoiceSettingsRequest,
    VoiceActivityRequest,
    DurableWorkflowDefRequest,
    DurableWorkflowStartRequest,
    WorkflowApprovalRequest,
    MarketplacePublishRequest,
    DesignAnalyzeRequest,
    RepoSearchRequest,
    AdaptiveIngestRequest,
    MasterRouteFeedbackRequest,
    SettingsUpdateRequest,
    SettingsImportRequest,
    ProviderControlUpdateRequest,
    ContextPlanRequest,
    WorkflowRecommendRequest,
    DocCompareRequest,
    AtsScoreRequest,
    DocTextRequest,
    DocQARequest,
    CodeAnalyzeRequest,
    CodeTextRequest,
    ResearchSourcesRequest,
    ResearchBriefRequest,
    ResearchTextRequest,
    MeetingAnalyzeRequest,
    MeetingToGoalRequest,
    CollaborationRequest,
    PermissionProfileRequest,
    PermissionEvaluateRequest,
    RedactionPreviewRequest,
    ImportPreviewRequest,
    ImportCommitRequest,
    ExportRequest,
    ExportPackageRequest,
    PluginRegisterRequest,
    PluginToggleRequest,
    QARecordRequest,
    PRSummaryRequest,
    ReleaseNotesRequest,
    WorkspaceTemplateCreateRequest,
    WorkspaceTemplateInstantiateRequest,
    ScheduledTaskCreateRequest,
    ScheduledTaskToggleRequest,
    DataImportRequest,
    TeamMemberCreateRequest,
    TeamMemberUpdateRequest,
    TeamAssignmentCreateRequest,
    TeamAssignmentUpdateRequest,
    TeamSprintCreateRequest,
    TeamSprintReviewRequest,
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
from app.services.industry_mode_service import IndustryModeService
from app.services.agent_network_service import AgentNetworkService
from app.services.self_healing_service import SelfHealingService
from app.services.company_brain_service import CompanyBrainService
from app.services.device_operator_service import DeviceOperatorService
from app.services.training_lab_service import TrainingLabService
from app.services.avatar_persona_service import AvatarPersonaService
from app.services.life_os_service import LifeOSService
from app.services.universal_operator_service import UniversalOperatorService
from app.services.saas_builder_service import SaaSBuilderService
from app.services.business_operator_advanced_service import BusinessOperatorAdvancedService
from app.services.compliance_intelligence_service import ComplianceIntelligenceService
from app.services.executive_board_service import ExecutiveBoardService
from app.services.innovation_lab_service import InnovationLabService
from app.services.simulation_world_service import SimulationWorldService
from app.services.organization_os_service import OrganizationOSService
from app.services.hardware_companion_service import HardwareCompanionService
from app.services.operating_layer_service import OperatingLayerService
from app.services.mcp_connector_service import MCPConnectorService
from app.services.mcp_suggestion_service import MCPSuggestionService
from app.services.mcp_policy_service import MCPPolicyService
from app.services.mcp_execution_service import MCPExecutionService
from app.services.mcp_approvals_inbox_service import MCPApprovalsInboxService
from app.services.mcp_audit_service import MCPAuditService
from app.services.mcp_secret_registry_service import MCPSecretRegistryService
from app.services.unified_approvals_service import UnifiedApprovalsService
from app.services.health_monitor_service import HealthMonitorService
from app.services.usage_ledger_service import UsageLedgerService
from app.services.local_retrieval_service import LocalRetrievalService
from app.services.eval_harness_service import EvalHarnessService
from app.services.playbook_library_service import PlaybookLibraryService
from app.services.operating_layer_v2_service import OperatingLayerV2Service
from app.services.notifications_center_service import NotificationsCenterService
from app.services.workspace_templates_service import WorkspaceTemplatesService
from app.services.scheduled_tasks_service import ScheduledTasksService
from app.services.data_export_service import DataExportService
from app.services.evolveagent_os2_service import EvolveAgentOS2Service
from app.services.master_agent_service import MasterAgentService
from app.services.git_discovery_service import GitDiscoveryService
from app.services.agent_profile_service import AgentProfileService
from app.services.voice_console_service import VoiceConsoleService
from app.services.durable_workflow_service import DurableWorkflowService
from app.services.marketplace_hub_service import MarketplaceHubService
from app.services.design_agent_service import DesignAgentService
from app.services.git_reader_service import GitReaderService
from app.services.github_connector_service import GitHubConnectorService
from app.services.mcp_github_adapter import MCPGitHubAdapter
from app.services.repo_finder_service import RepoFinderService
from app.services.code_writer_service import CodeWriterService
from app.services.adaptive_learning_service import AdaptiveLearningService
from app.services.home_dashboard_service import HomeDashboardService
from app.services.global_search_service import GlobalSearchService
from app.services.activity_timeline_service import ActivityTimelineService
from app.services.dashboard_home_service import DashboardHomeService
from app.services.feature_registry_service import FeatureRegistryService
from app.services.demo_service import DemoService
from app.services.settings_service import SettingsService
from app.services.provider_control_service import ProviderControlService
from app.services.notifications_inbox_service import NotificationsInboxService
from app.services.workspace_os_service import WorkspaceOSService
from app.services.smart_context_service import SmartContextService
from app.services.agent_quality_service import AgentQualityService
from app.services.workflow_recommendation_service import WorkflowRecommendationService
from app.services.personal_productivity_service import PersonalProductivityService
from app.services.document_intelligence_service import DocumentIntelligenceService
from app.services.code_intelligence_service import CodeIntelligenceService
from app.services.research_agent_service import ResearchAgentService
from app.services.business_intelligence_service import BusinessIntelligenceService
from app.services.meeting_intelligence_service import MeetingIntelligenceService
from app.services.agent_collaboration_service import AgentCollaborationService
from app.services.permission_profiles_service import PermissionProfilesService
from app.services.governance_console_service import GovernanceConsoleService
from app.services.data_manager_service import DataManagerService
from app.services.import_center_service import ImportCenterService
from app.services.export_center_service import ExportCenterService
from app.services.plugin_marketplace_service import PluginMarketplaceService
from app.services.integration_hub_service import IntegrationHubService
from app.services.qa_center_service import QACenterService
from app.services.release_manager_service import ReleaseManagerService
from app.services.product_launch_service import ProductLaunchService
from app.services.team_manager_service import TeamManagerService
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
industry_mode_service = IndustryModeService(storage, governance_service)
agent_network_service = AgentNetworkService(storage, governance_service)
self_healing_service = SelfHealingService(storage, governance_service, safe_command_runner)
company_brain_service = CompanyBrainService(storage, governance_service)
device_operator_service = DeviceOperatorService(storage, governance_service)
training_lab_service = TrainingLabService(storage, governance_service, SecretScanner())
avatar_persona_service = AvatarPersonaService(storage, governance_service, image_service)
life_os_service = LifeOSService(storage, governance_service)
universal_operator_service = UniversalOperatorService(storage, governance_service)
saas_builder_service = SaaSBuilderService(storage, governance_service)
business_operator_advanced_service = BusinessOperatorAdvancedService(storage, governance_service)
compliance_intelligence_service = ComplianceIntelligenceService(storage, governance_service, SecretScanner())
executive_board_service = ExecutiveBoardService(storage, governance_service)
innovation_lab_service = InnovationLabService(storage, governance_service)
simulation_world_service = SimulationWorldService(storage, governance_service)
organization_os_service = OrganizationOSService(storage, governance_service)
hardware_companion_service = HardwareCompanionService(storage, governance_service)
operating_layer_service = OperatingLayerService(storage, governance_service)
mcp_policy_service = MCPPolicyService(storage, governance_service)
mcp_connector_service = MCPConnectorService(storage, governance_service, policy_service=mcp_policy_service)
mcp_suggestion_service = MCPSuggestionService(mcp_connector_service, governance_service)
mcp_execution_service = MCPExecutionService(storage, governance_service, mcp_connector_service)
mcp_approvals_inbox_service = MCPApprovalsInboxService(mcp_execution_service, mcp_connector_service)
mcp_audit_service = MCPAuditService(storage, governance_service, mcp_connector_service, mcp_execution_service)
mcp_secret_registry_service = MCPSecretRegistryService(storage, governance_service)
unified_approvals_service = UnifiedApprovalsService(mcp_execution_service, business_operator_advanced_service)
health_monitor_service = HealthMonitorService(storage, governance_service)
usage_ledger_service = UsageLedgerService(storage, governance_service)
local_retrieval_service = LocalRetrievalService(storage, governance_service)
eval_harness_service = EvalHarnessService(storage, governance_service)
playbook_library_service = PlaybookLibraryService(storage, governance_service)
operating_layer_v2_service = OperatingLayerV2Service(storage, governance_service, health_monitor_service)
notifications_center_service = NotificationsCenterService(storage, governance_service, health_monitor_service)
workspace_templates_service = WorkspaceTemplatesService(storage, governance_service, workspace_service)
data_export_service = DataExportService(storage, governance_service)
evolveagent_os2_service = EvolveAgentOS2Service(storage, governance_service, operating_layer_v2_service, health_monitor_service)
master_agent_service = MasterAgentService(storage, governance_service, mcp_suggestion_service, kernel_service.run_workflow)
git_discovery_service = GitDiscoveryService(storage, governance_service)
agent_profile_service = AgentProfileService(storage, governance_service)
voice_console_service = VoiceConsoleService(storage, governance_service)
durable_workflow_service = DurableWorkflowService(storage, governance_service, agent_scheduler=agent_scheduler, approvals=approval_service)
# v120: scheduled tasks can start a REAL (still approval-gated) durable workflow run.
scheduled_tasks_service = ScheduledTasksService(storage, governance_service, workflows=durable_workflow_service)
from app.services.scheduler_tick_worker import SchedulerTickWorker  # noqa: E402
scheduler_tick_worker = SchedulerTickWorker(scheduled_tasks_service)
# v120: the event bus dispatches subscription actions through the two engines
# above; wire it back into them as an optional collaborator (post-init, since
# they were constructed first) so their own state transitions can emit events.
from app.services.event_bus_service import EventBusService  # noqa: E402
event_bus_service = EventBusService(storage, governance_service, workflows=durable_workflow_service, scheduled_tasks=scheduled_tasks_service)
durable_workflow_service.event_bus = event_bus_service
scheduled_tasks_service.event_bus = event_bus_service
marketplace_hub_service = MarketplaceHubService(storage, governance_service, agent_profile_service, durable_workflow_service)
design_agent_service = DesignAgentService(storage, governance_service)
git_reader_service = GitReaderService(governance_service)
github_connector_service = GitHubConnectorService(storage, governance_service)
# v100: wire the real (opt-in, read-only) GitHub adapter into MCP execution now
# that github_connector_service exists (it's constructed after mcp_execution_service).
mcp_execution_service.github_adapter = MCPGitHubAdapter(github_connector_service)
# v120: wire the real (opt-in, approval-gated) GitHub connector into durable
# workflows now that it exists (it's constructed after durable_workflow_service),
# backing the create_github_issue whitelisted effect with a real write.
durable_workflow_service.github = github_connector_service
# v150 Autonomous Software Team: wire the real (opt-in, allow-listed-repo,
# approval-gated) code writer into durable workflows, backing the
# write_code_change whitelisted effect with a real local git commit.
code_writer_service = CodeWriterService(governance_service)
durable_workflow_service.code_writer = code_writer_service
# v180 Personal Chief of Staff: wire the real (read-only) GitHub connector in
# now that it exists (it's constructed after chief_of_staff_service), folding
# real open PRs/issues from CHIEF_OF_STAFF_GITHUB_REPOS-configured repos into
# priority ranking and daily/weekly plans alongside internal signals.
chief_of_staff_service.github = github_connector_service
repo_finder_service = RepoFinderService(storage, governance_service)
from app.services.memory_service import MemoryService  # noqa: E402
memory_service = MemoryService(storage, governance_service)
# Memory v2 powers adaptive-learning recall (semantic when on pgvector).
adaptive_learning_service = AdaptiveLearningService(storage, governance_service, memory=memory_service)
# v140 Workspace Brain: wire Memory v2 into BOTH WorkspaceService instances now
# that it exists — the routes.py singleton (used by /api/workspaces/*) and the
# one MasterOrchestratorAgent built internally (used by the live /api/run
# pipeline, the one that actually matters for real agent memory recall).
workspace_service.memory_v2 = memory_service
master_agent.workspace.memory_v2 = memory_service
# v140 task 2: goals are the other context pillar (chats/files/goals/agents/
# memory) that real semantic recall hadn't reached yet — mirror them in too.
goal_service.memory_v2 = memory_service
master_agent.goal_service.memory_v2 = memory_service
# v140 task 3: uploaded files are another pillar (chats already flow through
# create_memory via persist_workspace_memory, so they get real recall for free).
file_service.memory_v2 = memory_service
master_agent.file_service.memory_v2 = memory_service
# v140 task 4: custom agents are the last of the 5 pillars (chats/files/goals/
# agents/memory) to reach real semantic recall.
custom_agent_service.memory_v2 = memory_service
master_agent.custom_agents.memory_v2 = memory_service
from app.services.agent_registry_service import AgentRegistryService  # noqa: E402
agent_registry_service = AgentRegistryService(storage, governance_service)
from app.services.agent_governance_service import AgentGovernanceService  # noqa: E402
agent_governance_service = AgentGovernanceService(storage, governance_service, agent_registry_service)
home_dashboard_service = HomeDashboardService(storage, governance_service)
global_search_service = GlobalSearchService(storage, governance_service)
activity_timeline_service = ActivityTimelineService(storage, governance_service)
dashboard_home_service = DashboardHomeService(storage, governance_service, health_monitor_service)
feature_registry_service = FeatureRegistryService(storage, governance_service)
demo_service = DemoService(storage, governance_service)
settings_service = SettingsService(storage, governance_service)
provider_control_service = ProviderControlService(storage, governance_service, llm_router=llm_router)
# Real task-based routing + real provider health (previously the model_by_task
# preference above had zero effect on llm_router, and llm_router had no
# observability into real call success/latency).
llm_router.provider_control = provider_control_service
llm_router.storage = storage
notifications_inbox_service = NotificationsInboxService(storage, governance_service, health_monitor_service, provider_control_service)
workspace_os_service = WorkspaceOSService(storage, governance_service, activity_timeline_service)
smart_context_service = SmartContextService(storage, governance_service)
agent_quality_service = AgentQualityService(storage, governance_service)
workflow_recommendation_service = WorkflowRecommendationService(storage, governance_service)
personal_productivity_service = PersonalProductivityService(storage, governance_service)
document_intelligence_service = DocumentIntelligenceService(storage, governance_service)
code_intelligence_service = CodeIntelligenceService(storage, governance_service)
research_agent_service = ResearchAgentService(storage, governance_service)
business_intelligence_service = BusinessIntelligenceService(storage, governance_service)
meeting_intelligence_service = MeetingIntelligenceService(storage, governance_service)
agent_collaboration_service = AgentCollaborationService(storage, governance_service)
permission_profiles_service = PermissionProfilesService(storage, governance_service)
governance_console_service = GovernanceConsoleService(storage, governance_service)
data_manager_service = DataManagerService(storage, governance_service)
import_center_service = ImportCenterService(storage, governance_service)
export_center_service = ExportCenterService(storage, governance_service)
plugin_marketplace_service = PluginMarketplaceService(storage, governance_service)
integration_hub_service = IntegrationHubService(storage, governance_service)
qa_center_service = QACenterService(storage, governance_service, feature_registry_service, health_monitor_service)
release_manager_service = ReleaseManagerService(storage, governance_service, feature_registry_service)
product_launch_service = ProductLaunchService(storage, governance_service, feature_registry_service, qa_center_service, export_center_service)
team_manager_service = TeamManagerService(storage, governance_service)
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


# NOTE: /simulations/* routes were extracted into app/api/simulations_routes.py (services still live here).


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


# NOTE: /tools/* routes were extracted into app/api/tools_routes.py (services still live here).


@router.get("/plugins")
def list_plugins() -> list[dict]:
    return plugin_loader.load_plugins()


# NOTE: /integrations/* routes were extracted into app/api/integrations_routes.py (services still live here).


@router.post("/run", response_model=RunResponse)
def run_workflow(request: RunRequest) -> RunResponse:
    response = kernel_service.run_workflow(request)
    slack_notifications.notify_run_completed(response)
    notion_exports.export_run_completed(response)
    return response


# NOTE: /system-prompts/* routes were extracted into app/api/system_prompts_routes.py (services still live here).


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


# NOTE: /learning/* routes were extracted into app/api/learning_routes.py (services still live here).


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
        **mcp_connector_service.analytics_summary(),
        **mcp_execution_service.analytics_summary(),
        **mcp_approvals_inbox_service.analytics_summary(),
        **mcp_policy_service.analytics_summary(),
        **mcp_audit_service.analytics_summary(),
        **mcp_secret_registry_service.analytics_summary(),
        **unified_approvals_service.analytics_summary(),
        **health_monitor_service.analytics_summary(),
        **usage_ledger_service.analytics_summary(),
        **local_retrieval_service.analytics_summary(),
        **eval_harness_service.analytics_summary(),
        **playbook_library_service.analytics_summary(),
        **operating_layer_v2_service.analytics_summary(),
        **notifications_center_service.analytics_summary(),
        **workspace_templates_service.analytics_summary(),
        **scheduled_tasks_service.analytics_summary(),
        **data_export_service.analytics_summary(),
        **evolveagent_os2_service.analytics_summary(),
        **master_agent_service.analytics_summary(),
        **git_discovery_service.analytics_summary(),
        **agent_profile_service.analytics_summary(),
        **voice_console_service.analytics_summary(),
        **durable_workflow_service.analytics_summary(),
        **marketplace_hub_service.analytics_summary(),
        **design_agent_service.analytics_summary(),
        **multimodal_agent_service.analytics_summary(),
        **git_reader_service.analytics_summary(),
        **github_connector_service.analytics_summary(),
        **code_writer_service.analytics_summary(),
        **chief_of_staff_service.analytics_summary(),
        **repo_finder_service.analytics_summary(),
        **memory_service.analytics_summary(),
        **agent_registry_service.analytics_summary(),
        **agent_governance_service.analytics_summary(),
        **event_bus_service.analytics_summary(),
        **adaptive_learning_service.analytics_summary(),
        **global_search_service.analytics_summary(),
        **activity_timeline_service.analytics_summary(),
        **dashboard_home_service.analytics_summary(),
        **feature_registry_service.analytics_summary(),
        **demo_service.analytics_summary(),
        **settings_service.analytics_summary(),
        **provider_control_service.analytics_summary(),
        **notifications_inbox_service.analytics_summary(),
        **workspace_os_service.analytics_summary(),
        **smart_context_service.analytics_summary(),
        **agent_quality_service.analytics_summary(),
        **workflow_recommendation_service.analytics_summary(),
        **personal_productivity_service.analytics_summary(),
        **document_intelligence_service.analytics_summary(),
        **code_intelligence_service.analytics_summary(),
        **research_agent_service.analytics_summary(),
        **business_intelligence_service.analytics_summary(),
        **meeting_intelligence_service.analytics_summary(),
        **agent_collaboration_service.analytics_summary(),
        **permission_profiles_service.analytics_summary(),
        **governance_console_service.analytics_summary(),
        **data_manager_service.analytics_summary(),
        **import_center_service.analytics_summary(),
        **export_center_service.analytics_summary(),
        **plugin_marketplace_service.analytics_summary(),
        **integration_hub_service.analytics_summary(),
        **qa_center_service.analytics_summary(),
        **release_manager_service.analytics_summary(),
        **product_launch_service.analytics_summary(),
        "recent_runs": list(reversed(runs[-10:])),
    }


# NOTE: /os/* routes were extracted into app/api/os_routes.py (services still live here).


# ----------------------------------------------------------------------
# v34.0 Legal / Compliance Intelligence Layer (not legal advice)
# ----------------------------------------------------------------------
@router.get("/compliance/dashboard")
def get_compliance_intel_dashboard() -> dict:
    return compliance_intelligence_service.dashboard()


@router.get("/compliance/policies")
def list_compliance_intel_policies() -> dict:
    policies = compliance_intelligence_service.list_policies()
    return {"policies": policies, "count": len(policies)}


@router.post("/compliance/policies")
def create_compliance_intel_policy(request: CompliancePolicyCreateRequest) -> dict:
    return compliance_intelligence_service.create_policy(request.model_dump())


@router.patch("/compliance/policies/{policy_id}")
def update_compliance_intel_policy(policy_id: str, request: CompliancePolicyUpdateRequest) -> dict:
    try:
        return compliance_intelligence_service.update_policy(policy_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Policy not found") from error


@router.post("/compliance/scan")
def run_compliance_scan(request: ComplianceScanRequest) -> dict:
    return compliance_intelligence_service.scan(request.content, request.label)


@router.get("/compliance/scans")
def list_compliance_scans() -> dict:
    scans = compliance_intelligence_service.list_scans()
    return {"scans": scans, "count": len(scans)}


@router.post("/compliance/contracts/review")
def review_compliance_contract(request: ComplianceContractReviewRequest) -> dict:
    return compliance_intelligence_service.review_contract(request.model_dump())


@router.get("/compliance/contracts/reviews")
def list_compliance_contract_reviews() -> dict:
    reviews = compliance_intelligence_service.list_contract_reviews()
    return {"reviews": reviews, "count": len(reviews)}


@router.post("/compliance/checklists")
def create_compliance_checklist(request: ComplianceChecklistRequest) -> dict:
    return compliance_intelligence_service.create_checklist(request.model_dump())


@router.get("/compliance/checklists")
def list_compliance_checklists() -> dict:
    checklists = compliance_intelligence_service.list_checklists()
    return {"checklists": checklists, "count": len(checklists)}


@router.post("/compliance/audit-packages")
def create_compliance_audit_package(request: ComplianceAuditPackageRequest | None = None) -> dict:
    return compliance_intelligence_service.create_audit_package(request.model_dump() if request else {})


@router.get("/compliance/audit-packages")
def list_compliance_audit_packages() -> dict:
    packages = compliance_intelligence_service.list_audit_packages()
    return {"audit_packages": packages, "count": len(packages)}


@router.get("/compliance/audit-packages/{package_id}")
def get_compliance_audit_package(package_id: str) -> dict:
    try:
        return compliance_intelligence_service.get_audit_package(package_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


# NOTE: /operating-layer/* routes were extracted into app/api/operating_layer_routes.py (services still live here).


# ----------------------------------------------------------------------
# v41.0 MCP Connector Hub (planning-first; no real MCP execution, no secrets exposed)
# ----------------------------------------------------------------------
@router.get("/mcp/summary")
def get_mcp_summary() -> dict:
    return mcp_connector_service.summarize_mcp_hub()


# Task-aware MCP suggestion — which connector(s) a task needs + key readiness (never values).
@router.post("/mcp/suggest")
def suggest_mcp(request: MCPSuggestRequest) -> dict:
    return mcp_suggestion_service.suggest(request.task)


@router.get("/mcp/templates")
def get_mcp_templates() -> dict:
    templates = mcp_connector_service.get_default_mcp_templates()
    return {"templates": templates, "count": len(templates)}


@router.get("/mcp/connectors")
def list_mcp_connectors() -> dict:
    connectors = mcp_connector_service.list_connectors()
    return {"connectors": connectors, "count": len(connectors)}


@router.post("/mcp/connectors")
def create_mcp_connector(request: MCPConnectorCreateRequest) -> dict:
    return mcp_connector_service.create_connector(request.model_dump(exclude_unset=True))


@router.get("/mcp/events")
def list_mcp_events(connector_id: str | None = Query(default=None)) -> dict:
    events = mcp_connector_service.list_connector_events(connector_id)
    return {"events": events, "count": len(events)}


@router.get("/mcp/connectors/{connector_id}")
def get_mcp_connector(connector_id: str) -> dict:
    connector = mcp_connector_service.get_connector(connector_id)
    if connector is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    return connector


@router.patch("/mcp/connectors/{connector_id}")
def update_mcp_connector(connector_id: str, request: MCPConnectorUpdateRequest) -> dict:
    try:
        return mcp_connector_service.update_connector(connector_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Connector not found") from error


@router.post("/mcp/connectors/{connector_id}/enable")
def enable_mcp_connector(connector_id: str) -> dict:
    try:
        return mcp_connector_service.enable_connector(connector_id)
    except ValueError as error:
        detail = str(error)
        status = 404 if "not found" in detail.lower() else 409
        raise HTTPException(status_code=status, detail=detail) from error


@router.post("/mcp/connectors/{connector_id}/disable")
def disable_mcp_connector(connector_id: str) -> dict:
    try:
        return mcp_connector_service.disable_connector(connector_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Connector not found") from error


@router.post("/mcp/connectors/{connector_id}/check")
def check_mcp_connector(connector_id: str) -> dict:
    try:
        return mcp_connector_service.check_connector_status(connector_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Connector not found") from error


@router.post("/mcp/connectors/{connector_id}/plan-action")
def plan_mcp_connector_action(connector_id: str, request: MCPPlanActionRequest) -> dict:
    try:
        return mcp_connector_service.plan_connector_action(
            connector_id, request.action_name, request.payload, request.workspace_id
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Connector not found") from error


# ----------------------------------------------------------------------
# v42.0 MCP Execution Adapter (approval-gated, mock-by-default; no real execution)
# ----------------------------------------------------------------------
@router.get("/mcp/executions/summary")
def get_mcp_execution_summary() -> dict:
    return mcp_execution_service.summarize()


# v43.0 MCP Read-Only Adapter — opt-in, sandboxed, read-only real execution status.
@router.get("/mcp/adapter/status")
def get_mcp_adapter_status() -> dict:
    return mcp_execution_service.adapter_status()


# ----------------------------------------------------------------------
# v44.0 MCP Approvals Inbox — unified, prioritized queue of pending approvals.
# ----------------------------------------------------------------------
@router.get("/mcp/inbox/summary")
def get_mcp_inbox_summary() -> dict:
    return mcp_approvals_inbox_service.summary()


@router.get("/mcp/inbox")
def get_mcp_inbox(risk_level: str | None = Query(default=None)) -> dict:
    items = mcp_approvals_inbox_service.list_inbox(risk_level)
    return {"items": items, "count": len(items)}


@router.post("/mcp/inbox/{item_id}/approve")
def approve_mcp_inbox_item(item_id: str) -> dict:
    try:
        return mcp_approvals_inbox_service.approve(item_id)
    except ValueError as error:
        detail = str(error)
        status = 404 if "not found" in detail.lower() else 409
        raise HTTPException(status_code=status, detail=detail) from error


@router.post("/mcp/inbox/{item_id}/reject")
def reject_mcp_inbox_item(item_id: str) -> dict:
    try:
        return mcp_approvals_inbox_service.reject(item_id)
    except ValueError as error:
        detail = str(error)
        status = 404 if "not found" in detail.lower() else 409
        raise HTTPException(status_code=status, detail=detail) from error


# ----------------------------------------------------------------------
# v46.0 MCP Audit & Replay — read-only unified timeline + dry replay.
# ----------------------------------------------------------------------
@router.get("/mcp/audit/summary")
def get_mcp_audit_summary() -> dict:
    return mcp_audit_service.summary()


@router.get("/mcp/audit")
def get_mcp_audit(
    connector_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    since: str | None = Query(default=None),
) -> dict:
    events = mcp_audit_service.timeline(connector_id=connector_id, event_type=event_type, since=since)
    return {"events": events, "count": len(events)}


@router.get("/mcp/audit/export")
def export_mcp_audit(format: str = Query(default="markdown")) -> dict:
    fmt = format if format in ("markdown", "json") else "markdown"
    return mcp_audit_service.export(fmt)


@router.get("/mcp/audit/replays")
def list_mcp_replays() -> dict:
    replays = mcp_audit_service.list_replays()
    return {"replays": replays, "count": len(replays)}


@router.post("/mcp/audit/replay")
def replay_mcp_request(request: MCPReplayRequest) -> dict:
    try:
        return mcp_audit_service.replay(request.request_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


# ----------------------------------------------------------------------
# v47.0 Secret Reference Registry — key names + readiness only; never values.
# ----------------------------------------------------------------------
@router.get("/mcp/secrets/summary")
def get_mcp_secrets_summary() -> dict:
    return mcp_secret_registry_service.summary()


@router.get("/mcp/secrets")
def list_mcp_secrets() -> dict:
    refs = mcp_secret_registry_service.list_refs()
    return {"refs": refs, "count": len(refs)}


@router.post("/mcp/secrets")
def register_mcp_secret(request: MCPSecretRefCreateRequest) -> dict:
    return mcp_secret_registry_service.register_ref(request.model_dump())


@router.patch("/mcp/secrets/{ref_id}")
def update_mcp_secret(ref_id: str, request: MCPSecretRefUpdateRequest) -> dict:
    try:
        return mcp_secret_registry_service.update_ref(ref_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Secret reference not found") from error


@router.post("/mcp/secrets/{ref_id}/rotate")
def rotate_mcp_secret(ref_id: str) -> dict:
    try:
        return mcp_secret_registry_service.mark_rotated(ref_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Secret reference not found") from error


# ----------------------------------------------------------------------
# v45.0 MCP Policy Engine — tighten-only deny rules evaluated before planning.
# ----------------------------------------------------------------------
@router.get("/mcp/policies/summary")
def get_mcp_policies_summary() -> dict:
    return mcp_policy_service.summarize()


@router.get("/mcp/policies")
def list_mcp_policies() -> dict:
    policies = mcp_policy_service.list_policies()
    return {"policies": policies, "count": len(policies)}


@router.post("/mcp/policies")
def create_mcp_policy(request: MCPPolicyCreateRequest) -> dict:
    return mcp_policy_service.create_policy(request.model_dump())


@router.post("/mcp/policies/evaluate")
def evaluate_mcp_policy(request: MCPPolicyEvaluateRequest) -> dict:
    connector = mcp_connector_service.get_connector(request.connector_id)
    if connector is None:
        raise HTTPException(status_code=404, detail="Connector not found")
    return mcp_policy_service.evaluate(connector, request.action_name)


@router.get("/mcp/policies/{policy_id}")
def get_mcp_policy(policy_id: str) -> dict:
    policy = mcp_policy_service.get_policy(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.patch("/mcp/policies/{policy_id}")
def update_mcp_policy(policy_id: str, request: MCPPolicyUpdateRequest) -> dict:
    try:
        return mcp_policy_service.update_policy(policy_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Policy not found") from error


@router.get("/mcp/executions")
def list_mcp_executions(connector_id: str | None = Query(default=None)) -> dict:
    requests = mcp_execution_service.list_requests(connector_id)
    return {"requests": requests, "count": len(requests)}


@router.post("/mcp/connectors/{connector_id}/execute")
def request_mcp_execution(connector_id: str, request: MCPExecuteRequest) -> dict:
    try:
        return mcp_execution_service.request_execution(
            connector_id, request.action_name, request.payload, request.workspace_id
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Connector not found") from error


@router.get("/mcp/executions/{request_id}")
def get_mcp_execution(request_id: str) -> dict:
    record = mcp_execution_service.get_request(request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Execution request not found")
    return record


@router.post("/mcp/executions/{request_id}/approve")
def approve_mcp_execution(request_id: str) -> dict:
    try:
        return mcp_execution_service.approve_execution(request_id)
    except ValueError as error:
        detail = str(error)
        status = 404 if "not found" in detail.lower() else 409
        raise HTTPException(status_code=status, detail=detail) from error


@router.post("/mcp/executions/{request_id}/reject")
def reject_mcp_execution(request_id: str) -> dict:
    try:
        return mcp_execution_service.reject_execution(request_id)
    except ValueError as error:
        detail = str(error)
        status = 404 if "not found" in detail.lower() else 409
        raise HTTPException(status_code=status, detail=detail) from error


@router.post("/mcp/executions/{request_id}/run")
def run_mcp_execution(request_id: str) -> dict:
    try:
        return mcp_execution_service.run_execution(request_id)
    except ValueError as error:
        detail = str(error)
        status = 404 if "not found" in detail.lower() else 409
        raise HTTPException(status_code=status, detail=detail) from error


# NOTE: /health-monitor/* routes were extracted into app/api/health_monitor_routes.py (services still live here).


# ----------------------------------------------------------------------
# v56.0 Notifications & Alerts Center — local in-app digest (no real sending).
# ----------------------------------------------------------------------
@router.get("/notifications/summary")
def get_notifications_summary() -> dict:
    return notifications_center_service.summary()


@router.get("/notifications")
def list_notifications(unread: bool = Query(default=False)) -> dict:
    items = notifications_center_service.list_notifications(unacknowledged_only=unread)
    return {"notifications": items, "count": len(items)}


@router.post("/notifications/generate")
def generate_notifications() -> dict:
    return notifications_center_service.generate()


@router.post("/notifications/{notif_id}/ack")
def acknowledge_notification(notif_id: str) -> dict:
    try:
        return notifications_center_service.acknowledge(notif_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Notification not found") from error


# NOTE: /data-export/* routes were extracted into app/api/data_export_routes.py (services still live here).


# ----------------------------------------------------------------------
# Git Intelligence (Phase 1) — read-only, opt-in, mock-safe discovery.
# ----------------------------------------------------------------------
@router.get("/git-intel/status")
def git_status() -> dict:
    return git_discovery_service.status()


@router.post("/git-intel/discover")
def git_discover(request: GitDiscoverRequest) -> dict:
    return git_discovery_service.discover(request.path, request.opt_in, request.workspace_id)


@router.get("/git-intel/repositories")
def git_repositories(workspace_id: str | None = Query(default=None)) -> dict:
    return git_discovery_service.repositories(workspace_id=workspace_id)


@router.get("/git-intel/repositories/{repo_id}")
def git_repository(repo_id: str) -> dict:
    try:
        return git_discovery_service.repository(repo_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/git-intel/repositories/{repo_id}/activity")
def git_repository_activity(repo_id: str) -> dict:
    try:
        return git_discovery_service.activity(repo_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/git-intel/repositories/{repo_id}/context")
def git_repository_context(repo_id: str) -> dict:
    try:
        return git_discovery_service.context(repo_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


# NOTE: /agent-studio/* routes were extracted into app/api/agent_studio_routes.py (services still live here).


# ----------------------------------------------------------------------
# v62.0 Global Search — one read-only search bar across the whole OS.
# ----------------------------------------------------------------------
@router.get("/search")
def global_search(
    q: str = Query(..., min_length=1),
    workspace_id: str | None = Query(default=None),
    types: str | None = Query(default=None, description="Comma-separated result types to filter by."),
    since: str | None = Query(default=None, description="ISO timestamp; only results created at/after this."),
) -> dict:
    type_list = [t.strip() for t in types.split(",") if t.strip()] if types else None
    return global_search_service.search(q, workspace_id=workspace_id, types=type_list, since=since)


@router.get("/search/sources")
def global_search_sources() -> dict:
    return global_search_service.sources()


# ----------------------------------------------------------------------
# v63.0 Unified Activity Timeline — chronological view of everything the OS did.
# ----------------------------------------------------------------------
@router.get("/activity")
def activity_timeline(
    workspace_id: str | None = Query(default=None),
    types: str | None = Query(default=None, description="Comma-separated event types."),
    status: str | None = Query(default=None),
    actor: str | None = Query(default=None),
    since: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    type_list = [t.strip() for t in types.split(",") if t.strip()] if types else None
    return activity_timeline_service.timeline(workspace_id=workspace_id, types=type_list, status=status, actor=actor, since=since, limit=limit)


@router.get("/activity/summary")
def activity_timeline_summary() -> dict:
    return activity_timeline_service.summary()


# ----------------------------------------------------------------------
# v64.0 Dashboard Home 2.0 — one professional homepage over the whole OS.
# ----------------------------------------------------------------------
@router.get("/home")
def dashboard_home(workspace_id: str | None = Query(default=None)) -> dict:
    return dashboard_home_service.home(workspace_id=workspace_id)


# NOTE: /features/* routes were extracted into app/api/features_routes.py (services still live here).


# ----------------------------------------------------------------------
# v67.0 Settings Center — central local configuration (no secrets stored).
# ----------------------------------------------------------------------
@router.get("/settings")
def get_settings() -> dict:
    return settings_service.get_settings()


@router.patch("/settings")
def update_settings(request: SettingsUpdateRequest) -> dict:
    return settings_service.update_settings(request.settings)


@router.post("/settings/reset")
def reset_settings() -> dict:
    return settings_service.reset()


@router.get("/settings/export")
def export_settings() -> dict:
    return settings_service.export_settings()


@router.post("/settings/import")
def import_settings(request: SettingsImportRequest) -> dict:
    try:
        return settings_service.import_settings({"settings": request.settings})
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


# NOTE: /notifications-inbox/* routes were extracted into app/api/notifications_inbox_routes.py (services still live here).


# ----------------------------------------------------------------------
# v70.0 Workspace Operating System 2.0 — per-workspace AI OS overview.
# ----------------------------------------------------------------------
@router.get("/workspace-os/summary")
def workspace_os_summary() -> dict:
    return workspace_os_service.summary()


@router.get("/workspace-os/{workspace_id}/dashboard")
def workspace_os_dashboard(workspace_id: str) -> dict:
    return workspace_os_service.dashboard(workspace_id)


# ----------------------------------------------------------------------
# v71.0 Smart Context Engine — plan context selection (read-only preview).
# ----------------------------------------------------------------------
@router.post("/context/plan")
def context_plan(request: ContextPlanRequest) -> dict:
    return smart_context_service.plan(request.query, workspace_id=request.workspace_id, budget_chars=request.budget_chars)


@router.get("/context/summary")
def context_summary() -> dict:
    return smart_context_service.summary()


# NOTE: /agent-quality/* routes were extracted into app/api/agent_quality_routes.py (services still live here).


# ----------------------------------------------------------------------
# v73.0 Workflow Recommendation Engine — suggest the best workflow (read-only).
# ----------------------------------------------------------------------
@router.post("/workflow-recommend")
def workflow_recommend(request: WorkflowRecommendRequest) -> dict:
    return workflow_recommendation_service.recommend(request.goal, task_type=request.task_type)


@router.get("/workflow-recommend/summary")
def workflow_recommend_summary() -> dict:
    return workflow_recommendation_service.summary()


# NOTE: /business-intel/* routes were extracted into app/api/business_intel_routes.py (services still live here).


# ----------------------------------------------------------------------
# v80.0 Multi-Agent Collaboration 2.0 — visible multi-agent analysis (read-only).
# ----------------------------------------------------------------------
@router.post("/collaboration/analyze")
def collaboration_analyze(request: CollaborationRequest) -> dict:
    return agent_collaboration_service.analyze(request.topic, request.contributions)


@router.get("/collaboration/summary")
def collaboration_summary() -> dict:
    return agent_collaboration_service.summary()


# NOTE: /governance-console/* routes were extracted into app/api/governance_console_routes.py (services still live here).


@router.get("/activity/export")
def activity_timeline_export(
    format: str = Query(default="markdown", pattern="^(markdown|json)$"),
    workspace_id: str | None = Query(default=None),
    types: str | None = Query(default=None),
    since: str | None = Query(default=None),
) -> dict:
    type_list = [t.strip() for t in types.split(",") if t.strip()] if types else None
    return activity_timeline_service.export(fmt=format, workspace_id=workspace_id, types=type_list, since=since)


# NOTE: /os2/* routes were extracted into app/api/os2_routes.py (services still live here).


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


# NOTE: /goals/* routes were extracted into app/api/goals_routes.py (services still live here).


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


# NOTE: /agent-marketplace/* routes were extracted into app/api/agent_marketplace_routes.py (services still live here).


@router.get("/providers/status", response_model=ProviderStatus)
def get_provider_status() -> ProviderStatus:
    return llm_router.status()


@router.post("/providers/smoke-test")
def provider_smoke_test(request: ProviderSmokeTestRequest) -> dict:
    return llm_router.smoke_test(provider=request.provider, live=request.live, task_type=request.task_type)


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


# NOTE: /real-api/* routes were extracted into app/api/real_api_routes.py (services still live here).


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
