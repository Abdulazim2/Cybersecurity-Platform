
from pydantic import BaseModel, ConfigDict, Field


class FactoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=2,
        max_length=150
    )

    location: str | None = Field(
        default=None,
        max_length=200
    )

    # Required only for Super Admin at API level.
    # Ordinary Admin always uses their own company.
    company_id: int | None = Field(
        default=None,
        gt=0
    )


class FactoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150
    )

    location: str | None = Field(
        default=None,
        max_length=200
    )


class FactoryResponse(BaseModel):
    id: int
    name: str
    location: str | None = None
    company_id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
