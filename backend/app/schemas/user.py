
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Data received when creating a new user
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)
    company_id: int
    role_id: int


# Data returned by the API
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    company_id: int
    role_id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50
    )

    email: EmailStr | None = None

    password: str | None = Field(
        default=None,
        min_length=8
    )

    role_id: int = Field(default=None)
