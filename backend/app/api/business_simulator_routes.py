"""business-simulator routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    business_simulator_service,
)
from app.models.request_models import (
    SimulationScenarioCreateRequest,
    SimulationScenarioUpdateRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v20.0 Autonomous Business Simulator
# ----------------------------------------------------------------------
@router.get("/business-simulator/dashboard")
def get_business_simulator_dashboard(workspace_id: str | None = Query(default=None)) -> dict:
    return business_simulator_service.dashboard(workspace_id)


@router.get("/business-simulator/scenarios")
def list_business_simulator_scenarios(workspace_id: str | None = Query(default=None)) -> dict:
    scenarios = business_simulator_service.list_scenarios(workspace_id)
    return {"scenarios": scenarios, "count": len(scenarios)}


@router.post("/business-simulator/scenarios")
def create_business_simulator_scenario(request: SimulationScenarioCreateRequest) -> dict:
    return business_simulator_service.create_scenario(request.model_dump())


@router.get("/business-simulator/results")
def list_business_simulator_results(workspace_id: str | None = Query(default=None)) -> dict:
    results = business_simulator_service.list_results(workspace_id)
    return {"results": results, "count": len(results)}


@router.get("/business-simulator/results/{result_id}")
def get_business_simulator_result(result_id: str) -> dict:
    result = business_simulator_service.get_result(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.get("/business-simulator/scenarios/{scenario_id}")
def get_business_simulator_scenario(scenario_id: str) -> dict:
    scenario = business_simulator_service.get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.patch("/business-simulator/scenarios/{scenario_id}")
def update_business_simulator_scenario(scenario_id: str, request: SimulationScenarioUpdateRequest) -> dict:
    try:
        return business_simulator_service.update_scenario(scenario_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Scenario not found") from error


@router.post("/business-simulator/scenarios/{scenario_id}/run")
def run_business_simulator_scenario(scenario_id: str) -> dict:
    try:
        return business_simulator_service.run_simulation(scenario_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Scenario not found") from error
