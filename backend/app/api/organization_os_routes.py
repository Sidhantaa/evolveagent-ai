"""organization-os routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.api.routes import (
    organization_os_service,
)
from app.models.request_models import (
    OrganizationCreateRequest,
    OrganizationMemberCreateRequest,
    OrganizationMemberUpdateRequest,
    OrganizationRoleCreateRequest,
    OrganizationWorkspaceLinkRequest,
)

router = APIRouter()


# NOTE: /simulation-world/* routes were extracted into app/api/simulation_world_routes.py (services still live here).


# ----------------------------------------------------------------------
# v38.0 Multi-User Organization OS (local records only — no production auth)
# ----------------------------------------------------------------------
@router.get("/organization-os/dashboard")
def get_organization_os_dashboard() -> dict:
    return organization_os_service.dashboard()


@router.get("/organization-os/activity")
def get_organization_os_activity() -> dict:
    activity = organization_os_service.activity_log()
    return {"activity": activity, "count": len(activity)}


@router.get("/organization-os/organizations")
def list_organizations() -> dict:
    orgs = organization_os_service.list_organizations()
    return {"organizations": orgs, "count": len(orgs)}


@router.post("/organization-os/organizations")
def create_organization(request: OrganizationCreateRequest) -> dict:
    return organization_os_service.create_organization(request.model_dump())


@router.get("/organization-os/members")
def list_organization_members() -> dict:
    members = organization_os_service.list_members()
    return {"members": members, "count": len(members)}


@router.post("/organization-os/members")
def create_organization_member(request: OrganizationMemberCreateRequest) -> dict:
    return organization_os_service.create_member(request.model_dump())


@router.patch("/organization-os/members/{member_id}")
def update_organization_member(member_id: str, request: OrganizationMemberUpdateRequest) -> dict:
    try:
        return organization_os_service.update_member(member_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Member not found") from error


@router.get("/organization-os/roles")
def list_organization_roles() -> dict:
    roles = organization_os_service.list_roles()
    return {"roles": roles, "count": len(roles)}


@router.post("/organization-os/roles")
def create_organization_role(request: OrganizationRoleCreateRequest) -> dict:
    return organization_os_service.create_role(request.model_dump())


@router.post("/organization-os/workspace-links")
def create_organization_workspace_link(request: OrganizationWorkspaceLinkRequest) -> dict:
    return organization_os_service.create_workspace_link(request.model_dump())


@router.get("/organization-os/organizations/{organization_id}")
def get_organization(organization_id: str) -> dict:
    org = organization_os_service.get_organization(organization_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org
