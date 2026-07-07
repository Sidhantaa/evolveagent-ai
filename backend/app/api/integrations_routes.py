"""integrations routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, Query, status
from app.api.routes import (
    workspace_service,
    list_notifications,
    notion_exports,
    slack_notifications,
)
from app.models.request_models import (
    NotionExportRequest,
    SlackTestNotificationRequest,
)

router = APIRouter()


@router.get("/integrations/slack/status")
def get_slack_integration_status() -> dict:
    return slack_notifications.status()


@router.get("/integrations/slack/notifications")
def list_slack_notifications(limit: int = Query(default=50, ge=1, le=200)) -> list[dict]:
    return slack_notifications.list_notifications(limit=limit)


@router.post("/integrations/slack/test")
def send_slack_test_notification(request: SlackTestNotificationRequest) -> dict:
    resolved_workspace_id = workspace_service.resolve_workspace_id(request.workspace_id) if request.workspace_id else None
    return slack_notifications.send_test_message(
        text=request.text,
        channel=request.channel,
        workspace_id=resolved_workspace_id,
    )


@router.get("/integrations/notion/status")
def get_notion_integration_status() -> dict:
    return notion_exports.status()


@router.get("/integrations/notion/exports")
def list_notion_exports(limit: int = Query(default=50, ge=1, le=200)) -> list[dict]:
    return notion_exports.list_exports(limit=limit)


@router.post("/integrations/notion/export")
def export_to_notion(request: NotionExportRequest) -> dict:
    resolved_workspace_id = workspace_service.resolve_workspace_id(request.workspace_id) if request.workspace_id else None
    return notion_exports.export_page(
        title=request.title,
        content=request.content,
        workspace_id=resolved_workspace_id,
    )


# NOTE: /autopilot/* routes were extracted into app/api/autopilot_routes.py (services still live here).
