from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import field_validator


class DiagnosticCentreCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    address: str = Field(min_length=5, max_length=500)
    city: str = Field(min_length=2, max_length=100)
    description: str | None = None
    state: str | None = Field(default=None, max_length=100)
    timezone: str = "Asia/Kolkata"
    postal_code: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    opening_hours: dict[str, str] | None = None
    services: list[str] | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("timezone must be a valid IANA timezone") from error
        return value
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    phone: str | None = Field(default=None, max_length=20)


class DiagnosticCentreUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    address: str | None = Field(default=None, min_length=5, max_length=500)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    state: str | None = Field(default=None, max_length=100)
    timezone: str | None = None
    postal_code: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    opening_hours: dict[str, str] | None = None
    services: list[str] | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    phone: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as error:
            raise ValueError("timezone must be a valid IANA timezone") from error
        return value


class DiagnosticCentreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    address: str
    city: str
    description: str | None = None
    state: str | None = None
    timezone: str = "Asia/Kolkata"
    postal_code: str | None = None
    email: str | None = None
    opening_hours: dict | None = None
    services: list | None = None
    latitude: float | None
    longitude: float | None
    phone: str | None
    is_active: bool


class NearbyCentreResponse(DiagnosticCentreResponse):
    distance_km: float
