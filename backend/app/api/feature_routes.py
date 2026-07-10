"""Voice Console, Durable Workflows, and Marketplace Hub routes.

Second slice of the routes.py split (after discovery_routes.py). Owns three
cohesive feature groups (Phases 4/6/7). The service singletons still live in
routes.py; this module imports them one-directionally (it imports routes, never
the reverse — no circular import). main.py includes this router under /api.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.routes import (
    durable_workflow_service,
    marketplace_hub_service,
    voice_console_service,
)
from app.models.request_models import (
    DurableWorkflowDefRequest,
    DurableWorkflowStartRequest,
    MarketplacePublishRequest,
    MarketplaceRatingRequest,
    VoiceActivityRequest,
    VoiceSettingsRequest,
    WorkflowApprovalRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# Phase 4 Voice Console — browser voice preferences + privacy-safe audit.
# ----------------------------------------------------------------------
@router.get("/voice-console/status")
def voice_console_status() -> dict:
    return voice_console_service.status()


@router.get("/voice-console/settings")
def voice_console_get_settings(workspace_id: str = "global") -> dict:
    return voice_console_service.get_settings(workspace_id)


@router.put("/voice-console/settings")
def voice_console_update_settings(request: VoiceSettingsRequest) -> dict:
    patch = request.model_dump(exclude_none=True)
    workspace_id = patch.pop("workspace_id", "global")
    return voice_console_service.update_settings(patch, workspace_id)


@router.post("/voice-console/activity")
def voice_console_activity(request: VoiceActivityRequest) -> dict:
    try:
        return voice_console_service.log_activity(
            request.kind, request.workspace_id, request.text, request.meta
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/voice-console/events")
def voice_console_events(workspace_id: str = "global", limit: int = 50) -> dict:
    return voice_console_service.events(workspace_id, limit)


@router.delete("/voice-console/events")
def voice_console_clear_events(workspace_id: str = "global") -> dict:
    return voice_console_service.clear_events(workspace_id)


@router.get("/voice-console/summary")
def voice_console_summary() -> dict:
    return voice_console_service.summary()


# ----------------------------------------------------------------------
# Phase 6 Durable Workflows — resumable, approval-gated, mock-safe runs.
# ----------------------------------------------------------------------
@router.get("/durable-workflows/templates")
def durable_workflow_templates() -> dict:
    return durable_workflow_service.templates()


@router.get("/durable-workflows/definitions")
def durable_workflow_definitions() -> dict:
    return durable_workflow_service.list_definitions()


@router.post("/durable-workflows/definitions")
def durable_workflow_create_def(request: DurableWorkflowDefRequest) -> dict:
    try:
        return durable_workflow_service.create_definition(request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/durable-workflows/runs")
def durable_workflow_list_runs() -> dict:
    return durable_workflow_service.list_runs()


@router.post("/durable-workflows/runs")
def durable_workflow_start(request: DurableWorkflowStartRequest) -> dict:
    try:
        return durable_workflow_service.start_run(request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/durable-workflows/runs/{run_id}")
def durable_workflow_get_run(run_id: str) -> dict:
    try:
        return durable_workflow_service.get_run(run_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/durable-workflows/runs/{run_id}/advance")
def durable_workflow_advance(run_id: str) -> dict:
    try:
        return durable_workflow_service.advance_run(run_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/durable-workflows/runs/{run_id}/approve")
def durable_workflow_approve(run_id: str, request: WorkflowApprovalRequest) -> dict:
    try:
        return durable_workflow_service.approve_step(run_id, request.approved, request.note, request.approver)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/durable-workflows/runs/{run_id}/pause")
def durable_workflow_pause(run_id: str) -> dict:
    try:
        return durable_workflow_service.pause_run(run_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/durable-workflows/runs/{run_id}/resume")
def durable_workflow_resume(run_id: str) -> dict:
    try:
        return durable_workflow_service.resume_run(run_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/durable-workflows/runs/{run_id}/cancel")
def durable_workflow_cancel(run_id: str) -> dict:
    try:
        return durable_workflow_service.cancel_run(run_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/durable-workflows/effects")
def durable_workflow_effects(run_id: str | None = None, limit: int = 50) -> dict:
    return durable_workflow_service.effects(run_id, limit)


@router.get("/durable-workflows/summary")
def durable_workflow_summary() -> dict:
    return durable_workflow_service.summary()


# ----------------------------------------------------------------------
# Phase 7 Marketplace Hub — local, sanitized agent + workflow bundles.
# ----------------------------------------------------------------------
@router.get("/marketplace-hub/listings")
def marketplace_hub_listings(kind: str | None = None, sort: str | None = None) -> dict:
    return marketplace_hub_service.list_listings(kind, sort)


@router.get("/marketplace-hub/listings/{listing_id}")
def marketplace_hub_get_listing(listing_id: str) -> dict:
    try:
        return marketplace_hub_service.get_listing(listing_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/marketplace-hub/listings")
def marketplace_hub_publish(request: MarketplacePublishRequest) -> dict:
    try:
        return marketplace_hub_service.publish(request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/marketplace-hub/listings/{listing_id}/install")
def marketplace_hub_install(listing_id: str) -> dict:
    try:
        return marketplace_hub_service.install(listing_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/marketplace-hub/listings/{listing_id}")
def marketplace_hub_unpublish(listing_id: str) -> dict:
    try:
        return marketplace_hub_service.unpublish(listing_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/marketplace-hub/listings/{listing_id}/rate")
def marketplace_hub_rate(listing_id: str, request: MarketplaceRatingRequest) -> dict:
    try:
        return marketplace_hub_service.rate_listing(listing_id, request.rating, request.review)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/marketplace-hub/listings/{listing_id}/ratings")
def marketplace_hub_list_ratings(listing_id: str) -> dict:
    return marketplace_hub_service.list_ratings(listing_id)


@router.get("/marketplace-hub/installs")
def marketplace_hub_installs() -> dict:
    return marketplace_hub_service.installs()


@router.get("/marketplace-hub/summary")
def marketplace_hub_summary() -> dict:
    return marketplace_hub_service.summary()
