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


# ----------------------------------------------------------------------
# v24.0 Self-Healing Project System
# ----------------------------------------------------------------------
class SelfHealingCheckRequest(BaseModel):
    command: str = Field(default="pytest", max_length=120)
    mode: str = Field(default="run", pattern="^(run|mock)$")
    mock_stdout: str = Field(default="", max_length=8000)
    mock_stderr: str = Field(default="", max_length=8000)
    mock_exit_code: int = Field(default=0, ge=0, le=255)
    workspace_id: str | None = None


class SelfHealingVerifyRequest(BaseModel):
    mode: str = Field(default="run", pattern="^(run|mock)$")
    mock_stdout: str = Field(default="", max_length=8000)
    mock_stderr: str = Field(default="", max_length=8000)
    mock_exit_code: int = Field(default=0, ge=0, le=255)


# ----------------------------------------------------------------------
# v25.0 AI Company Brain
# ----------------------------------------------------------------------
class CompanyStrategyRequest(BaseModel):
    title: str = Field(default="", max_length=200)
    horizon: str = Field(default="quarter", max_length=40)
    objectives: list[str] = Field(default_factory=list)
    focus_areas: list[str] = Field(default_factory=list)


class CompanyDecisionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    context: str = Field(default="", max_length=2000)
    decision: str = Field(default="", max_length=2000)
    rationale: str = Field(default="", max_length=2000)
    impact: str = Field(default="medium", pattern="^(low|medium|high)$")


class CompanyReportRequest(BaseModel):
    workspace_id: str | None = None


# ----------------------------------------------------------------------
# v26.0 Personal Device Operator / Phone Autopilot
# ----------------------------------------------------------------------
class DeviceSessionCreateRequest(BaseModel):
    device_label: str = Field(default="", max_length=120)
    permission_level: str = Field(
        default="suggest_only",
        pattern="^(suggest_only|read_screen_only|tap_type_with_confirmation|auto_safe_actions|blocked)$",
    )
    workspace_id: str | None = None


class DevicePlanRequest(BaseModel):
    command: str = Field(default="", max_length=2000)
    screen_text: str = Field(default="", max_length=8000)


class DeviceConfirmActionRequest(BaseModel):
    action_id: str = Field(..., min_length=1, max_length=120)
    approve: bool = Field(default=False)


# ----------------------------------------------------------------------
# v27.0 Private Training Lab
# ----------------------------------------------------------------------
class TrainingDatasetCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)
    purpose: str = Field(default="fine_tuning_preparation", max_length=200)


class TrainingExampleCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=20000)
    completion: str = Field(default="", max_length=20000)
    approved: bool = Field(default=False)


class TrainingExampleUpdateRequest(BaseModel):
    status: str | None = Field(default=None, pattern="^(pending|approved|rejected)$")
    prompt: str | None = Field(default=None, max_length=20000)
    completion: str | None = Field(default=None, max_length=20000)


class TrainingRunCreateRequest(BaseModel):
    dataset_id: str | None = Field(default=None, max_length=120)
    base_model: str = Field(default="", max_length=120)
    method: str = Field(default="lora", max_length=60)


class TrainingComparisonRequest(BaseModel):
    baseline_model: str = Field(default="", max_length=120)
    candidate_model: str = Field(default="", max_length=120)
    metric: str = Field(default="win_rate", max_length=80)
    baseline_score: float = Field(default=0)
    candidate_score: float = Field(default=0)


# ----------------------------------------------------------------------
# v28.0 Personal AI Avatar / Voice Twin
# ----------------------------------------------------------------------
class AvatarPersonaUpdateRequest(BaseModel):
    avatar_name: str | None = Field(default=None, max_length=80)
    tone: str | None = Field(default=None, pattern="^(friendly|professional|concise|encouraging|neutral)$")
    format: str | None = Field(default=None, pattern="^(bullets|paragraph|step_by_step|summary_first)$")
    style: str | None = Field(default=None, max_length=200)


class AvatarVoiceSettingsUpdateRequest(BaseModel):
    voice_mode: str | None = Field(default=None, pattern="^(text_only|spoken_summary_ready|disabled)$")
    spoken_summary_max_chars: int | None = Field(default=None, ge=100, le=2000)


class AvatarMeetingSessionRequest(BaseModel):
    title: str = Field(default="", max_length=200)
    context: str = Field(default="", max_length=4000)


