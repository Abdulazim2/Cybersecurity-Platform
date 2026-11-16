from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.database.connection import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False, unique=True)

    industry = Column(String(100), nullable=True)

    email = Column(String(150), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )