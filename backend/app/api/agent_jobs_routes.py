"""agent-jobs routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from app.api.routes import (
    agent_scheduler,
)
from app.models.request_models import (
    AgentJobActionRequest,
    CreateAgentJobRequest,
)

router = APIRouter()


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
