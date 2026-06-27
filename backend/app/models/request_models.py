from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    user_input: str = Field(..., min_length=1, description="The task the user wants agents to solve.")
    task_type: str = Field(default="auto", description="auto, resume, coding, business, research, finance, pharmacy, image_generation, system_explanation, app_automation, recording_summary, document_analysis, file_summary, resume_review, code_review, data_analysis, or general")
    deep_mode: bool = Field(default=False, description="Run optional multi-model consensus candidates.")
    session_id: str | None = Field(default=None, description="Existing chat session ID. Omit to create a new session.")
    file_ids: list[str] = Field(default_factory=list, description="Uploaded file IDs to include as context.")
    recording_ids: list[str] = Field(default_factory=list, description="Uploaded recording IDs to include as transcript context.")
    voice_used: bool = Field(default=False, description="Whether the request came from browser voice transcription.")
    voice_transcript: str | None = Field(default=None, description="Browser-transcribed voice command text, if used.")
    workspace_id: str | None = Field(default=None, description="Optional workspace ID. Omit to use the default workspace.")
    goal_id: str | None = Field(default=None, description="Optional Mission Control goal ID associated with this run.")
    task_id: str | None = Field(default=None, description="Optional Mission Control task ID associated with this run.")
    custom_agent_id: str | None = Field(default=None, description="Optional custom agent ID to include in the workflow.")


class RenameChatRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=80)


class CreateChatRequest(BaseModel):
    title: str | None = Field(default=None, max_length=80)
    workspace_id: str | None = None


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    run_id: str
    workspace_id: str | None = None
    rating: str = Field(..., pattern="^(helpful|not_helpful|saved)$")
    comment: str | None = Field(default=None, max_length=1000)


class FilePatchRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=300)
    content: str | None = Field(default=None, max_length=500_000)
    find: str | None = Field(default=None, max_length=50_000)
    replace: str | None = Field(default=None, max_length=50_000)


class AutomationApplyRequest(BaseModel):
    run_id: str
    approved: bool
    patches: list[FilePatchRequest] = Field(default_factory=list, max_length=5)


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject)$")
    comment: str | None = Field(default=None, max_length=1000)


class PromptProposalRequest(BaseModel):
    agent_name: str = Field(..., min_length=1, max_length=80)
    reason: str = Field(..., min_length=1, max_length=1000)
    proposed_prompt: str = Field(..., min_length=1, max_length=8000)


class PromptDecisionRequest(BaseModel):
    agent_name: str = Field(..., min_length=1, max_length=80)
    version_id: str = Field(..., min_length=1, max_length=80)


class CreateGoalRequest(BaseModel):
    prompt: str | None = Field(default=None, max_length=4000)
    title: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=4000)
    workspace_id: str | None = None
    source_session_id: str | None = None
    source_message_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class UpdateGoalRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=4000)
    status: str | None = Field(default=None, pattern="^(active|paused|completed|archived)$")
    tags: list[str] | None = None


class CreateGoalTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)
    phase: str = Field(default="Planning", max_length=80)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    depends_on: list[str] = Field(default_factory=list)
    recommended_agent: str = Field(default="Strategy Agent", max_length=120)
    estimated_effort: str = Field(default="medium", pattern="^(small|medium|large)$")
    requires_approval: bool = False
    automation_supported: bool = False


class UpdateGoalTaskRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    phase: str | None = Field(default=None, max_length=80)
    status: str | None = Field(default=None, pattern="^(pending|running|needs_approval|blocked|done|failed)$")
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")
    last_result_summary: str | None = Field(default=None, max_length=2000)
    completion_note: str | None = Field(default=None, max_length=2000, description="Optional note when marking done; posted to Linear and task summary.")
    depends_on: list[str] | None = None
    recommended_agent: str | None = Field(default=None, max_length=120)
    estimated_effort: str | None = Field(default=None, pattern="^(small|medium|large)$")
    requires_approval: bool | None = None
    automation_supported: bool | None = None


