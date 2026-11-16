from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    JSON
)
from sqlalchemy.sql import func

from app.database.connection import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

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

    uploaded_dataset_id = Column(
        Integer,
        ForeignKey("uploaded_datasets.id"),
        nullable=False,
        index=True
    )

    record_index = Column(
        Integer,
        nullable=True
    )

    model_name = Column(
        String(100),
        nullable=False
    )

    model_version = Column(
        String(50),
        nullable=True
    )

    prediction_label = Column(
        String(100),
        nullable=True
    )

    confidence_score = Column(
        Float,
        nullable=True
    )

    shap_explanation = Column(
        JSON,
        nullable=True
    )

    prediction_output = Column(
        JSON,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )