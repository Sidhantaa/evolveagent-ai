"""agent-quality routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    agent_quality_service,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v72.0 Agent Quality Optimizer — trends, weak agents, regressions (read-only).
# ----------------------------------------------------------------------
@router.get("/agent-quality/dashboard")
def agent_quality_dashboard() -> dict:
    return agent_quality_service.dashboard()


@router.get("/agent-quality/summary")
def agent_quality_summary() -> dict:
    return agent_quality_service.summary()


@router.get("/agent-quality/best-by-task")
def agent_quality_best_by_task() -> dict:
    return {"best_by_task": agent_quality_service.best_by_task()}
