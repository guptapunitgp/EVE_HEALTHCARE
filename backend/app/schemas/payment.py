from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class PaymentCreate(BaseModel):
    booking_id: UUID
    idempotency_key: str = Field(
        min_length=10,
        max_length=255,
    )


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_id: UUID
    amount: Decimal
    status: str
    transaction_id: str | None
    idempotency_key: str
    razorpay_order_id: str | None
    razorpay_payment_id: str | None
    currency: str = "INR"
    attempt_number: int = 1
    created_at: datetime
    razorpay_key_id: str | None = None


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str = Field(min_length=5, max_length=255)
    razorpay_payment_id: str = Field(min_length=5, max_length=255)
    razorpay_signature: str = Field(min_length=20, max_length=255)
