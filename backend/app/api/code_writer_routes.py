"""v150 Autonomous Software Team — real, write-capable code agent status.

The one write action (write_and_commit) is never called directly through a
route — it's only reachable via an approved DurableWorkflowService step
(action_type="write_code_change"). This module only exposes read-only status.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import code_writer_service

router = APIRouter()


@router.get("/code-writer/status")
def code_writer_status() -> dict:
    return code_writer_service.status()


@router.get("/code-writer/summary")
def code_writer_summary() -> dict:
    return {**code_writer_service.status(), **code_writer_service.analytics_summary()}
