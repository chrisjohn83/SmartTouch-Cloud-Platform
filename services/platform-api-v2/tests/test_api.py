"""Contract-level tests for all three SmartTouch API v2 surfaces."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import reset_store


client = TestClient(app)
AUTH = {"Authorization": "Bearer demo-token"}


@pytest.fixture(autouse=True)
def fresh_store():
    reset_store()
    yield


def test_health_is_public():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP", "version": "2.0.0"}
    assert response.headers["X-Request-ID"].startswith("req-")


def test_protected_endpoint_uses_problem_details():
    response = client.get("/v2/devices")
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["title"] == "Unauthorized"


def test_device_lifecycle_and_audit_event():
    create = client.post(
        "/v2/devices",
        headers=AUTH,
        json={
            "id": "sensor-003",
            "display_name": "Pressure Sensor 003",
            "fleet": "factory-floor",
            "labels": {"site": "pune"},
        },
    )
    assert create.status_code == 201
    assert create.json()["data"]["agent_status"] == "unknown"

    update = client.patch(
        "/v2/devices/sensor-003",
        headers=AUTH,
        json={"fleet": "assembly-line"},
    )
    assert update.status_code == 200
    assert update.json()["data"]["fleet"] == "assembly-line"

    events = client.get(
        "/v2/audit/events?resource_id=sensor-003",
        headers=AUTH,
    )
    assert events.status_code == 200
    assert [item["event"] for item in events.json()["data"]] == [
        "device.updated",
        "device.registered",
    ]

    remove = client.delete("/v2/devices/sensor-003", headers=AUTH)
    assert remove.status_code == 204
    assert client.get("/v2/devices/sensor-003", headers=AUTH).status_code == 404


def test_device_cursor_pagination():
    first = client.get("/v2/devices?limit=1", headers=AUTH)
    assert first.status_code == 200
    cursor = first.json()["meta"]["next_cursor"]
    assert cursor

    second = client.get(f"/v2/devices?limit=1&cursor={cursor}", headers=AUTH)
    assert second.status_code == 200
    assert second.json()["data"][0]["id"] == "sensor-002"

    invalid = client.get("/v2/devices?cursor=not-a-cursor", headers=AUTH)
    assert invalid.status_code == 400


def test_deployment_revision_rollback_and_canary():
    deploy = client.post(
        "/v2/services",
        headers=AUTH,
        json={
            "name": "telemetry-service",
            "environment": "staging",
            "image": "registry.smarttouch.io/telemetry:2.0.0",
            "replicas": 2,
        },
    )
    assert deploy.status_code == 201
    assert deploy.json()["data"]["current_revision"] == "rev-1"

    deploy_again = client.post(
        "/v2/services",
        headers=AUTH,
        json={
            "name": "telemetry-service",
            "environment": "staging",
            "image": "registry.smarttouch.io/telemetry:2.1.0",
            "replicas": 3,
        },
    )
    assert deploy_again.json()["data"]["current_revision"] == "rev-2"

    rollback = client.post(
        "/v2/services/telemetry-service/rollback?environment=staging",
        headers=AUTH,
        json={},
    )
    assert rollback.status_code == 200
    assert rollback.json()["data"]["image"].endswith(":2.0.0")

    canary = client.put(
        "/v2/services/telemetry-service/canary?environment=staging",
        headers=AUTH,
        json={"image": "registry.smarttouch.io/telemetry:2.2.0", "weight": 10},
    )
    assert canary.status_code == 200
    assert canary.json()["data"]["stable_weight"] == 90

    promote = client.post(
        "/v2/services/telemetry-service/canary/promote?environment=staging",
        headers=AUTH,
    )
    assert promote.status_code == 200
    assert promote.json()["data"]["image"].endswith(":2.2.0")


def test_each_v2_surface_is_in_combined_openapi():
    schema = client.get("/openapi.json").json()
    assert "/v2/devices" in schema["paths"]
    assert "/v2/services" in schema["paths"]
    assert "/v2/audit/events" in schema["paths"]
