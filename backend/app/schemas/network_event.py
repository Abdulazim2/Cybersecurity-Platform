import math
from datetime import datetime
from ipaddress import ip_address

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NetworkEventCreate(BaseModel):
    factory_id: int

    source_ip: str
    destination_ip: str

    protocol: str = Field(min_length=1, max_length=20)

    source_port: int | None = Field(default=None, ge=0, le=65535)
    destination_port: int | None = Field(default=None, ge=0, le=65535)

    packet_count: int | None = Field(default=None, ge=0)
    bytes_transferred: int | None = Field(default=None, ge=0)
    duration: float | None = Field(default=None, ge=0)

    event_time: datetime | None = None

    @field_validator("source_ip", "destination_ip")
    @classmethod
    def validate_ip(cls, value):
        try:
            ip_address(value)
        except ValueError:
            raise ValueError("Invalid IP address")
        return value
    @field_validator("protocol")
    @classmethod
    def normalize_protocol(cls, value):
        value = value.strip().upper()

        if not value:
            raise ValueError("Protocol cannot be empty")

        return value
    @field_validator("duration")
    @classmethod
    def validate_duration(cls, value):
        if value is not None and not math.isfinite(value):
            raise ValueError("Duration must be a finite number")

        return value

class NetworkEventResponse(BaseModel):
    id: int
    company_id: int
    factory_id: int

    source_ip: str
    destination_ip: str
    protocol: str

    source_port: int | None
    destination_port: int | None

    packet_count: int | None
    bytes_transferred: int | None
    duration: float | None

    event_time: datetime | None
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
