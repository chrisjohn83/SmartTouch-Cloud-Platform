from enum import Enum
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, Optional

class EventSource(str, Enum):

    DOCUMENTATION = "DOCUMENTATION"

    PLAYGROUND = "PLAYGROUND"

    API = "API"

    MQTT = "MQTT"

    OTA = "OTA"

    SUPPORT = "SUPPORT"

    AI_ASSISTANT = "AI_ASSISTANT"

class EventType(str, Enum):

    PAGE_VIEW = "PAGE_VIEW"

    SEARCH = "SEARCH"

    SEARCH_CLICK = "SEARCH_CLICK"

    PLAYGROUND_REQUEST = "PLAYGROUND_REQUEST"

    API_CALL = "API_CALL"

    MQTT_CONNECT = "MQTT_CONNECT"

    MQTT_DISCONNECT = "MQTT_DISCONNECT"

    OTA_SUCCESS = "OTA_SUCCESS"

    OTA_FAILURE = "OTA_FAILURE"

    SUPPORT_TICKET = "SUPPORT_TICKET"

    AI_QUESTION = "AI_QUESTION"
class AnalyticsEvent(BaseModel):

    eventId: UUID

    eventVersion: str

    timestamp: datetime

    source: EventSource

    eventType: EventType

    userId: Optional[str] = None

    sessionId: Optional[str] = None

    payload: Dict[str, Any]