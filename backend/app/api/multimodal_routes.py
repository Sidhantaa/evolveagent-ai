"""multimodal routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    multimodal_agent_service,
)
from app.models.request_models import (
    MultimodalAnalyzeRequest,
    MultimodalItemCreateRequest,
)

router = APIRouter()


# NOTE: /chief-of-staff/* routes were extracted into app/api/chief_of_staff_routes.py (services still live here).


# ----------------------------------------------------------------------
# v21.0 Multi-Modal Real-World Agent
# ----------------------------------------------------------------------
@router.get("/multimodal/dashboard")
def get_multimodal_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    return multimodal_agent_service.dashboard(workspace_id)


@router.get("/multimodal/items")
def list_multimodal_items(workspace_id: str | None = Query(default=None)) -> dict:
    items = multimodal_agent_service.list_items(workspace_id)
    return {"items": items, "count": len(items)}


@router.post("/multimodal/items")
def create_multimodal_item(request: MultimodalItemCreateRequest) -> dict:
    return multimodal_agent_service.create_item(request.model_dump())


@router.get("/multimodal/analyses")
def list_multimodal_analyses(workspace_id: str | None = Query(default=None)) -> dict:
    analyses = multimodal_agent_service.list_analyses(workspace_id)
    return {"analyses": analyses, "count": len(analyses)}


@router.post("/multimodal/items/{item_id}/analyze")
def analyze_multimodal_item(item_id: str, request: MultimodalAnalyzeRequest | None = None) -> dict:
    analysis_type = request.analysis_type if request else None
    image = request.image if request else None
    allow_live = request.allow_live if request else False
    try:
        return multimodal_agent_service.analyze_item(item_id, analysis_type, image, allow_live)
    except ValueError as error:
        if str(error) == "Item not found":
            raise HTTPException(status_code=404, detail="Item not found") from error
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/multimodal/status")
def get_multimodal_status() -> dict:
    return multimodal_agent_service.status()


@router.get("/multimodal/summary")
def get_multimodal_summary() -> dict:
    return multimodal_agent_service.summary()


# NOTE: /industry-modes/* routes were extracted into app/api/industry_modes_routes.py (services still live here).
