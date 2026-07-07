"""Event Bus routes (v120) — the event system: a log of occurrences plus
subscriptions that chain one action into another. Imports the shared service
from routes.py."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.routes import event_bus_service
from app.models.request_models import EventEmitRequest, EventSubscriptionCreateRequest, EventSubscriptionUpdateRequest

router = APIRouter()


@router.get("/events")
def list_events(event_type: str | None = None, limit: int = 50) -> dict:
    return event_bus_service.list_events(event_type, limit)


@router.post("/events")
def emit_event(request: EventEmitRequest) -> dict:
    """Manually emit an event (explicit action — e.g. for testing a subscription)."""
    return event_bus_service.emit(request.event_type, request.payload, request.source)


@router.get("/event-subscriptions")
def list_event_subscriptions() -> dict:
    return {"subscriptions": event_bus_service.list_subscriptions()}


@router.post("/event-subscriptions")
def create_event_subscription(request: EventSubscriptionCreateRequest) -> dict:
    try:
        return event_bus_service.create_subscription(request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/event-subscriptions/summary")
def event_subscriptions_summary() -> dict:
    return event_bus_service.summary()


@router.get("/event-subscriptions/{subscription_id}")
def get_event_subscription(subscription_id: str) -> dict:
    sub = event_bus_service.get_subscription(subscription_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.patch("/event-subscriptions/{subscription_id}")
def update_event_subscription(subscription_id: str, request: EventSubscriptionUpdateRequest) -> dict:
    try:
        return event_bus_service.update_subscription(subscription_id, request.model_dump(exclude_unset=True))
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
