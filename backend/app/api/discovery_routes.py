"""Discovery & intelligence routes, split out of the routes.py monolith.

A first, safe slice of the routes.py split: this module owns a cohesive group of
newer read-mostly features (Design Agent, Git reader, Repo Finder, Adaptive
Learning, Today). The service singletons still live in ``routes.py``; we import
them here (one-directional — this module imports routes, never the reverse — so
there is no circular import). ``main.py`` includes this router alongside the main
one under the same ``/api`` prefix.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.routes import (
    adaptive_learning_service,
    design_agent_service,
    git_reader_service,
    home_dashboard_service,
    repo_finder_service,
)
from app.models.request_models import (
    AdaptiveIngestRequest,
    DesignAnalyzeRequest,
    RepoSearchRequest,
)

router = APIRouter()


# ----------------------------------------------------------------------
# Design Agent — in-app multimodal UI/UX analysis (mock-safe; live opt-in).
# ----------------------------------------------------------------------
@router.get("/design-agent/status")
def design_agent_status() -> dict:
    return design_agent_service.status()


@router.post("/design-agent/analyze")
def design_agent_analyze(request: DesignAnalyzeRequest) -> dict:
    try:
        return design_agent_service.analyze(request.image, request.analyses, request.context, request.allow_live)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/design-agent/history")
def design_agent_history(limit: int = 20) -> dict:
    return design_agent_service.history(limit)


@router.get("/design-agent/summary")
def design_agent_summary() -> dict:
    return design_agent_service.summary()


# ----------------------------------------------------------------------
# Git Intelligence — real read-only reads (log / branches / commit stat).
# ----------------------------------------------------------------------
@router.get("/git-intel/read-status")
def git_reader_status() -> dict:
    return git_reader_service.status()


@router.get("/git-intel/log")
def git_reader_log(path: str, limit: int = 20) -> dict:
    try:
        return git_reader_service.log(path, limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/git-intel/branches")
def git_reader_branches(path: str) -> dict:
    try:
        return git_reader_service.branches(path)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/git-intel/commit-stat")
def git_reader_commit_stat(path: str, ref: str = "HEAD") -> dict:
    try:
        return git_reader_service.commit_stat(path, ref)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


# ----------------------------------------------------------------------
# Repo Finder — find relevant GitHub repositories for a query (read-only).
# ----------------------------------------------------------------------
@router.get("/repo-finder/status")
def repo_finder_status() -> dict:
    return repo_finder_service.status()


@router.post("/repo-finder/search")
def repo_finder_search(request: RepoSearchRequest) -> dict:
    try:
        return repo_finder_service.search(request.query, request.limit, request.sort)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/repo-finder/history")
def repo_finder_history(limit: int = 20) -> dict:
    return repo_finder_service.history(limit)


@router.get("/repo-finder/summary")
def repo_finder_summary() -> dict:
    return repo_finder_service.summary()


# ----------------------------------------------------------------------
# Adaptive Learning — safe self-improving retrieval memory (NOT training).
# ----------------------------------------------------------------------
@router.get("/adaptive-learning/status")
def adaptive_learning_status() -> dict:
    return adaptive_learning_service.status()


@router.post("/adaptive-learning/learn")
def adaptive_learning_learn() -> dict:
    return adaptive_learning_service.learn()


@router.get("/adaptive-learning/recommend")
def adaptive_learning_recommend(query: str, limit: int = 5) -> dict:
    return adaptive_learning_service.recommend(query, limit)


@router.get("/adaptive-learning/items")
def adaptive_learning_items(kind: str | None = None, limit: int = 50) -> dict:
    return adaptive_learning_service.items(kind, limit)


@router.post("/adaptive-learning/items")
def adaptive_learning_ingest(request: AdaptiveIngestRequest) -> dict:
    try:
        return adaptive_learning_service.ingest(request.text, request.kind, request.source)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.delete("/adaptive-learning/items/{item_id}")
def adaptive_learning_forget(item_id: str) -> dict:
    try:
        return adaptive_learning_service.forget(item_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/adaptive-learning/summary")
def adaptive_learning_summary() -> dict:
    return adaptive_learning_service.summary()


# ----------------------------------------------------------------------
# Today — a read-only home dashboard aggregating activity across the app.
# ----------------------------------------------------------------------
@router.get("/today/summary")
def today_summary() -> dict:
    return home_dashboard_service.today()