class CreateCustomAgentRequest(BaseModel):
    workspace_id: str | None = None
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default="", max_length=1000)
    role: str | None = Field(default="", max_length=1000)
    prompt: str | None = Field(default="", max_length=8000)
    tools_allowed: list[str] = Field(default_factory=list)
    model_preference: str = Field(default="default", pattern="^(default|openai|claude|gemini|mock)$")
    memory_scope: str = Field(default="session", pattern="^(none|session|workspace|global)$")
    approval_level: str = Field(default="read_only", pattern="^(read_only|plan_only|approve_to_edit|approve_to_run|blocked)$")
    enabled: bool = True
    template_name: str | None = Field(default=None, max_length=120)


class UpdateCustomAgentRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    role: str | None = Field(default=None, max_length=1000)
    prompt: str | None = Field(default=None, max_length=8000)
    tools_allowed: list[str] | None = None
    model_preference: str | None = Field(default=None, pattern="^(default|openai|claude|gemini|mock)$")
    memory_scope: str | None = Field(default=None, pattern="^(none|session|workspace|global)$")
    approval_level: str | None = Field(default=None, pattern="^(read_only|plan_only|approve_to_edit|approve_to_run|blocked)$")
    enabled: bool | None = None


class AgentTeamCreateRequest(BaseModel):
    workspace_id: str | None = None
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=1200)
    category: str = Field(default="custom", max_length=80)
    agents: list[dict] = Field(default_factory=list, max_length=12)
    workflow_packs: list[str] = Field(default_factory=list, max_length=12)
    permission_profile: str = Field(default="read_only", pattern="^(read_only|plan_only|approve_to_edit|approve_to_run|blocked)$")
    version: str = Field(default="1.0.0", max_length=40)
    enabled: bool = True
    benchmark_score: int = Field(default=0, ge=0, le=100)


class AgentTeamUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1200)
    category: str | None = Field(default=None, max_length=80)
    agents: list[dict] | None = Field(default=None, max_length=12)
    workflow_packs: list[str] | None = Field(default=None, max_length=12)
    permission_profile: str | None = Field(default=None, pattern="^(read_only|plan_only|approve_to_edit|approve_to_run|blocked)$")
    version: str | None = Field(default=None, max_length=40)
    version_notes: str | None = Field(default=None, max_length=500)
    enabled: bool | None = None
    benchmark_score: int | None = Field(default=None, ge=0, le=100)


class AgentPackInstallRequest(BaseModel):
    workspace_id: str | None = None


class AgentTeamImportRequest(BaseModel):
    workspace_id: str | None = None
    payload: dict = Field(default_factory=dict)


class AgentTeamRatingRequest(BaseModel):
    workspace_id: str | None = None
    rating: int = Field(..., ge=1, le=5)
    review: str | None = Field(default="", max_length=1000)


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default="", max_length=1000)
    tags: list[str] = Field(default_factory=list)


class UpdateWorkspaceRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    status: str | None = Field(default=None, pattern="^(active|archived)$")
    tags: list[str] | None = None


class CreateWorkspaceMemoryRequest(BaseModel):
    type: str = Field(default="summary", pattern="^(preference|project_fact|decision|summary|task_result|learned_pattern)$")
    title: str = Field(..., min_length=1, max_length=160)
    content: str = Field(..., min_length=1, max_length=5000)
    source: str = Field(default="manual", pattern="^(chat|file|recording|goal|feedback|manual)$")
    importance: str = Field(default="medium", pattern="^(low|medium|high)$")
    tags: list[str] = Field(default_factory=list)


class UpdateWorkspaceMemoryRequest(BaseModel):
    type: str | None = Field(default=None, pattern="^(preference|project_fact|decision|summary|task_result|learned_pattern)$")
    title: str | None = Field(default=None, min_length=1, max_length=160)
    content: str | None = Field(default=None, min_length=1, max_length=5000)
    source: str | None = Field(default=None, pattern="^(chat|file|recording|goal|feedback|manual)$")
    importance: str | None = Field(default=None, pattern="^(low|medium|high)$")
    tags: list[str] | None = None
    pinned: bool | None = None


class MemoryConsolidateRequest(BaseModel):
    approved: bool = Field(default=False, description="Preview by default; archive duplicates only when approved.")


class MemoryConsolidationJobRequest(BaseModel):
    apply: bool = Field(default=False, description="Create a preview job by default; apply immediately only when true.")


class CreateKnowledgeLinkRequest(BaseModel):
    source_type: str = Field(..., pattern="^(memory|chat|file|recording|goal|custom_agent)$")
    source_id: str = Field(..., min_length=1, max_length=160)
    target_type: str = Field(..., pattern="^(memory|chat|file|recording|goal|custom_agent)$")
    target_id: str = Field(..., min_length=1, max_length=160)
    reason: str | None = Field(default=None, max_length=500)


class LinearCommentRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=8000)


class LinearCursorVerifyRequest(BaseModel):
    completion_note: str | None = Field(default=None, max_length=2000)
    auto_commit: bool = Field(default=False, description="Stage and commit safe files after verification passes.")


class GitBranchRequest(BaseModel):
    branch_name: str = Field(..., min_length=1, max_length=160)


class GitCommitRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=200)


class GitPushRequest(BaseModel):
    remote: str | None = Field(default=None, max_length=80)
    branch: str | None = Field(default=None, max_length=160)


class QualityRunRequest(BaseModel):
    commands: list[str] = Field(default_factory=list, max_length=2)
    issue_id: str | None = Field(default=None, max_length=120)


class TestSuggestionRequest(BaseModel):
    changed_files: list[str] = Field(default_factory=list, max_length=50)


class ProviderSmokeTestRequest(BaseModel):
    provider: str | None = Field(default=None, pattern="^(openai|anthropic|gemini|mistral|mock)$")
    live: bool = Field(default=False, description="When false, only checks configuration/readiness without calling a paid API.")


class ImageSmokeTestRequest(BaseModel):
    live: bool = Field(default=False, description="When false, only checks image-provider readiness without calling a paid API.")
    prompt: str = Field(default="A futuristic AI assistant in a holographic interface", max_length=1000)


class TranscriptionSmokeTestRequest(BaseModel):
    live: bool = Field(default=False, description="When false, only checks transcription-provider readiness without calling a paid API.")


class RealApiErrorDecodeRequest(BaseModel):
    error: str = Field(default="", max_length=4000)


class QualityLinearSummaryRequest(BaseModel):
    issue_id: str = Field(..., min_length=1, max_length=120)
    quality_run_id: str | None = Field(default=None, max_length=120)


class AppBuilderPlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    stack_id: str = Field(default="fastapi-react", max_length=80)
    workspace_id: str | None = None


class AppBuilderScaffoldRequest(BaseModel):
    plan_id: str = Field(..., min_length=1, max_length=120)
    approved: bool = False


class AppBuilderWizardRequest(BaseModel):
    plan_id: str | None = Field(default=None, max_length=120)
    app_name: str | None = Field(default=None, max_length=120)
    stack_id: str | None = Field(default=None, max_length=80)
    features: list[str] = Field(default_factory=list, max_length=12)
    notes: str | None = Field(default=None, max_length=2000)


class DebateCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    workspace_id: str | None = None
    agents: list[str] = Field(default_factory=list, max_length=6)


class SimulationCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    scenario: str | None = Field(default=None, max_length=1000)
    workspace_id: str | None = None


class DebateConsensusRequest(BaseModel):
    debate_id: str = Field(..., min_length=1, max_length=120)


class ResearchSessionCreateRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    workspace_id: str | None = None
    require_approval: bool = True
    notes: str | None = Field(default=None, max_length=2000)


class ResearchSourceCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    url: str = Field(..., min_length=1, max_length=1000)
    snippet: str = Field(default="", max_length=4000)
    publisher: str | None = Field(default=None, max_length=200)
    fetched: bool = False


class ResearchCitationCreateRequest(BaseModel):
    source_id: str = Field(..., min_length=1, max_length=120)
    claim: str = Field(..., min_length=1, max_length=1000)
    quote: str | None = Field(default=None, max_length=1000)


class AssistantCommandRequest(BaseModel):
    input_text: str = Field(default="", max_length=2000)
    workspace_id: str | None = None


class RegisterToolRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    input_schema: dict = Field(default_factory=dict)
    permission_level: str = Field(default="read_only", pattern="^(read_only|plan_only|approve_to_edit|approve_to_run|blocked)$")
    enabled: bool = True
    source: str = Field(default="built_in", pattern="^(built_in|plugin|assistant_command)$")


