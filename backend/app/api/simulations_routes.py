"""simulations routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    debate_simulation_service,
)
from app.models.request_models import (
    SimulationCreateRequest,
)

router = APIRouter()


# NOTE: /debate/* routes were extracted into app/api/debate_routes.py (services still live here).


@router.get("/simulations")
def list_simulation_runs(workspace_id: str | None = Query(default=None)) -> list[dict]:
    return debate_simulation_service.list_simulations(workspace_id)


@router.get("/simulations/{simulation_id}")
def get_simulation_run(simulation_id: str) -> dict:
    simulation = debate_simulation_service.get_simulation(simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    return simulation


@router.post("/simulations")
def create_simulation_run(request: SimulationCreateRequest) -> dict:
    return debate_simulation_service.create_simulation(
        prompt=request.prompt,
        scenario=request.scenario,
        workspace_id=request.workspace_id,
    )


# NOTE: /research/* routes were extracted into app/api/research_routes.py (services still live here).
