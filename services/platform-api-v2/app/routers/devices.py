"""Device API v2 routes."""

from copy import deepcopy

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from ..models import (
    AgentStatus,
    AgentStatusResponse,
    DeviceCreate,
    DeviceListResponse,
    DeviceResponse,
    DeviceUpdate,
)
from ..security import Principal, get_principal
from ..store import DEVICES, LOCK, paginate, record_audit, utcnow


router = APIRouter(prefix="/v2/devices", tags=["Device API v2"])


def _device_or_404(device_id: str) -> dict:
    with LOCK:
        device = DEVICES.get(device_id)
        if device is None:
            raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
        return deepcopy(device)


@router.get("", response_model=DeviceListResponse, summary="List devices")
def list_devices(
    status_filter: AgentStatus | None = Query(default=None, alias="status"),
    fleet: str | None = None,
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    _: Principal = Depends(get_principal),
) -> dict:
    with LOCK:
        devices = sorted(DEVICES.values(), key=lambda item: item["id"])
        if status_filter:
            devices = [item for item in devices if item["agent_status"] == status_filter.value]
        if fleet:
            devices = [item for item in devices if item.get("fleet") == fleet]
        page, next_cursor = paginate(devices, cursor, limit)
    return {"data": page, "meta": {"limit": limit, "next_cursor": next_cursor}}


@router.post(
    "",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a device",
)
def register_device(
    payload: DeviceCreate,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    with LOCK:
        if payload.id in DEVICES:
            raise HTTPException(status_code=409, detail=f"Device already exists: {payload.id}")
        device = {
            **payload.model_dump(),
            "agent_status": "unknown",
            "last_seen_at": None,
            "remote_access": {
                "enabled": True,
                "broker_url": "wss://broker.smarttouch.local:8443",
                "allowed_protocols": ["diagnostics"],
            },
        }
        DEVICES[payload.id] = device
    record_audit(
        "device.registered",
        principal.subject,
        "device",
        payload.id,
        request.state.request_id,
        {"fleet": payload.fleet},
    )
    return {"data": deepcopy(device)}


@router.get("/{device_id}", response_model=DeviceResponse, summary="Get a device")
def get_device(device_id: str, _: Principal = Depends(get_principal)) -> dict:
    return {"data": _device_or_404(device_id)}


@router.patch("/{device_id}", response_model=DeviceResponse, summary="Update device metadata")
def update_device(
    device_id: str,
    payload: DeviceUpdate,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    with LOCK:
        if device_id not in DEVICES:
            raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
        changes = payload.model_dump(exclude_unset=True)
        DEVICES[device_id].update(changes)
        device = deepcopy(DEVICES[device_id])
    record_audit(
        "device.updated",
        principal.subject,
        "device",
        device_id,
        request.state.request_id,
        {"changed_fields": sorted(changes)},
    )
    return {"data": device}


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deregister a device")
def deregister_device(
    device_id: str,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> Response:
    with LOCK:
        if device_id not in DEVICES:
            raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
        del DEVICES[device_id]
    record_audit(
        "device.deregistered",
        principal.subject,
        "device",
        device_id,
        request.state.request_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{device_id}/agent-status",
    response_model=AgentStatusResponse,
    summary="Get device agent status",
)
def get_agent_status(device_id: str, _: Principal = Depends(get_principal)) -> dict:
    device = _device_or_404(device_id)
    online = device["agent_status"] == "online"
    return {
        "data": {
            "device_id": device_id,
            "agent_status": device["agent_status"],
            "last_seen_at": device.get("last_seen_at"),
            "broker_url": device["remote_access"]["broker_url"],
            "latency_ms": 12 if online else None,
            "checked_at": utcnow(),
        }
    }
