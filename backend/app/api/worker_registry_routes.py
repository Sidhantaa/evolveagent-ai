"""worker registry + Kaggle worker routes (v220 Compute Fabric)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    worker_registry_service,
    kaggle_worker_service,
)
from app.models.request_models import (
    KaggleJobSubmitRequest,
    WorkerHeartbeatRequest,
    WorkerRegisterRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v220 Compute Fabric -- Worker Registry
# ----------------------------------------------------------------------
@router.get("/worker-registry/dashboard")
def get_worker_registry_dashboard() -> dict:
    return worker_registry_service.dashboard()


@router.get("/worker-registry/workers")
def list_workers(status: str | None = None) -> dict:
    workers = worker_registry_service.list_workers(status=status)
    return {"workers": workers, "count": len(workers)}


@router.post("/worker-registry/workers")
def register_worker(request: WorkerRegisterRequest) -> dict:
    return worker_registry_service.register_worker(
        worker_type=request.worker_type, capabilities=request.capabilities, metadata=request.metadata,
    )


@router.post("/worker-registry/workers/{worker_id}/heartbeat")
def worker_heartbeat(worker_id: str, request: WorkerHeartbeatRequest | None = None) -> dict:
    payload = request or WorkerHeartbeatRequest()
    try:
        return worker_registry_service.heartbeat(worker_id, status=payload.status)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Worker not found") from error


@router.delete("/worker-registry/workers/{worker_id}")
def deregister_worker(worker_id: str) -> dict:
    try:
        return worker_registry_service.deregister_worker(worker_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Worker not found") from error


# ----------------------------------------------------------------------
# v220 Compute Fabric -- real (opt-in) Kaggle GPU worker
# ----------------------------------------------------------------------
@router.get("/worker-registry/kaggle/jobs")
def list_kaggle_jobs() -> dict:
    jobs = kaggle_worker_service.list_jobs()
    return {"jobs": jobs, "count": len(jobs)}


@router.post("/worker-registry/kaggle/jobs")
def submit_kaggle_job(request: KaggleJobSubmitRequest) -> dict:
    try:
        return kaggle_worker_service.submit_job(code=request.code, title=request.title, workspace_id=request.workspace_id)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/worker-registry/kaggle/jobs/{job_id}")
def get_kaggle_job(job_id: str) -> dict:
    job = kaggle_worker_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/worker-registry/kaggle/jobs/{job_id}/poll")
def poll_kaggle_job(job_id: str) -> dict:
    try:
        return kaggle_worker_service.poll_job(job_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Job not found") from error


@router.get("/worker-registry/kaggle/jobs/{job_id}/output")
def get_kaggle_job_output(job_id: str) -> dict:
    try:
        return kaggle_worker_service.get_job_output(job_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Job not found") from error
