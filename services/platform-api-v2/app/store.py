"""Thread-safe in-memory data store used by the API v2 reference service."""

from __future__ import annotations

import base64
import json
from copy import deepcopy
from datetime import UTC, datetime
from threading import RLock
from uuid import uuid4


LOCK = RLock()
DEVICES: dict[str, dict] = {}
SERVICES: dict[str, dict] = {}
REVISIONS: dict[str, list[dict]] = {}
CANARIES: dict[str, dict] = {}
AUDIT_EVENTS: list[dict] = []


def utcnow() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def service_key(environment: str, name: str) -> str:
    return f"{environment}:{name}"


def encode_cursor(offset: int) -> str:
    payload = json.dumps({"offset": offset}, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        value = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
        offset = int(value["offset"])
        if offset < 0:
            raise ValueError
        return offset
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("The cursor is invalid or expired.") from exc


def paginate(items: list[dict], cursor: str | None, limit: int) -> tuple[list[dict], str | None]:
    offset = decode_cursor(cursor)
    page = items[offset : offset + limit]
    next_offset = offset + len(page)
    next_cursor = encode_cursor(next_offset) if next_offset < len(items) else None
    return deepcopy(page), next_cursor


def record_audit(
    event: str,
    actor: str,
    resource_type: str,
    resource_id: str,
    request_id: str,
    details: dict | None = None,
) -> dict:
    entry = {
        "id": f"audit-{uuid4().hex[:12]}",
        "event": event,
        "actor": actor,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "outcome": "success",
        "timestamp": utcnow(),
        "request_id": request_id,
        "details": details or {},
    }
    with LOCK:
        AUDIT_EVENTS.insert(0, entry)
    return deepcopy(entry)


def reset_store() -> None:
    with LOCK:
        DEVICES.clear()
        SERVICES.clear()
        REVISIONS.clear()
        CANARIES.clear()
        AUDIT_EVENTS.clear()

        DEVICES.update(
            {
                "sensor-001": {
                    "id": "sensor-001",
                    "display_name": "Temperature Sensor 001",
                    "fleet": "factory-floor",
                    "labels": {"site": "pune", "criticality": "high"},
                    "agent_status": "online",
                    "agent_version": "2.0.0",
                    "last_seen_at": "2026-10-31T09:12:00Z",
                    "remote_access": {
                        "enabled": True,
                        "broker_url": "wss://broker.smarttouch.local:8443",
                        "allowed_protocols": ["shell", "diagnostics"],
                    },
                },
                "sensor-002": {
                    "id": "sensor-002",
                    "display_name": "Humidity Sensor 002",
                    "fleet": "factory-floor",
                    "labels": {"site": "pune"},
                    "agent_status": "offline",
                    "agent_version": "1.4.2",
                    "last_seen_at": "2026-10-31T06:00:00Z",
                    "remote_access": {
                        "enabled": True,
                        "broker_url": "wss://broker.smarttouch.local:8443",
                        "allowed_protocols": ["diagnostics"],
                    },
                },
            }
        )

        key = service_key("staging", "remote-access-service")
        SERVICES[key] = {
            "name": "remote-access-service",
            "environment": "staging",
            "status": "healthy",
            "image": "harbor.smarttouch.local/library/remote-access-service:2.0.0",
            "replicas": {"desired": 3, "ready": 3},
            "current_revision": "rev-2",
            "last_deployed_at": "2026-10-31T08:00:00Z",
            "configuration": {"LOG_LEVEL": "info"},
        }
        REVISIONS[key] = [
            {
                "id": "rev-2",
                "image": "harbor.smarttouch.local/library/remote-access-service:2.0.0",
                "replicas": 3,
                "created_at": "2026-10-31T08:00:00Z",
                "status": "active",
            },
            {
                "id": "rev-1",
                "image": "harbor.smarttouch.local/library/remote-access-service:1.4.2",
                "replicas": 3,
                "created_at": "2026-10-30T08:00:00Z",
                "status": "superseded",
            },
        ]

        AUDIT_EVENTS.extend(
            [
                {
                    "id": "audit-002",
                    "event": "service.deployed",
                    "actor": "platform-engineer@smarttouch.local",
                    "resource_type": "service",
                    "resource_id": "remote-access-service",
                    "outcome": "success",
                    "timestamp": "2026-10-31T08:00:00Z",
                    "request_id": "req-seed-002",
                    "details": {"environment": "staging", "revision": "rev-2"},
                },
                {
                    "id": "audit-001",
                    "event": "device.registered",
                    "actor": "system",
                    "resource_type": "device",
                    "resource_id": "sensor-001",
                    "outcome": "success",
                    "timestamp": "2026-10-30T09:00:00Z",
                    "request_id": "req-seed-001",
                    "details": {"fleet": "factory-floor"},
                },
            ]
        )


reset_store()