class CreateAgentJobRequest(BaseModel):
    job_type: str = Field(default="workflow", pattern="^(workflow|tool|maintenance|health_check)$")
    title: str = Field(..., min_length=1, max_length=160)
    payload: dict = Field(default_factory=dict)
    workspace_id: str | None = None


class AgentJobActionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class UpdateSystemPromptRequest(BaseModel):
    agent_name: str = Field(..., min_length=1, max_length=120)
    prompt: str = Field(..., min_length=1, max_length=8000)
    reason: str | None = Field(default=None, max_length=1000)


class ResearchSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    workspace_id: str | None = None
    max_results: int = Field(default=5, ge=1, le=10)


class DigitalTwinUpdateRequest(BaseModel):
    workspace_id: str | None = None
    detail_level: str | None = Field(default=None, max_length=120)
    technical_level: str | None = Field(default=None, max_length=120)
    format: str | None = Field(default=None, max_length=120)
    planning_style: str | None = Field(default=None, max_length=120)
    tone: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=1000)


class PiiScanRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20_000)
    redact: bool = True


class RetentionPolicyRequest(BaseModel):
    retention_days: int | None = Field(default=None, ge=1, le=3650)
    action: str | None = Field(default=None, pattern="^(keep|review|archive)$")
    enabled: bool | None = None
    description: str | None = Field(default=None, max_length=1000)


class SlackTestNotificationRequest(BaseModel):
    text: str = Field(default="EvolveAgent AI Slack notification test.", max_length=2000)
    channel: str | None = Field(default=None, max_length=120)
    workspace_id: str | None = None


class NotionExportRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=20_000)
    workspace_id: str | None = None


class AutopilotActionRequest(BaseModel):
    action_type: str = Field(..., min_length=1, max_length=80)
    summary: str = Field(..., min_length=1, max_length=1000)
    files_targeted: list[str] = Field(default_factory=list, max_length=5)
    command_requested: str | None = Field(default=None, max_length=200)
    risk_level: str = Field(default="medium", pattern="^(low|medium|high)$")


class AutopilotRunCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    workspace_id: str | None = None
    mode: str = Field(default="supervised", pattern="^(supervised|plan_only)$")
    actions: list[AutopilotActionRequest] = Field(default_factory=list, max_length=12)


class AutopilotSettingsUpdateRequest(BaseModel):
    kill_switch_enabled: bool | None = None
    permission_mode: str | None = Field(default=None, pattern="^(read_only|plan_only|supervised)$")
    default_permission_level: str | None = Field(
        default=None,
        pattern="^(read_only|plan_only|approve_to_edit|approve_to_run|blocked)$",
    )
    notes: str | None = Field(default=None, max_length=1000)


class AutopilotCheckpointDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject)$")
    comment: str | None = Field(default=None, max_length=1000)


class AutopilotRunControlRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class EvaluationRunRequest(BaseModel):
    benchmark_id: str | None = Field(default=None, max_length=120)
    task_type: str | None = Field(default=None, max_length=120)
    workspace_id: str | None = None
    notes: str | None = Field(default=None, max_length=1000)


class EvaluationABTestRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    variant_a: str = Field(..., min_length=1, max_length=160)
    variant_b: str = Field(..., min_length=1, max_length=160)
    metric: str = Field(default="overall_judge_score", max_length=80)
    workspace_id: str | None = None


class ProjectRiskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    severity: str = Field(default="medium", pattern="^(low|medium|high)$")
    mitigation: str = Field(default="", max_length=2000)
    goal_id: str | None = Field(default=None, max_length=120)
    workspace_id: str | None = None


class ProjectRiskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    severity: str | None = Field(default=None, pattern="^(low|medium|high)$")
    mitigation: str | None = Field(default=None, max_length=2000)
    status: str | None = Field(default=None, pattern="^(open|monitoring|resolved)$")
    goal_id: str | None = Field(default=None, max_length=120)


class ProjectReportRequest(BaseModel):
    workspace_id: str | None = None


class PortfolioReportRequest(BaseModel):
    title: str | None = Field(default=None, max_length=160)


