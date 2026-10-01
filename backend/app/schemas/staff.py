from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class StaffAssignRequest(BaseModel):
    email: EmailStr


class CentreStaffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    centre_id: UUID
    user_id: UUID
    email: EmailStr
    full_name: str | None
