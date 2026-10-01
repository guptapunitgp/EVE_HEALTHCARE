from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BookingCreate(BaseModel):
    centre_test_id: UUID
    appointment_at: datetime


class BookingUpdate(BaseModel):
    appointment_at: datetime | None = None


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    centre_test_id: UUID
    appointment_at: datetime
    amount: float
    status: str
    created_at: datetime
    updated_at: datetime
