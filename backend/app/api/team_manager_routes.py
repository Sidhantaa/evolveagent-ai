"""team-manager routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    team_manager_service,
)
from app.models.request_models import (
    TeamAssignmentCreateRequest,
    TeamAssignmentUpdateRequest,
    TeamMemberCreateRequest,
    TeamMemberUpdateRequest,
    TeamSprintCreateRequest,
    TeamSprintReviewRequest,
)

router = APIRouter()


# NOTE: /self-healing/* routes were extracted into app/api/self_healing_routes.py (services still live here).
# ----------------------------------------------------------------------
@router.get("/team-manager/dashboard")
def get_team_manager_dashboard() -> dict:
    return team_manager_service.dashboard()


@router.get("/team-manager/analytics")
def get_team_manager_analytics() -> dict:
    return team_manager_service.analytics()


@router.get("/team-manager/members")
def list_team_members() -> dict:
    members = team_manager_service.list_members()
    return {"members": members, "count": len(members)}


@router.post("/team-manager/members")
def create_team_member(request: TeamMemberCreateRequest) -> dict:
    return team_manager_service.create_member(request.model_dump())


@router.patch("/team-manager/members/{member_id}")
def update_team_member(member_id: str, request: TeamMemberUpdateRequest) -> dict:
    try:
        return team_manager_service.update_member(member_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Member not found") from error


@router.get("/team-manager/assignments")
def list_team_assignments() -> dict:
    assignments = team_manager_service.list_assignments()
    return {"assignments": assignments, "count": len(assignments)}


@router.post("/team-manager/assignments")
def create_team_assignment(request: TeamAssignmentCreateRequest) -> dict:
    return team_manager_service.create_assignment(request.model_dump())


@router.patch("/team-manager/assignments/{assignment_id}")
def update_team_assignment(assignment_id: str, request: TeamAssignmentUpdateRequest) -> dict:
    try:
        return team_manager_service.update_assignment(assignment_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Assignment not found") from error


@router.get("/team-manager/standups")
def list_team_standups() -> dict:
    standups = team_manager_service.list_standups()
    return {"standups": standups, "count": len(standups)}


@router.post("/team-manager/standups")
def create_team_standup() -> dict:
    return team_manager_service.create_standup()


@router.get("/team-manager/sprints")
def list_team_sprints() -> dict:
    sprints = team_manager_service.list_sprints()
    return {"sprints": sprints, "count": len(sprints)}


@router.post("/team-manager/sprints")
def create_team_sprint(request: TeamSprintCreateRequest) -> dict:
    return team_manager_service.create_sprint(request.model_dump())


@router.post("/team-manager/sprints/{sprint_id}/review")
def create_team_sprint_review(sprint_id: str, request: TeamSprintReviewRequest | None = None) -> dict:
    payload = request.model_dump() if request else {}
    try:
        return team_manager_service.create_review(sprint_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Sprint not found") from error


# NOTE: /business-operator/* routes were extracted into app/api/business_operator_routes.py (services still live here).
