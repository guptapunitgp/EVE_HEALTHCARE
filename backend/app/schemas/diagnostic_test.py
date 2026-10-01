from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DiagnosticTestCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    preparation_instructions: str | None = None
    duration_minutes: int = Field(default=30, ge=1, le=1440)
    category: str | None = Field(default=None, max_length=100)
    sample_type: str | None = Field(default=None, max_length=100)
    estimated_report_time_minutes: int | None = Field(default=None, ge=1, le=10080)


class DiagnosticTestUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    preparation_instructions: str | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    category: str | None = Field(default=None, max_length=100)
    sample_type: str | None = Field(default=None, max_length=100)
    estimated_report_time_minutes: int | None = Field(default=None, ge=1, le=10080)
    is_active: bool | None = None


class DiagnosticTestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    preparation_instructions: str | None
    duration_minutes: int
    is_active: bool
    category: str | None = None
    sample_type: str | None = None
    estimated_report_time_minutes: int | None = None
