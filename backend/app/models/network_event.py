
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database.connection import Base


class NetworkEvent(Base):
    __tablename__ = "network_events"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(
        Integer,
        ForeignKey("companies.id"),
        nullable=False,
        index=True
    )

    factory_id = Column(
        Integer,
        ForeignKey("factories.id"),
        nullable=False,
        index=True
    )

    source_ip = Column(String(45), nullable=False)
    destination_ip = Column(String(45), nullable=False)

    protocol = Column(String(20), nullable=False)

    source_port = Column(Integer, nullable=True)
    destination_port = Column(Integer, nullable=True)

    packet_count = Column(Integer, nullable=True)
    bytes_transferred = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)

    event_time = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
