"""innovation-lab routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    innovation_lab_service,
)
from app.models.request_models import (
    InnovationCompetitorRequest,
    InnovationExperimentRequest,
    InnovationIdeaRequest,
    InnovationPrototypeRequest,
    InnovationReportRequest,
    InnovationResearchRequest,
    InnovationTrendRequest,
)

router = APIRouter()


# NOTE: /executive-board/* routes were extracted into app/api/executive_board_routes.py (services still live here).


# ----------------------------------------------------------------------
# v36.0 Autonomous Research + Innovation Lab (local/manual research only)
# ----------------------------------------------------------------------
@router.get("/innovation-lab/dashboard")
def get_innovation_lab_dashboard() -> dict:
    return innovation_lab_service.dashboard()


@router.get("/innovation-lab/research")
def list_innovation_research() -> dict:
    items = innovation_lab_service.list_research()
    return {"research": items, "count": len(items)}


@router.post("/innovation-lab/research")
def create_innovation_research(request: InnovationResearchRequest) -> dict:
    return innovation_lab_service.create_research(request.model_dump())


@router.get("/innovation-lab/competitors")
def list_innovation_competitors() -> dict:
    items = innovation_lab_service.list_competitors()
    return {"competitors": items, "count": len(items)}


@router.post("/innovation-lab/competitors")
def create_innovation_competitor(request: InnovationCompetitorRequest) -> dict:
    return innovation_lab_service.create_competitor(request.model_dump())


@router.get("/innovation-lab/trends")
def list_innovation_trends() -> dict:
    items = innovation_lab_service.list_trends()
    return {"trends": items, "count": len(items)}


@router.post("/innovation-lab/trends")
def create_innovation_trend(request: InnovationTrendRequest) -> dict:
    return innovation_lab_service.create_trend(request.model_dump())


@router.get("/innovation-lab/ideas")
def list_innovation_ideas() -> dict:
    items = innovation_lab_service.list_ideas()
    return {"ideas": items, "count": len(items)}


@router.post("/innovation-lab/ideas")
def create_innovation_idea(request: InnovationIdeaRequest) -> dict:
    return innovation_lab_service.create_idea(request.model_dump())


@router.get("/innovation-lab/experiments")
def list_innovation_experiments() -> dict:
    items = innovation_lab_service.list_experiments()
    return {"experiments": items, "count": len(items)}


@router.post("/innovation-lab/experiments")
def create_innovation_experiment(request: InnovationExperimentRequest) -> dict:
    return innovation_lab_service.create_experiment(request.model_dump())


@router.get("/innovation-lab/prototypes")
def list_innovation_prototypes() -> dict:
    items = innovation_lab_service.list_prototypes()
    return {"prototypes": items, "count": len(items)}


@router.post("/innovation-lab/prototypes")
def create_innovation_prototype(request: InnovationPrototypeRequest) -> dict:
    return innovation_lab_service.create_prototype(request.model_dump())


@router.get("/innovation-lab/reports")
def list_innovation_reports() -> dict:
    items = innovation_lab_service.list_reports()
    return {"reports": items, "count": len(items)}


@router.post("/innovation-lab/reports")
def create_innovation_report(request: InnovationReportRequest | None = None) -> dict:
    return innovation_lab_service.create_report(request.model_dump() if request else {})
