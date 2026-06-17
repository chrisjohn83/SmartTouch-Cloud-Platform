from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB

from app.database.connection import Base


class AnalyticsEventEntity(Base):

    __tablename__ = "analytics_events"

    event_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True
    )

    event_version = Column(
        String(20),
        nullable=False
    )

    timestamp = Column(
        DateTime,
        nullable=False
    )

    source = Column(
        String(50),
        nullable=False
    )

    event_type = Column(
        String(100),
        nullable=False
    )

    user_id = Column(
        String(100),
        nullable=True
    )

    session_id = Column(
        String(100),
        nullable=True
    )

    payload = Column(
        JSONB,
        nullable=False
    )
