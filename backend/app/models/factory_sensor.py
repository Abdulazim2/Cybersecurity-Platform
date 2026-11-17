
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean
)
from sqlalchemy.sql import func

from app.database.connection import Base


class FactorySensor(Base):
    __tablename__ = "factory_sensors"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    factory_id = Column(
        Integer,
        ForeignKey("factories.id"),
        nullable=False,
        index=True
    )

    name = Column(
        String(150),
        nullable=False
    )

    token_hash = Column(
        String(64),
        nullable=False,
        unique=True
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )

    last_seen = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
