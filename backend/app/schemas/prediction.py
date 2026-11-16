from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PredictionCreate(BaseModel):
    uploaded_dataset_id: int = Field(gt=0)

    record_index: int | None = Field(default=None, ge=0)

    model_name: str = Field(min_length=1, max_length=100)

    model_version: str | None = Field(default=None, max_length=50)

    prediction_label: str | None = Field(default=None, max_length=100)

    confidence_score: float | None = None

    shap_explanation: dict[str, Any] | None = None

    prediction_output: dict[str, Any] | list[Any] | None = None

    @field_validator("model_name")
    @classmethod
    def normalize_model_name(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Model name cannot be empty")

        return value


class PredictionResponse(BaseModel):
    id: int

    company_id: int
    factory_id: int
    uploaded_dataset_id: int

    record_index: int | None

    model_name: str
    model_version: str | None

    prediction_label: str | None
    confidence_score: float | None

    shap_explanation: dict[str, Any] | None
    prediction_output: dict[str, Any] | list[Any] | None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)