class AvatarConsentRequest(BaseModel):
    scope: str = Field(default="persona_behavior", max_length=120)
    granted: bool = Field(default=False)
    note: str = Field(default="", max_length=1000)


class AvatarImageRequest(BaseModel):
    description: str = Field(default="", max_length=600, description="Self-description for a stylized avatar (not a photo-real clone).")
    style: str = Field(default="illustrated", pattern="^(illustrated|cartoon|minimal|3d_stylized|pixel)$")


# ----------------------------------------------------------------------
# v29.0 Real-Time Life Operating System
# ----------------------------------------------------------------------
class LifeScheduleCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    date: str = Field(default="", max_length=10)
    start_time: str = Field(default="", max_length=10)
    end_time: str = Field(default="", max_length=10)
    location: str = Field(default="", max_length=200)
    notes: str = Field(default="", max_length=1000)
    workspace_id: str | None = None


class LifeTaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    due_date: str = Field(default="", max_length=10)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    importance: str = Field(default="medium", pattern="^(low|medium|high)$")
    status: str = Field(default="todo", pattern="^(todo|in_progress|done|archived)$")
    notes: str = Field(default="", max_length=1000)
    workspace_id: str | None = None


class LifeTaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    due_date: str | None = Field(default=None, max_length=10)
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")
    importance: str | None = Field(default=None, pattern="^(low|medium|high)$")
    status: str | None = Field(default=None, pattern="^(todo|in_progress|done|archived)$")
    notes: str | None = Field(default=None, max_length=1000)


class LifeReminderCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    remind_on: str = Field(default="", max_length=10)
    status: str = Field(default="open", pattern="^(open|done|snoozed)$")
    notes: str = Field(default="", max_length=1000)
    workspace_id: str | None = None


class LifeDeadlineCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    kind: str = Field(default="other", pattern="^(school|work|personal|other)$")
    due_date: str = Field(default="", max_length=10)
    course_or_project: str = Field(default="", max_length=200)
    notes: str = Field(default="", max_length=1000)
    workspace_id: str | None = None


class LifeDailyPlanRequest(BaseModel):
    workspace_id: str | None = None


# ----------------------------------------------------------------------
# v30.0 Universal App Operator
# ----------------------------------------------------------------------
class UniversalSessionCreateRequest(BaseModel):
    label: str = Field(default="", max_length=160)
    surface: str = Field(default="cross_app", pattern="^(desktop|browser|mobile|cross_app)$")
    apps: list[str] = Field(default_factory=list)
    workspace_id: str | None = None


class UniversalWorkflowCreateRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=2000)
    steps: list[str] = Field(default_factory=list)
    session_id: str | None = Field(default=None, max_length=120)
    workspace_id: str | None = None


class UniversalActionDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject)$")


class UniversalHandoffCreateRequest(BaseModel):
    workflow_id: str | None = Field(default=None, max_length=120)
    from_device: str = Field(default="", max_length=120)
    to_device: str = Field(default="", max_length=120)
    summary: str = Field(default="", max_length=1000)


# ----------------------------------------------------------------------
# v32.0 Autonomous SaaS Builder
# ----------------------------------------------------------------------
class SaaSProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    idea: str = Field(default="", max_length=4000)


class SaaSFeedbackCreateRequest(BaseModel):
    type: str = Field(default="feature", pattern="^(feature|bug|improvement|question)$")
    title: str = Field(..., min_length=1, max_length=200)
    detail: str = Field(default="", max_length=2000)
    linked_phase: str = Field(default="", max_length=60)
    status: str = Field(default="open", pattern="^(open|planned|resolved|wont_do)$")
# v31.0 AI Team Lead / Manager Mode
# ----------------------------------------------------------------------
class TeamMemberCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    member_type: str = Field(default="human", pattern="^(human|ai_agent)$")
    role: str = Field(default="", max_length=160)
    skills: list[str] = Field(default_factory=list)


class TeamMemberUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=160)
    member_type: str | None = Field(default=None, pattern="^(human|ai_agent)$")
    role: str | None = Field(default=None, max_length=160)
    skills: list[str] | None = None
    active: bool | None = None


class TeamAssignmentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    owner_id: str | None = Field(default=None, max_length=120)
    owner_name: str = Field(default="", max_length=160)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    status: str = Field(default="todo", pattern="^(todo|in_progress|blocked|done|archived)$")
    due_date: str = Field(default="", max_length=10)
    blocked_reason: str = Field(default="", max_length=500)


class TeamAssignmentUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    owner_id: str | None = Field(default=None, max_length=120)
    owner_name: str | None = Field(default=None, max_length=160)
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")
    status: str | None = Field(default=None, pattern="^(todo|in_progress|blocked|done|archived)$")
    due_date: str | None = Field(default=None, max_length=10)
    blocked_reason: str | None = Field(default=None, max_length=500)


class TeamSprintCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    goals: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    owners: list[str] = Field(default_factory=list)
    start_date: str = Field(default="", max_length=10)
    end_date: str = Field(default="", max_length=10)


class TeamSprintReviewRequest(BaseModel):
    summary: str = Field(default="", max_length=2000)
    carry_over: list[str] = Field(default_factory=list)
    learnings: list[str] = Field(default_factory=list)


# ----------------------------------------------------------------------
# v33.0 AI Business Operator Advanced
# ----------------------------------------------------------------------
class BusinessWorkflowCreateRequest(BaseModel):
    workflow_type: str = Field(default="custom", pattern="^(lead_pipeline|support_triage|invoice_processing|custom)$")
    title: str = Field(default="", max_length=200)
    context: str = Field(default="", max_length=2000)
    status: str = Field(default="queued", pattern="^(queued|in_review|completed|blocked)$")


class BusinessReportCreateRequest(BaseModel):
    title: str = Field(default="", max_length=200)
    period: str = Field(default="current", max_length=40)


class BusinessApprovalCreateRequest(BaseModel):
    kind: str = Field(default="high_risk", pattern="^(external_send|payment|high_risk|data_share)$")
    title: str = Field(..., min_length=1, max_length=200)
    detail: str = Field(default="", max_length=2000)


class BusinessApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")


# ----------------------------------------------------------------------
# v34.0 Legal / Compliance Intelligence Layer
# ----------------------------------------------------------------------
class CompliancePolicyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    category: str = Field(default="general", max_length=80)
    rules: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", pattern="^(draft|active|archived)$")


class CompliancePolicyUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=160)
    category: str | None = Field(default=None, max_length=80)
    rules: list[str] | None = None
    status: str | None = Field(default=None, pattern="^(draft|active|archived)$")


class ComplianceScanRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=20000)
    label: str = Field(default="", max_length=160)


class ComplianceContractReviewRequest(BaseModel):
    title: str = Field(default="", max_length=200)
    content: str = Field(..., min_length=1, max_length=20000)


class ComplianceChecklistRequest(BaseModel):
    title: str = Field(default="", max_length=200)
    framework: str = Field(default="general", max_length=80)
    items: list[str] = Field(default_factory=list)


class ComplianceAuditPackageRequest(BaseModel):
    title: str = Field(default="", max_length=200)


# ----------------------------------------------------------------------
# v35.0 AI Executive Board
# ----------------------------------------------------------------------
class ExecutiveBoardSessionCreateRequest(BaseModel):
    title: str = Field(default="", max_length=200)
    decision: str = Field(..., min_length=1, max_length=2000)
    context: str = Field(default="", max_length=4000)


class ExecutiveBoardVoteRequest(BaseModel):
    role: str = Field(
        default="CEO",
        pattern="^(CEO|CTO|CFO|COO|Legal/Compliance|Product|Marketing|Security)$",
    )
    vote: str = Field(default="abstain", pattern="^(approve|reject|abstain)$")
    rationale: str = Field(default="", max_length=1000)


# ----------------------------------------------------------------------
# v36.0 Autonomous Research + Innovation Lab
# ----------------------------------------------------------------------
class InnovationResearchRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    source: str = Field(default="", max_length=300)
    credibility: str = Field(default="medium", pattern="^(low|medium|high)$")
    notes: str = Field(default="", max_length=4000)
    tags: list[str] = Field(default_factory=list)


class InnovationCompetitorRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(default="", max_length=120)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=2000)


class InnovationTrendRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    direction: str = Field(default="rising", pattern="^(rising|flat|declining)$")
    evidence_notes: list[str] = Field(default_factory=list)
    confidence: str = Field(default="medium", pattern="^(low|medium|high)$")


class InnovationIdeaRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    impact: int = Field(default=3, ge=1, le=5)
    feasibility: int = Field(default=3, ge=1, le=5)
    novelty: int = Field(default=3, ge=1, le=5)
    risk: int = Field(default=3, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)


class InnovationExperimentRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    hypothesis: str = Field(default="", max_length=2000)
    method: str = Field(default="", max_length=2000)
    success_metrics: list[str] = Field(default_factory=list)


class InnovationPrototypeRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    phases: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class InnovationReportRequest(BaseModel):
    title: str = Field(default="", max_length=200)


# ----------------------------------------------------------------------
# v37.0 AI Simulation World
# ----------------------------------------------------------------------
class SimulationWorldCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)


class SimulationPersonaCreateRequest(BaseModel):
    world_id: str | None = Field(default=None, max_length=120)
    name: str = Field(..., min_length=1, max_length=160)
    persona_type: str = Field(default="user", pattern="^(user|customer|stakeholder|other)$")
    goals: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)


class SimWorldScenarioCreateRequest(BaseModel):
    world_id: str | None = Field(default=None, max_length=120)
    title: str = Field(..., min_length=1, max_length=200)
    scenario_type: str = Field(default="business", pattern="^(business|product|project|bug|risk|launch)$")
    description: str = Field(default="", max_length=4000)
    assumptions: list[str] = Field(default_factory=list)


class SimulationCompareRequest(BaseModel):
    scenario_ids: list[str] = Field(default_factory=list)


class SimulationReportRequest(BaseModel):
    title: str = Field(default="", max_length=200)


# ----------------------------------------------------------------------
# v38.0 Multi-User Organization OS (local records only — no auth)
# ----------------------------------------------------------------------
class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)


class OrganizationMemberCreateRequest(BaseModel):
    organization_id: str | None = Field(default=None, max_length=120)
    display_name: str = Field(..., min_length=1, max_length=160)
    role: str = Field(default="contributor", pattern="^(owner|admin|manager|contributor|viewer)$")


class OrganizationMemberUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=160)
    role: str | None = Field(default=None, pattern="^(owner|admin|manager|contributor|viewer)$")
    active: bool | None = None


class OrganizationRoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    permissions: list[str] = Field(default_factory=list)


class OrganizationWorkspaceLinkRequest(BaseModel):
    organization_id: str | None = Field(default=None, max_length=120)
    workspace_id: str | None = Field(default=None, max_length=120)
    workspace_name: str = Field(default="", max_length=160)


# ----------------------------------------------------------------------
# v39.0 AI Hardware / Always-On Companion (readiness/planning only)
# ----------------------------------------------------------------------
class HardwareDeviceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    device_type: str = Field(default="other", pattern="^(phone|laptop|desktop|speaker|wearable|other)$")
    has_mic: bool = Field(default=False)
    has_speaker: bool = Field(default=False)
    local_processing: bool = Field(default=False)


class HardwareDeviceUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=160)
    device_type: str | None = Field(default=None, pattern="^(phone|laptop|desktop|speaker|wearable|other)$")
    has_mic: bool | None = None
    has_speaker: bool | None = None
    local_processing: bool | None = None


class CompanionSettingsUpdateRequest(BaseModel):
    companion_mode: str | None = Field(default=None, pattern="^(disabled|push_to_talk_ready|local_only_ready)$")


class CompanionReadinessCheckRequest(BaseModel):
    device_id: str | None = Field(default=None, max_length=120)


class CompanionSessionCreateRequest(BaseModel):
    device_id: str | None = Field(default=None, max_length=120)
    title: str = Field(default="", max_length=200)
    notes: str = Field(default="", max_length=4000)


# ----------------------------------------------------------------------
# v41.0 MCP Connector Hub (planning-first; no real MCP execution)
# ----------------------------------------------------------------------
class MCPConnectorCreateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    slug: str | None = Field(default=None, max_length=60)
    description: str = Field(default="", max_length=600)
    category: str = Field(default="custom", pattern="^(development|productivity|knowledge|browser|desktop|custom)$")
    mode: str = Field(default="approval_required", pattern="^(read_only|approval_required|disabled)$")
    risk_level: str = Field(default="medium", pattern="^(low|medium|high)$")
    server_type: str = Field(default="local_mock", pattern="^(stdio|http|local_mock|external)$")
    enabled: bool = Field(default=False)
    args: list[str] = Field(default_factory=list)
    env_keys_required: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)
    blocked_actions: list[str] = Field(default_factory=list)
    workspace_scope: str = Field(default="global", pattern="^(global|workspace)$")


class MCPConnectorUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=600)
    category: str | None = Field(default=None, pattern="^(development|productivity|knowledge|browser|desktop|custom)$")
    mode: str | None = Field(default=None, pattern="^(read_only|approval_required|disabled)$")
    risk_level: str | None = Field(default=None, pattern="^(low|medium|high)$")
    server_type: str | None = Field(default=None, pattern="^(stdio|http|local_mock|external)$")
    args: list[str] | None = None
    env_keys_required: list[str] | None = None
    capabilities: list[str] | None = None
    allowed_actions: list[str] | None = None
    blocked_actions: list[str] | None = None
    workspace_scope: str | None = Field(default=None, pattern="^(global|workspace)$")


class MCPPlanActionRequest(BaseModel):
    action_name: str = Field(..., min_length=1, max_length=80)
    payload: dict = Field(default_factory=dict)
    workspace_id: str | None = Field(default=None, max_length=120)


# ----------------------------------------------------------------------
# v42.0 MCP Execution Adapter (approval-gated, mock-by-default)
# ----------------------------------------------------------------------
class MCPExecuteRequest(BaseModel):
    action_name: str = Field(..., min_length=1, max_length=80)
    payload: dict = Field(default_factory=dict)
    workspace_id: str | None = Field(default=None, max_length=120)


# ----------------------------------------------------------------------
# v45.0 MCP Policy Engine (tighten-only deny rules)
# ----------------------------------------------------------------------
class MCPPolicyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=400)
    connector_slug: str = Field(default="*", max_length=60)
    action: str = Field(default="*", max_length=80)
    risk_level: str = Field(default="*", pattern="^(\\*|low|medium|high)$")
    except_actions: list[str] = Field(default_factory=list)
    enabled: bool = Field(default=True)


class MCPPolicyUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=400)
    connector_slug: str | None = Field(default=None, max_length=60)
    action: str | None = Field(default=None, max_length=80)
    risk_level: str | None = Field(default=None, pattern="^(\\*|low|medium|high)$")
    except_actions: list[str] | None = None
    enabled: bool | None = None


class MCPPolicyEvaluateRequest(BaseModel):
    connector_id: str = Field(..., min_length=1, max_length=120)
    action_name: str = Field(..., min_length=1, max_length=80)


# ----------------------------------------------------------------------
# v46.0 MCP Audit & Replay
# ----------------------------------------------------------------------
class MCPReplayRequest(BaseModel):
    request_id: str = Field(..., min_length=1, max_length=120)


# ----------------------------------------------------------------------
# v47.0 Secret Reference Registry (references only — never values)
# ----------------------------------------------------------------------
class MCPSecretRefCreateRequest(BaseModel):
    key_name: str = Field(..., min_length=1, max_length=120)
    label: str = Field(default="", max_length=160)
    owner: str = Field(default="", max_length=120)
    category: str = Field(default="api_key", pattern="^(api_key|token|webhook|database|other)$")
    connector_slug: str = Field(default="", max_length=60)
    rotation_days: int = Field(default=0, ge=0, le=3650)


class MCPSecretRefUpdateRequest(BaseModel):
    label: str | None = Field(default=None, max_length=160)
    owner: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, pattern="^(api_key|token|webhook|database|other)$")
    rotation_days: int | None = Field(default=None, ge=0, le=3650)


# ----------------------------------------------------------------------
# v48.0 Unified Approvals Center
# ----------------------------------------------------------------------
class ApprovalDecisionRequest(BaseModel):
    source: str = Field(..., pattern="^(mcp_execution|business_operator)$")
    item_id: str = Field(..., min_length=1, max_length=120)


# ----------------------------------------------------------------------
# v50.0 Cost & Usage Ledger (estimates only — no billing)
# ----------------------------------------------------------------------
class UsageRecordRequest(BaseModel):
    workspace_id: str | None = Field(default=None, max_length=120)
    capability: str = Field(default="other", pattern="^(text|image|transcription|mcp|other)$")
    units: float = Field(default=1.0, ge=0)
    estimated_cost: float | None = Field(default=None, ge=0)
    mode: str = Field(default="mock", pattern="^(mock|real)$")


