"""features routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from app.api.routes import (
    feature_registry_service,
)

router = APIRouter()


# ----------------------------------------------------------------------
# v65.0 Feature Registry + Capability Map 3.0 — make all 60+ versions discoverable.
# ----------------------------------------------------------------------
@router.get("/features")
def list_features(
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
) -> dict:
    return feature_registry_service.list_features(query=q, status=status, category=category)


@router.get("/features/route-map")
def features_route_map() -> dict:
    return feature_registry_service.route_map()


@router.get("/features/summary")
def features_summary() -> dict:
    return feature_registry_service.summary()


@router.post("/features/{key}/try")
def try_feature(key: str) -> dict:
    try:
        return feature_registry_service.try_feature(key)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


# NOTE: /demo/* routes were extracted into app/api/demo_routes.py (services still live here).
