"""Deployment API v2 routes."""

from copy import deepcopy
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from ..models import (
    CanaryRequest,
    CanaryResponse,
    Environment,
    RevisionListResponse,
    RollbackRequest,
    ServiceDeploymentRequest,
    ServiceListResponse,
    ServiceResponse,
    ServiceStatus,
)
from ..security import Principal, get_principal
from ..store import (
    CANARIES,
    LOCK,
    REVISIONS,
    SERVICES,
    paginate,
    record_audit,
    service_key,
    utcnow,
)


router = APIRouter(prefix="/v2/services", tags=["Deployment API v2"])


def _service_or_404(name: str, environment: Environment) -> tuple[str, dict]:
    key = service_key(environment.value, name)
    with LOCK:
        service = SERVICES.get(key)
        if service is None:
            raise HTTPException(
                status_code=404,
                detail=f"Service not found in {environment.value}: {name}",
            )
        return key, deepcopy(service)


@router.get("", response_model=ServiceListResponse, summary="List deployed services")
def list_services(
    environment: Environment | None = None,
    status_filter: ServiceStatus | None = Query(default=None, alias="status"),
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    _: Principal = Depends(get_principal),
) -> dict:
    with LOCK:
        services = sorted(SERVICES.values(), key=lambda item: (item["environment"], item["name"]))
        if environment:
            services = [item for item in services if item["environment"] == environment.value]
        if status_filter:
            services = [item for item in services if item["status"] == status_filter.value]
        page, next_cursor = paginate(services, cursor, limit)
    return {"data": page, "meta": {"limit": limit, "next_cursor": next_cursor}}


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Deploy a service",
)
def deploy_service(
    payload: ServiceDeploymentRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    key = service_key(payload.environment.value, payload.name)
    with LOCK:
        existing = SERVICES.get(key)
        revision_number = len(REVISIONS.get(key, [])) + 1
        revision_id = f"rev-{revision_number}"
        service = {
            "name": payload.name,
            "environment": payload.environment.value,
            "status": "healthy" if not payload.dry_run else "validated",
            "image": payload.image,
            "replicas": {
                "desired": payload.replicas,
                "ready": payload.replicas if not payload.dry_run else 0,
            },
            "current_revision": revision_id if not payload.dry_run else existing and existing.get("current_revision"),
            "previous_revision": existing and existing.get("current_revision"),
            "last_deployed_at": utcnow(),
            "configuration": payload.configuration,
            "dry_run": payload.dry_run,
        }
        if not payload.dry_run:
            SERVICES[key] = service
            revisions = REVISIONS.setdefault(key, [])
            for revision in revisions:
                revision["status"] = "superseded"
            revisions.insert(
                0,
                {
                    "id": revision_id,
                    "image": payload.image,
                    "replicas": payload.replicas,
                    "created_at": service["last_deployed_at"],
                    "status": "active",
                },
            )
    if not payload.dry_run:
        record_audit(
            "service.deployed",
            principal.subject,
            "service",
            payload.name,
            request.state.request_id,
            {"environment": payload.environment.value, "revision": revision_id},
        )
    return {"data": deepcopy(service)}


@router.get("/{service_name}", response_model=ServiceResponse, summary="Get service status")
def get_service(
    service_name: str,
    environment: Environment,
    _: Principal = Depends(get_principal),
) -> dict:
    _, service = _service_or_404(service_name, environment)
    return {"data": service}


@router.delete("/{service_name}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove a service")
def remove_service(
    service_name: str,
    environment: Environment,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> Response:
    key, _ = _service_or_404(service_name, environment)
    with LOCK:
        del SERVICES[key]
        CANARIES.pop(key, None)
    record_audit(
        "service.removed",
        principal.subject,
        "service",
        service_name,
        request.state.request_id,
        {"environment": environment.value},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{service_name}/revisions",
    response_model=RevisionListResponse,
    summary="List service revisions",
)
def list_revisions(
    service_name: str,
    environment: Environment,
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    _: Principal = Depends(get_principal),
) -> dict:
    key, _ = _service_or_404(service_name, environment)
    with LOCK:
        page, next_cursor = paginate(REVISIONS.get(key, []), cursor, limit)
    return {"data": page, "meta": {"limit": limit, "next_cursor": next_cursor}}


@router.post(
    "/{service_name}/rollback",
    response_model=ServiceResponse,
    summary="Roll back a service",
)
def rollback_service(
    service_name: str,
    environment: Environment,
    payload: RollbackRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    key, _ = _service_or_404(service_name, environment)
    with LOCK:
        revisions = REVISIONS.get(key, [])
        target_id = payload.revision or (revisions[1]["id"] if len(revisions) > 1 else None)
        target = next((item for item in revisions if item["id"] == target_id), None)
        if target is None:
            raise HTTPException(status_code=404, detail=f"Revision not found: {target_id}")
        for revision in revisions:
            revision["status"] = "superseded"
        target["status"] = "active"
        SERVICES[key].update(
            {
                "image": target["image"],
                "replicas": {"desired": target["replicas"], "ready": target["replicas"]},
                "current_revision": target["id"],
                "status": "healthy",
                "last_deployed_at": utcnow(),
            }
        )
        service = deepcopy(SERVICES[key])
    record_audit(
        "service.rolled_back",
        principal.subject,
        "service",
        service_name,
        request.state.request_id,
        {"environment": environment.value, "revision": target["id"]},
    )
    return {"data": service}


@router.get(
    "/{service_name}/canary",
    response_model=CanaryResponse,
    summary="Get canary configuration",
)
def get_canary(
    service_name: str,
    environment: Environment,
    _: Principal = Depends(get_principal),
) -> dict:
    key, _ = _service_or_404(service_name, environment)
    with LOCK:
        canary = CANARIES.get(key)
        if canary is None:
            raise HTTPException(status_code=404, detail="No canary is configured for this service.")
        return {"data": deepcopy(canary)}


@router.put(
    "/{service_name}/canary",
    response_model=CanaryResponse,
    summary="Configure canary traffic",
)
def set_canary(
    service_name: str,
    environment: Environment,
    payload: CanaryRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    key, service = _service_or_404(service_name, environment)
    canary = {
        "service_name": service_name,
        "environment": environment.value,
        "stable_image": service["image"],
        "canary_image": payload.image,
        "canary_weight": payload.weight,
        "stable_weight": 100 - payload.weight,
        "updated_at": utcnow(),
    }
    with LOCK:
        CANARIES[key] = canary
    record_audit(
        "service.canary_updated",
        principal.subject,
        "service",
        service_name,
        request.state.request_id,
        {"environment": environment.value, "weight": payload.weight},
    )
    return {"data": deepcopy(canary)}


@router.delete("/{service_name}/canary", status_code=status.HTTP_204_NO_CONTENT, summary="Cancel a canary")
def cancel_canary(
    service_name: str,
    environment: Environment,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> Response:
    key, _ = _service_or_404(service_name, environment)
    with LOCK:
        if key not in CANARIES:
            raise HTTPException(status_code=404, detail="No canary is configured for this service.")
        del CANARIES[key]
    record_audit(
        "service.canary_cancelled",
        principal.subject,
        "service",
        service_name,
        request.state.request_id,
        {"environment": environment.value},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{service_name}/canary/promote",
    response_model=ServiceResponse,
    summary="Promote a canary",
)
def promote_canary(
    service_name: str,
    environment: Environment,
    request: Request,
    principal: Principal = Depends(get_principal),
) -> dict:
    key, _ = _service_or_404(service_name, environment)
    with LOCK:
        canary = CANARIES.get(key)
        if canary is None:
            raise HTTPException(status_code=404, detail="No canary is configured for this service.")
        revision_id = f"rev-{uuid4().hex[:8]}"
        SERVICES[key]["image"] = canary["canary_image"]
        SERVICES[key]["current_revision"] = revision_id
        SERVICES[key]["last_deployed_at"] = utcnow()
        for revision in REVISIONS.setdefault(key, []):
            revision["status"] = "superseded"
        REVISIONS[key].insert(
            0,
            {
                "id": revision_id,
                "image": canary["canary_image"],
                "replicas": SERVICES[key]["replicas"]["desired"],
                "created_at": SERVICES[key]["last_deployed_at"],
                "status": "active",
            },
        )
        del CANARIES[key]
        service = deepcopy(SERVICES[key])
    record_audit(
        "service.canary_promoted",
        principal.subject,
        "service",
        service_name,
        request.state.request_id,
        {"environment": environment.value, "revision": revision_id},
    )
    return {"data": service}