class UsageBudgetRequest(BaseModel):
    workspace_id: str | None = Field(default=None, max_length=120)
    monthly_limit: float = Field(..., ge=0)


# ----------------------------------------------------------------------
# v51.0 Local Retrieval Layer (local-only)
# ----------------------------------------------------------------------
class RetrievalIndexRequest(BaseModel):
    workspace_id: str | None = Field(default=None, max_length=120)
    title: str = Field(default="", max_length=200)
    content: str = Field(..., min_length=1, max_length=40000)


class RetrievalQueryRequest(BaseModel):
    workspace_id: str | None = Field(default=None, max_length=120)
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)


# ----------------------------------------------------------------------
# v52.0 Evaluation Harness 2.0
# ----------------------------------------------------------------------
class EvalCaseModel(BaseModel):
    prompt: str = Field(default="", max_length=2000)
    reference_answer: str = Field(default="", max_length=4000)
    expected_keywords: list[str] = Field(default_factory=list)


class EvalSuiteCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    cases: list[EvalCaseModel] = Field(default_factory=list)


# ----------------------------------------------------------------------
# v53.0 Playbook Library
# ----------------------------------------------------------------------
class PlaybookStepModel(BaseModel):
    title: str = Field(default="", max_length=200)
    step_type: str = Field(default="plan", pattern="^(plan|note|approval_required)$")
    detail: str = Field(default="", max_length=2000)


class PlaybookCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    description: str = Field(default="", max_length=1000)
    steps: list[PlaybookStepModel] = Field(default_factory=list)


# ----------------------------------------------------------------------
# Task-aware MCP suggestion (voice/ask console)
# ----------------------------------------------------------------------
class MCPSuggestRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=500)


# ----------------------------------------------------------------------
# Master Agent — single top-level AI surface over all of v1–v60
# ----------------------------------------------------------------------
class MasterAgentRouteRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    workspace_id: str | None = Field(default=None)
    voice_used: bool = Field(default=False)
    execute: bool = Field(default=False, description="Only honored for non-risky intents; risky actions still require explicit approval.")


class MasterRouteFeedbackRequest(BaseModel):
    correct: bool = Field(..., description="Was the Master Agent's route correct for this request?")
    correct_domain: str | None = Field(default=None, max_length=80, description="If incorrect, the domain it should have routed to.")
    note: str = Field(default="", max_length=500)


# ----------------------------------------------------------------------
# Settings Center (v67)
# ----------------------------------------------------------------------
class SettingsUpdateRequest(BaseModel):
    settings: dict = Field(default_factory=dict, description="Partial settings by category; only allow-listed keys are applied. No secret values.")


class SettingsImportRequest(BaseModel):
    settings: dict = Field(default_factory=dict)


# ----------------------------------------------------------------------
# Provider Control Center (v68)
# ----------------------------------------------------------------------
class ProviderControlUpdateRequest(BaseModel):
    model_by_task: dict | None = Field(default=None, description="task_type → model name preference.")
    capability_modes: dict | None = Field(default=None, description="capability → 'mock' | 'real' preference.")
    fallback_enabled: bool | None = Field(default=None)


# ----------------------------------------------------------------------
# Smart Context Engine (v71)
# ----------------------------------------------------------------------
class ContextPlanRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    workspace_id: str | None = Field(default=None)
    budget_chars: int = Field(default=4000, ge=200, le=20000)


# ----------------------------------------------------------------------
# Workflow Recommendation Engine (v73)
# ----------------------------------------------------------------------
class WorkflowRecommendRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=2000)
    task_type: str | None = Field(default=None)


# ----------------------------------------------------------------------
# Document Intelligence 2.0 (v75)
# ----------------------------------------------------------------------
class DocCompareRequest(BaseModel):
    text_a: str = Field(..., min_length=1, max_length=50000)
    text_b: str = Field(..., min_length=1, max_length=50000)


class AtsScoreRequest(BaseModel):
    resume_text: str = Field(..., min_length=1, max_length=50000)
    job_keywords: list[str] = Field(default_factory=list)


class DocTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=100000)


class DocQARequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=100000)
    question: str = Field(..., min_length=1, max_length=1000)


# ----------------------------------------------------------------------
# Code Intelligence 2.0 (v76)
# ----------------------------------------------------------------------
class CodeAnalyzeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=200000)
    language: str = Field(default="python", max_length=30)


class CodeTextRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=200000)


# ----------------------------------------------------------------------
# Research Agent 2.0 (v77)
# ----------------------------------------------------------------------
class ResearchSourcesRequest(BaseModel):
    sources: list[dict] = Field(default_factory=list, description="List of {title, text} sources.")


class ResearchBriefRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    sources: list[dict] = Field(default_factory=list)


class ResearchTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=100000)


# ----------------------------------------------------------------------
# Meeting Intelligence 2.0 (v79)
# ----------------------------------------------------------------------
class MeetingAnalyzeRequest(BaseModel):
    transcript: str = Field(..., min_length=1, max_length=200000)


class MeetingToGoalRequest(BaseModel):
    transcript: str = Field(..., min_length=1, max_length=200000)
    title: str | None = Field(default=None, max_length=200)


# ----------------------------------------------------------------------
# Multi-Agent Collaboration 2.0 (v80)
# ----------------------------------------------------------------------
class CollaborationRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    contributions: list[dict] = Field(default_factory=list, description="List of {role, position} agent contributions.")


# ----------------------------------------------------------------------
# Permission System 3.0 (v81)
# ----------------------------------------------------------------------
class PermissionProfileRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    scope_type: str = Field(default="global")
    scope_value: str = Field(default="*", max_length=120)
    action_pattern: str = Field(default="*", max_length=120)
    effect: str = Field(default="require_approval")
    risk_level: str = Field(default="high")


class PermissionEvaluateRequest(BaseModel):
    scope_type: str = Field(default="global")
    scope_value: str = Field(default="*", max_length=120)
    action: str = Field(..., min_length=1, max_length=120)
    risk_level: str = Field(default="medium")


# ----------------------------------------------------------------------
# Local Data Manager (v83)
# ----------------------------------------------------------------------
class RedactionPreviewRequest(BaseModel):
    collection: str = Field(..., min_length=1, max_length=120)


# ----------------------------------------------------------------------
# Import Center (v84)
# ----------------------------------------------------------------------
class ImportPreviewRequest(BaseModel):
    kind: str = Field(..., min_length=1, max_length=40)
    content: str = Field(..., min_length=1, max_length=500000)


class ImportCommitRequest(BaseModel):
    kind: str = Field(..., min_length=1, max_length=40)
    content: str = Field(..., min_length=1, max_length=500000)
    workspace_id: str | None = Field(default=None)


# ----------------------------------------------------------------------
# Export Center (v85)
# ----------------------------------------------------------------------
class ExportRequest(BaseModel):
    kind: str = Field(..., min_length=1, max_length=40)
    format: str = Field(default="markdown")
    workspace_id: str | None = Field(default=None)


class ExportPackageRequest(BaseModel):
    kinds: list[str] = Field(default_factory=list)
    format: str = Field(default="markdown")
    workspace_id: str | None = Field(default=None)


# ----------------------------------------------------------------------
# Plugin Marketplace 3.0 (v86)
# ----------------------------------------------------------------------
class PluginRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    permissions: list[str] = Field(default_factory=list)


class PluginToggleRequest(BaseModel):
    enabled: bool


# ----------------------------------------------------------------------
# v57.0 Workspace Templates & Cloning
# ----------------------------------------------------------------------
class WorkspaceTemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    description: str = Field(default="", max_length=1000)
    default_tags: list[str] = Field(default_factory=list)
    preset: dict = Field(default_factory=dict)


class WorkspaceTemplateInstantiateRequest(BaseModel):
    name: str = Field(default="", max_length=160)


# ----------------------------------------------------------------------
# v58.0 Scheduled Tasks (local, planning-first)
# ----------------------------------------------------------------------
class ScheduledTaskCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    schedule: str = Field(default="manual", pattern="^(manual|hourly|daily|weekly)$")
    action_type: str = Field(default="plan", pattern="^(plan|note|approval_required)$")
    detail: str = Field(default="", max_length=2000)
    enabled: bool = Field(default=True)


class ScheduledTaskToggleRequest(BaseModel):
    enabled: bool


# ----------------------------------------------------------------------
# v59.0 Data Export & Backup
# ----------------------------------------------------------------------
class DataImportRequest(BaseModel):
    bundle: dict = Field(default_factory=dict)
