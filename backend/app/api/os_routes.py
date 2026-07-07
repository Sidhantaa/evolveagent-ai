"""os routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    os_scheduler_service,
    platform_installer_service,
    plugin_sdk_service,
    sla_monitoring_service,
)
from app.models.request_models import (
    PluginManifestValidateRequest,
)

router = APIRouter()


# NOTE: /portfolio/* routes were extracted into app/api/portfolio_routes.py (services still live here).


@router.get("/os/installer")
def get_os_installer() -> dict:
    return platform_installer_service.installer()


@router.get("/os/plugin-sdk")
def get_os_plugin_sdk() -> dict:
    return plugin_sdk_service.sdk()


@router.post("/os/plugin-sdk/validate")
def validate_os_plugin_manifest(request: PluginManifestValidateRequest) -> dict:
    return plugin_sdk_service.validate(request.manifest)


@router.get("/os/sla")
def get_os_sla() -> dict:
    return sla_monitoring_service.sla()


@router.get("/os/scheduler")
def get_os_scheduler() -> dict:
    return os_scheduler_service.overview()


@router.get("/os/summary")
def get_os_summary() -> dict:
    installer = platform_installer_service.installer()
    sla = sla_monitoring_service.sla()
    scheduler = os_scheduler_service.overview()
    return {
        "platform": "EvolveAgent OS",
        "version": "v15.0",
        "positioning": (
            "EvolveAgent OS is a local-first, workspace-aware multi-agent AI platform with governed "
            "automation, plugins, analytics, evaluation, and portfolio management."
        ),
        "installer_readiness": installer["readiness"],
        "plugin_sdk": plugin_sdk_service.summary(),
        "sla_rating": sla["sla_rating"],
        "uptime_proxy_score": sla["uptime_proxy_score"],
        "scheduler_health": scheduler["scheduler_health"],
        "safety_notes": installer["safety_notes"],
    }


# NOTE: /team-manager/* routes were extracted into app/api/team_manager_routes.py (services still live here).
