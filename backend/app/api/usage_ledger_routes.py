"""usage-ledger routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, Query
from app.api.routes import (
    usage_ledger_service,
)
from app.models.request_models import (
    UsageBudgetRequest,
    UsageRecordRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v50.0 Cost & Usage Ledger — usage estimates + budgets (no billing).
# ----------------------------------------------------------------------
@router.get("/usage-ledger/summary")
def get_usage_ledger_summary(workspace_id: str | None = Query(default=None)) -> dict:
    return usage_ledger_service.summary(workspace_id)


@router.get("/usage-ledger/entries")
def list_usage_entries(workspace_id: str | None = Query(default=None)) -> dict:
    entries = usage_ledger_service.list_entries(workspace_id)
    return {"entries": entries, "count": len(entries)}


@router.post("/usage-ledger/entries")
def record_usage_entry(request: UsageRecordRequest) -> dict:
    return usage_ledger_service.record_usage(request.model_dump())


@router.get("/usage-ledger/budgets")
def list_usage_budgets() -> dict:
    budgets = usage_ledger_service.list_budgets()
    return {"budgets": budgets, "count": len(budgets)}


@router.post("/usage-ledger/budgets")
def set_usage_budget(request: UsageBudgetRequest) -> dict:
    return usage_ledger_service.set_budget(request.model_dump())
