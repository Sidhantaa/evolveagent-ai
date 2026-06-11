from datetime import UTC, datetime
from collections import Counter
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.agents.learning_agent import LearningAgent
from app.agents.master_agent import MasterOrchestratorAgent
from app.agents.memory_agent import MemoryAgent
from app.models.request_models import (
    AutomationApplyRequest,
    CreateChatRequest,
    CreateCustomAgentRequest,
    CreateGoalRequest,
    CreateGoalTaskRequest,
    CreateWorkspaceMemoryRequest,
    CreateWorkspaceRequest,
    FeedbackRequest,
    PromptDecisionRequest,
    PromptProposalRequest,
    RenameChatRequest,
    RunRequest,
    UpdateCustomAgentRequest,
    UpdateGoalRequest,
    UpdateGoalTaskRequest,
    UpdateWorkspaceMemoryRequest,
    UpdateWorkspaceRequest,
    LinearCommentRequest,
    LinearCursorVerifyRequest,
)
from app.models.response_models import AutomationApplyResult, GovernanceEvent, ProviderStatus, RunResponse
from app.services.governance_service import GovernanceService
from app.services.custom_agent_service import CustomAgentService
from app.services.goal_service import GoalService
from app.services.llm_router import llm_router
from app.services.permission_service import PermissionService
from app.services.file_service import FileService
from app.services.prompt_version_service import PromptVersionService
from app.services.recording_service import RecordingService
from app.services.safe_command_runner import SafeCommandRunner
from app.services.safe_file_editor import SafeFileEditor
from app.services.storage_service import StorageService
from app.services.workspace_service import WorkspaceService
from app.services.user_preference_service import UserPreferenceService
from app.services.workflow_strategy_service import WorkflowStrategyService
from app.services.linear_service import LinearService, LinearServiceError
from app.services.linear_link_service import LinearLinkService
from app.services.linear_orchestration_service import LinearOrchestrationService
from app.services.linear_poll_worker import LinearPollWorker
from app.services.git_service import GitService
from app.services.secret_scanner import SecretScanner

router = APIRouter()
storage = StorageService()
memory_agent = MemoryAgent(storage)
master_agent = MasterOrchestratorAgent(storage=storage, memory_agent=memory_agent)
file_service = FileService(storage)
recording_service = RecordingService(storage)
safe_file_editor = SafeFileEditor()
safe_command_runner = SafeCommandRunner()
permission_service = PermissionService()
governance_service = GovernanceService(storage)
prompt_versions = PromptVersionService(storage)
learning_agent = LearningAgent(storage)
workflow_strategy = WorkflowStrategyService(storage)
user_preferences = UserPreferenceService(storage)
goal_service = GoalService(storage)
custom_agent_service = CustomAgentService(storage)
workspace_service = WorkspaceService(storage)
linear_service = LinearService(SecretScanner())
linear_link_service = LinearLinkService(storage)
git_service = GitService()
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
linear_poll_worker = LinearPollWorker(linear_service, linear_orchestration)


def filter_by_workspace(items: list[dict], workspace_id: str | None = None) -> list[dict]:
    if not workspace_id:
        return items
    return [item for item in items if item.get("workspace_id") == workspace_id]


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
) -> list[dict]:
    return workspace_service.list_memory(workspace_id, query=q, memory_type=memory_type)


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


@router.post("/run", response_model=RunResponse)
def run_workflow(request: RunRequest) -> RunResponse:
    return master_agent.run(request)


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

    if not request.approved:
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
    result = safe_file_editor.apply_plan_conservatively(automation_plan)
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


@router.get("/learning/report")
def get_learning_report(workspace_id: str | None = Query(default=None)) -> dict:
    resolved = workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
    return learning_agent.report(workspace_id=resolved)


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
        "recent_runs": list(reversed(runs[-10:])),
    }


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


@router.get("/providers/status", response_model=ProviderStatus)
def get_provider_status() -> ProviderStatus:
    return llm_router.status()


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
