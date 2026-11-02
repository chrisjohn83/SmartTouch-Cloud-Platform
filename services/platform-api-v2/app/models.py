"""Pydantic models shared by the SmartTouch API v2 routers."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class Environment(StrEnum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class ServiceStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    DEPLOYING = "deploying"


class DeviceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,63}$", examples=["sensor-003"])
    display_name: str = Field(min_length=1, max_length=120)
    fleet: str | None = Field(default=None, max_length=80)
    agent_version: str = Field(default="2.0.0", max_length=40)
    labels: dict[str, str] = Field(default_factory=dict)


class DeviceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    fleet: str | None = Field(default=None, max_length=80)
    labels: dict[str, str] | None = None

    @model_validator(mode="after")
    def require_change(self) -> "DeviceUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be supplied.")
        return self


class ServiceDeploymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[a-z][a-z0-9-]{2,62}$")
    environment: Environment
    image: str = Field(min_length=3, max_length=300)
    replicas: int = Field(default=1, ge=1, le=100)
    configuration: dict[str, str] = Field(default_factory=dict)
    dry_run: bool = False


class RollbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision: str | None = Field(default=None, description="Revision to restore; defaults to the previous revision.")


class CanaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image: str = Field(min_length=3, max_length=300)
    weight: int = Field(ge=1, le=99)


class ProblemDetail(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str
    request_id: str
    errors: list[dict] | None = None


class CursorMeta(BaseModel):
    limit: int
    next_cursor: str | None = None


class RemoteAccessConfig(BaseModel):
    enabled: bool
    broker_url: str
    allowed_protocols: list[str]


class Device(BaseModel):
    id: str
    display_name: str
    fleet: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    agent_status: AgentStatus
    agent_version: str
    last_seen_at: datetime | None = None
    remote_access: RemoteAccessConfig


class DeviceResponse(BaseModel):
    data: Device


class DeviceListResponse(BaseModel):
    data: list[Device]
    meta: CursorMeta


class AgentStatusDetail(BaseModel):
    device_id: str
    agent_status: AgentStatus
    last_seen_at: datetime | None = None
    broker_url: str
    latency_ms: int | None = None
    checked_at: datetime


class AgentStatusResponse(BaseModel):
    data: AgentStatusDetail


class ReplicaStatus(BaseModel):
    desired: int
    ready: int


class Service(BaseModel):
    name: str
    environment: Environment
    status: str
    image: str
    replicas: ReplicaStatus
    current_revision: str | None = None
    previous_revision: str | None = None
    last_deployed_at: datetime
    configuration: dict[str, str] = Field(default_factory=dict)
    dry_run: bool = False


class ServiceResponse(BaseModel):
    data: Service


class ServiceListResponse(BaseModel):
    data: list[Service]
    meta: CursorMeta


class Revision(BaseModel):
    id: str
    image: str
    replicas: int
    created_at: datetime
    status: str


class RevisionListResponse(BaseModel):
    data: list[Revision]
    meta: CursorMeta


class CanaryState(BaseModel):
    service_name: str
    environment: Environment
    stable_image: str
    canary_image: str
    canary_weight: int
    stable_weight: int
    updated_at: datetime


class CanaryResponse(BaseModel):
    data: CanaryState


class AuditEvent(BaseModel):
    id: str
    event: str
    actor: str
    resource_type: str
    resource_id: str
    outcome: str
    timestamp: datetime
    request_id: str
    details: dict = Field(default_factory=dict)


class AuditEventResponse(BaseModel):
    data: AuditEvent


class AuditEventListResponse(BaseModel):
    data: list[AuditEvent]
    meta: CursorMeta
