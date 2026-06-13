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


class AutomationApplyRequest(BaseModel):
    run_id: str
    approved: bool


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


class LinearCommentRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=8000)


class LinearCursorVerifyRequest(BaseModel):
    completion_note: str | None = Field(default=None, max_length=2000)
    auto_commit: bool = Field(default=False, description="Stage and commit safe files after verification passes.")
