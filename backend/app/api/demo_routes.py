"""demo routes, split out of routes.py (services + models imported from there)."""

from __future__ import annotations

from fastapi import APIRouter
from app.api.routes import (
    demo_service,
)

router = APIRouter()


# ----------------------------------------------------------------------
# Demo Mode / Portfolio Mode — demo-safe, impressive, resettable.
# ----------------------------------------------------------------------
@router.get("/demo/script")
def demo_script() -> dict:
    return demo_service.script()


@router.get("/demo/walkthrough")
def demo_walkthrough() -> dict:
    return demo_service.walkthrough()


@router.get("/demo/feature-sequence")
def demo_feature_sequence() -> dict:
    return demo_service.feature_sequence()


@router.get("/demo/resume-bullets")
def demo_resume_bullets() -> dict:
    return demo_service.resume_bullets()


@router.get("/demo/case-study")
def demo_case_study() -> dict:
    return demo_service.case_study()


@router.get("/demo/summary")
def demo_summary() -> dict:
    return demo_service.summary()


@router.post("/demo/seed")
def demo_seed() -> dict:
    return demo_service.seed()


@router.post("/demo/reset")
def demo_reset() -> dict:
    return demo_service.reset()
