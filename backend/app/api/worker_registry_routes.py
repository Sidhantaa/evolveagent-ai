"""worker registry + Kaggle worker routes (v220 Compute Fabric)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    worker_registry_service,
    kaggle_worker_service,
    runpod_worker_service,
    gpu_worker_service,
    model_serving_service,
)
from app.models.request_models import (
    GPUDryRunRequest,
    KaggleJobSubmitRequest,
    LocalGPUWorkerRegisterRequest,
    ModelServingDryRunRequest,
    RunPodJobSubmitRequest,
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
# v240 GPU worker expansion -- readiness + dry-run only
# ----------------------------------------------------------------------
@router.get("/worker-registry/gpu/dashboard")
def get_gpu_worker_dashboard() -> dict:
    return gpu_worker_service.dashboard()


@router.get("/worker-registry/gpu/providers")
def get_gpu_worker_providers() -> dict:
    return gpu_worker_service.providers()


@router.post("/worker-registry/gpu/dry-run")
def dry_run_gpu_worker(request: GPUDryRunRequest) -> dict:
    return gpu_worker_service.dry_run(request.model_dump())


@router.post("/worker-registry/gpu/local-workers")
def register_local_gpu_worker(request: LocalGPUWorkerRegisterRequest) -> dict:
    return gpu_worker_service.register_local_worker(request.model_dump())


# ----------------------------------------------------------------------
# v260 Distributed model serving -- readiness/dry-run only. Never starts,
# installs, or supervises a model-server process; detect() only GETs an
# operator-configured, already-running local endpoint.
# ----------------------------------------------------------------------
@router.get("/model-serving/dashboard")
def get_model_serving_dashboard() -> dict:
    return model_serving_service.dashboard()


@router.post("/model-serving/dry-run")
def dry_run_model_serving(request: ModelServingDryRunRequest) -> dict:
    return model_serving_service.dry_run(request.model_dump())


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


# ----------------------------------------------------------------------
# v240+ Compute Fabric -- real RunPod worker status/poll/output.
# Submission is intentionally routed through DurableWorkflowService's
# approval-gated run_runpod_job action, not this direct API route.
# ----------------------------------------------------------------------
@router.get("/worker-registry/runpod/jobs")
def list_runpod_jobs() -> dict:
    jobs = runpod_worker_service.list_jobs()
    return {"jobs": jobs, "count": len(jobs)}


@router.post("/worker-registry/runpod/jobs")
def submit_runpod_job(_: RunPodJobSubmitRequest) -> dict:
    raise HTTPException(
        status_code=400,
        detail="Direct RunPod submission is disabled. Use an approved durable workflow run_runpod_job step.",
    )


@router.get("/worker-registry/runpod/jobs/{job_id}")
def get_runpod_job(job_id: str) -> dict:
    job = runpod_worker_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/worker-registry/runpod/jobs/{job_id}/poll")
def poll_runpod_job(job_id: str) -> dict:
    try:
        return runpod_worker_service.poll_job(job_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Job not found") from error
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/worker-registry/runpod/jobs/{job_id}/output")
def get_runpod_job_output(job_id: str) -> dict:
    try:
        return runpod_worker_service.get_job_output(job_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Job not found") from error
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
