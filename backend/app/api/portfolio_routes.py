"""portfolio routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, Query
from app.api.routes import (
    portfolio_service,
    PlainTextResponse,
)
from app.models.request_models import (
    PortfolioReportRequest,
)

router = APIRouter()


# NOTE: /project-manager/* routes were extracted into app/api/project_manager_routes.py (services still live here).


@router.get("/portfolio/dashboard")
def get_portfolio_dashboard() -> dict:
    return portfolio_service.dashboard()


@router.get("/portfolio/analytics")
def get_portfolio_analytics() -> dict:
    return portfolio_service.analytics()


@router.get("/portfolio/health")
def get_portfolio_health() -> dict:
    return portfolio_service.health()


@router.post("/portfolio/reports")
def generate_portfolio_report(request: PortfolioReportRequest | None = None) -> dict:
    return portfolio_service.generate_executive_summary()


@router.get("/portfolio/reports")
def get_portfolio_reports() -> list[dict]:
    return portfolio_service.list_reports()


@router.get("/portfolio/export")
def export_portfolio(format: str = Query(default="json", pattern="^(json|markdown)$")) -> PlainTextResponse:
    content = portfolio_service.export(format=format)
    media_type = "application/json" if format == "json" else "text/markdown"
    extension = "json" if format == "json" else "md"
    return PlainTextResponse(
        content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="evolveagent-portfolio.{extension}"'},
    )
