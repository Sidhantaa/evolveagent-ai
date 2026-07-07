"""Read-only GitHub connector routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.api.routes import github_connector_service

router = APIRouter()


@router.get("/github/status")
def github_status() -> dict:
    return github_connector_service.status()


@router.get("/github/repos")
def github_repos(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    return github_connector_service.list_repos(limit)


@router.get("/github/issues")
def github_issues(repo: str, state: str = "open", limit: int = Query(default=20, ge=1, le=100)) -> dict:
    try:
        return github_connector_service.list_issues(repo, state, limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/github/pulls")
def github_pulls(repo: str, state: str = "open", limit: int = Query(default=20, ge=1, le=100)) -> dict:
    try:
        return github_connector_service.list_pull_requests(repo, state, limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/github/summary")
def github_summary() -> dict:
    return github_connector_service.summary()
