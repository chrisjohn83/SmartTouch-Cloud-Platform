from fastapi import FastAPI
from fastapi import Depends
from sqlalchemy.orm import Session

from app.schemas.analytics_event import AnalyticsEvent
from app.database.connection import engine
from app.database.connection import get_db
from app.database.connection import Base
from app.models.analytics_event_model import AnalyticsEventEntity

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SmartTouch Analytics Service",
    description="Collects analytics events from documentation, API playground, MQTT, OTA, and support systems.",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "service": "SmartTouch Analytics Service",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "UP"
    }


@app.post("/api/v1/analytics/events")
def create_event(
    event: AnalyticsEvent,
    db: Session = Depends(get_db)
):
    event_entity = AnalyticsEventEntity(
        event_id=event.eventId,
        event_version=event.eventVersion,
        timestamp=event.timestamp,
        source=event.source.value,
        event_type=event.eventType.value,
        user_id=event.userId,
        session_id=event.sessionId,
        payload=event.payload
    )

    db.add(event_entity)
    db.commit()

    return {
        "message": "Event stored successfully",
        "eventId": str(event.eventId),
        "eventType": event.eventType.value
    }
