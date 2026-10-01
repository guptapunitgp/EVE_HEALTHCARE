from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CentreTestCreate(BaseModel):
    centre_id: UUID
    test_id: UUID
    price: float = Field(gt=0)


class CentreTestUpdate(BaseModel):
    price: float | None = Field(default=None, gt=0)
    is_available: bool | None = None


class CentreTestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    centre_id: UUID
    test_id: UUID
    price: float
    is_available: bool
