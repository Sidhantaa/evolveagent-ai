"""goals routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from app.api.routes import (
    goal_service,
    governance_service,
    workspace_service,
    GoalService,
    GovernanceEvent,
    LinearServiceError,
    RunResponse,
    linear_orchestration,
    master_agent,
)
from app.models.request_models import (
    CreateGoalRequest,
    CreateGoalTaskRequest,
    RunRequest,
    UpdateGoalRequest,
    UpdateGoalTaskRequest,
)

router = APIRouter()


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
