"""playbooks routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.api.routes import (
    playbook_library_service,
)
from app.models.request_models import (
    PlaybookCreateRequest,
)

router = APIRouter()


# NOTE: /eval-harness/* routes were extracted into app/api/eval_harness_routes.py (services still live here).


# ----------------------------------------------------------------------
# v53.0 Playbook Library — reusable multi-step playbooks (planning-first).
# ----------------------------------------------------------------------
@router.get("/playbooks/summary")
def get_playbooks_summary() -> dict:
    return playbook_library_service.summary()


@router.get("/playbooks")
def list_playbooks() -> dict:
    playbooks = playbook_library_service.list_playbooks()
    return {"playbooks": playbooks, "count": len(playbooks)}


@router.post("/playbooks")
def create_playbook(request: PlaybookCreateRequest) -> dict:
    return playbook_library_service.create_playbook(request.model_dump())


@router.post("/playbooks/{playbook_id}/run")
def run_playbook(playbook_id: str) -> dict:
    try:
        return playbook_library_service.run_playbook(playbook_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Playbook not found") from error


@router.get("/playbooks/runs")
def list_playbook_runs(playbook_id: str | None = Query(default=None)) -> dict:
    runs = playbook_library_service.list_runs(playbook_id)
    return {"runs": runs, "count": len(runs)}


# NOTE: /operating-layer-2/* routes were extracted into app/api/operating_layer_2_routes.py (services still live here).
