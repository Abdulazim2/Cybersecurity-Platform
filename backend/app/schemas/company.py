from pydantic import BaseModel, ConfigDict, Field, EmailStr


class CompanyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=2,
        max_length=150
    )

    industry: str | None = Field(
        default=None,
        max_length=100
    )

    email: EmailStr | None = None


class CompanyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150
    )

    industry: str | None = Field(
        default=None,
        max_length=100
    )

    email: EmailStr | None = None


class CompanyResponse(BaseModel):
    id: int
    name: str
    industry: str | None = None
    email: EmailStr | None = None

    model_config = ConfigDict(from_attributes=True)