class PluginManifestValidateRequest(BaseModel):
    manifest: dict = Field(default_factory=dict, description="Plugin manifest object to validate.")


class DepartmentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    manager_agent: str | None = Field(default=None, max_length=120)
    worker_agents: list[str] = Field(default_factory=list)
    reviewer_agents: list[str] = Field(default_factory=list)
    auditor_agents: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    permission_level: str = Field(
        default="read_only",
        pattern="^(read_only|plan_only|approve_to_edit|approve_to_run|blocked)$",
    )


class DepartmentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    manager_agent: str | None = Field(default=None, max_length=120)
    worker_agents: list[str] | None = None
    reviewer_agents: list[str] | None = None
    auditor_agents: list[str] | None = None
    allowed_tools: list[str] | None = None
    permission_level: str | None = Field(
        default=None,
        pattern="^(read_only|plan_only|approve_to_edit|approve_to_run|blocked)$",
    )
    active: bool | None = None


class DepartmentRunRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=2000)


class DepartmentCollaborationRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=2000)
    departments: list[str] = Field(default_factory=list)
    lead_department: str | None = Field(default=None, max_length=120)


# ----------------------------------------------------------------------
# v18.0 Real Business Automation Layer
# ----------------------------------------------------------------------
class BusinessLeadCreateRequest(BaseModel):
    name: str = Field(default="", max_length=160)
    company: str = Field(default="", max_length=160)
    email: str = Field(default="", max_length=200)
    status: str = Field(default="new", pattern="^(new|contacted|qualified|proposal_sent|won|lost)$")
    source: str = Field(default="manual", pattern="^(manual|chat|file|recording)$")
    notes: str = Field(default="", max_length=4000)
    next_step: str = Field(default="", max_length=500)
    workspace_id: str | None = None


class BusinessLeadUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=160)
    company: str | None = Field(default=None, max_length=160)
    email: str | None = Field(default=None, max_length=200)
    status: str | None = Field(default=None, pattern="^(new|contacted|qualified|proposal_sent|won|lost)$")
    source: str | None = Field(default=None, pattern="^(manual|chat|file|recording)$")
    notes: str | None = Field(default=None, max_length=4000)
    next_step: str | None = Field(default=None, max_length=500)


class BusinessSupportCaseCreateRequest(BaseModel):
    customer: str = Field(default="", max_length=160)
    subject: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    status: str = Field(default="open", pattern="^(open|waiting|resolved|escalated)$")
    workspace_id: str | None = None


class BusinessSupportCaseUpdateRequest(BaseModel):
    customer: str | None = Field(default=None, max_length=160)
    subject: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")
    status: str | None = Field(default=None, pattern="^(open|waiting|resolved|escalated)$")
    triage_summary: str | None = Field(default=None, max_length=1000)
    draft_reply: str | None = Field(default=None, max_length=4000)


class BusinessDocumentCreateRequest(BaseModel):
    title: str = Field(default="", max_length=200)
    document_type: str = Field(default="other", pattern="^(invoice|contract|proposal|receipt|other)$")
    content: str = Field(default="", max_length=20000)
    workspace_id: str | None = None


class BusinessDocumentUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    document_type: str | None = Field(default=None, pattern="^(invoice|contract|proposal|receipt|other)$")
    content: str | None = Field(default=None, max_length=20000)


class BusinessProposalCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    client: str = Field(default="", max_length=160)
    scope: str = Field(default="", max_length=4000)
    draft: str = Field(default="", max_length=8000)
    lead_id: str | None = Field(default=None, max_length=120)
    status: str = Field(default="draft", pattern="^(draft|reviewed|sent_manually|archived)$")
    workspace_id: str | None = None


class BusinessProposalUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    client: str | None = Field(default=None, max_length=160)
    scope: str | None = Field(default=None, max_length=4000)
    draft: str | None = Field(default=None, max_length=8000)
    lead_id: str | None = Field(default=None, max_length=120)
    status: str | None = Field(default=None, pattern="^(draft|reviewed|sent_manually|archived)$")


class BusinessMarketingItemCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    channel: str = Field(default="other", pattern="^(email|linkedin|website|instagram|other)$")
    scheduled_for: str = Field(default="", max_length=60)
    status: str = Field(default="planned", pattern="^(planned|drafted|approved|posted_manually)$")
    draft_content: str = Field(default="", max_length=4000)
    workspace_id: str | None = None


class BusinessMarketingItemUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    channel: str | None = Field(default=None, pattern="^(email|linkedin|website|instagram|other)$")
    scheduled_for: str | None = Field(default=None, max_length=60)
    status: str | None = Field(default=None, pattern="^(planned|drafted|approved|posted_manually)$")
    draft_content: str | None = Field(default=None, max_length=4000)


# ----------------------------------------------------------------------
# v19.0 AI Chief of Staff
# ----------------------------------------------------------------------
class ChiefPlanRequest(BaseModel):
    workspace_id: str | None = None


class ChiefFollowupCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    source_type: str = Field(default="manual", pattern="^(manual|goal|business|support|approval|risk)$")
    source_id: str | None = Field(default=None, max_length=120)
    due_date: str = Field(default="", max_length=10)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    status: str = Field(default="open", pattern="^(open|done|snoozed|archived)$")
    workspace_id: str | None = None


class ChiefFollowupUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    source_type: str | None = Field(default=None, pattern="^(manual|goal|business|support|approval|risk)$")
    source_id: str | None = Field(default=None, max_length=120)
    due_date: str | None = Field(default=None, max_length=10)
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")
    status: str | None = Field(default=None, pattern="^(open|done|snoozed|archived)$")


# ----------------------------------------------------------------------
# v20.0 Autonomous Business Simulator
# ----------------------------------------------------------------------
class SimulationScenarioCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    scenario_type: str = Field(default="decision", pattern="^(decision|cost|time|risk|launch|workflow|custom)$")
    assumptions: list[str] = Field(default_factory=list)
    options: list[str] = Field(default_factory=list)
    workspace_id: str | None = None


class SimulationScenarioUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    scenario_type: str | None = Field(default=None, pattern="^(decision|cost|time|risk|launch|workflow|custom)$")
    assumptions: list[str] | None = None
    options: list[str] | None = None


# ----------------------------------------------------------------------
# v21.0 Multi-Modal Real-World Agent
# ----------------------------------------------------------------------
class MultimodalItemCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    item_type: str = Field(default="screenshot", pattern="^(screenshot|ui_bug|diagram|whiteboard|document_image|custom)$")
    description: str = Field(default="", max_length=6000)
    source_ref: str | None = Field(default=None, max_length=300)
    workspace_id: str | None = None


class MultimodalAnalyzeRequest(BaseModel):
    analysis_type: str | None = Field(default=None, pattern="^(screenshot|ui_bug|diagram|whiteboard|document_image|custom)$")


# ----------------------------------------------------------------------
# v22.0 Industry Workflow Modes
# ----------------------------------------------------------------------
class IndustryModeUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    terminology: list[str] | None = None
    recommended_agents: list[str] | None = None
    workflow_templates: list[str] | None = None
    risk_rules: list[str] | None = None
    approval_rules: list[str] | None = None
    enabled: bool | None = None


class IndustryModeRunRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    workspace_id: str | None = None


# ----------------------------------------------------------------------
# v23.0 Agent-to-Agent Network
# ----------------------------------------------------------------------
class AgentContractCreateRequest(BaseModel):
    source_agent: str = Field(default="", max_length=160)
    target_agent: str = Field(default="", max_length=160)
    task: str = Field(..., min_length=1, max_length=2000)
    expected_output: str = Field(default="", max_length=2000)
    constraints: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", pattern="^(draft|sent|accepted|completed|failed|verified)$")


class AgentContractUpdateRequest(BaseModel):
    source_agent: str | None = Field(default=None, max_length=160)
    target_agent: str | None = Field(default=None, max_length=160)
    task: str | None = Field(default=None, max_length=2000)
    expected_output: str | None = Field(default=None, max_length=2000)
    constraints: list[str] | None = None
    status: str | None = Field(default=None, pattern="^(draft|sent|accepted|completed|failed|verified)$")


class AgentHandoffCreateRequest(BaseModel):
    handoff_type: str = Field(default="local", pattern="^(local|external_mock)$")
    payload: dict = Field(default_factory=dict)
