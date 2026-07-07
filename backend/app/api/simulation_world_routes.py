"""simulation-world routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    simulation_world_service,
)
from app.models.request_models import (
    SimWorldScenarioCreateRequest,
    SimulationCompareRequest,
    SimulationPersonaCreateRequest,
    SimulationReportRequest,
    SimulationWorldCreateRequest,
)

router = APIRouter()


# NOTE: /innovation-lab/* routes were extracted into app/api/innovation_lab_routes.py (services still live here).


# ----------------------------------------------------------------------
# v37.0 AI Simulation World (deterministic mock sandbox — no real actions)
# ----------------------------------------------------------------------
@router.get("/simulation-world/dashboard")
def get_simulation_world_dashboard() -> dict:
    return simulation_world_service.dashboard()


@router.get("/simulation-world/worlds")
def list_simulation_worlds() -> dict:
    worlds = simulation_world_service.list_worlds()
    return {"worlds": worlds, "count": len(worlds)}


@router.post("/simulation-world/worlds")
def create_simulation_world(request: SimulationWorldCreateRequest) -> dict:
    return simulation_world_service.create_world(request.model_dump())


@router.get("/simulation-world/personas")
def list_simulation_personas() -> dict:
    personas = simulation_world_service.list_personas()
    return {"personas": personas, "count": len(personas)}


@router.post("/simulation-world/personas")
def create_simulation_persona(request: SimulationPersonaCreateRequest) -> dict:
    return simulation_world_service.create_persona(request.model_dump())


@router.get("/simulation-world/scenarios")
def list_simulation_scenarios() -> dict:
    scenarios = simulation_world_service.list_scenarios()
    return {"scenarios": scenarios, "count": len(scenarios)}


@router.post("/simulation-world/scenarios")
def create_simulation_scenario(request: SimWorldScenarioCreateRequest) -> dict:
    return simulation_world_service.create_scenario(request.model_dump())


@router.post("/simulation-world/scenarios/{scenario_id}/run")
def run_simulation_scenario(scenario_id: str) -> dict:
    try:
        return simulation_world_service.run_scenario(scenario_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Scenario not found") from error


@router.post("/simulation-world/compare")
def compare_simulation_scenarios(request: SimulationCompareRequest) -> dict:
    return simulation_world_service.compare(request.scenario_ids)


@router.get("/simulation-world/reports")
def list_simulation_world_reports() -> dict:
    reports = simulation_world_service.list_reports()
    return {"reports": reports, "count": len(reports)}


@router.post("/simulation-world/reports")
def create_simulation_world_report(request: SimulationReportRequest | None = None) -> dict:
    return simulation_world_service.create_report(request.model_dump() if request else {})
