"""Immutable Audit Log API v2 routes."""

from copy import deepcopy
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from ..models import AuditEventListResponse, AuditEventResponse
from ..security import Principal, get_principal
from ..store import AUDIT_EVENTS, LOCK, paginate


router = APIRouter(prefix="/v2/audit/events", tags=["Audit Log API v2"])


@router.get("", response_model=AuditEventListResponse, summary="List audit events")
def list_audit_events(
    event: str | None = None,
    actor: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    outcome: str | None = Query(default=None, pattern="^(success|failure)$"),
    since: datetime | None = None,
    until: datetime | None = None,
    cursor: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    _: Principal = Depends(get_principal),
) -> dict:
    with LOCK:
        events = list(AUDIT_EVENTS)
        if event:
            events = [item for item in events if item["event"] == event]
        if actor:
            events = [item for item in events if item["actor"] == actor]
        if resource_type:
            events = [item for item in events if item["resource_type"] == resource_type]
        if resource_id:
            events = [item for item in events if item["resource_id"] == resource_id]
        if outcome:
            events = [item for item in events if item["outcome"] == outcome]
        if since:
            events = [item for item in events if datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")) >= since]
        if until:
            events = [item for item in events if datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")) < until]
        page, next_cursor = paginate(events, cursor, limit)
    return {"data": page, "meta": {"limit": limit, "next_cursor": next_cursor}}


@router.get("/{entry_id}", response_model=AuditEventResponse, summary="Get an audit event")
def get_audit_event(entry_id: str, _: Principal = Depends(get_principal)) -> dict:
    with LOCK:
        entry = next((item for item in AUDIT_EVENTS if item["id"] == entry_id), None)
        if entry is None:
            raise HTTPException(status_code=404, detail=f"Audit event not found: {entry_id}")
        return {"data": deepcopy(entry)}
