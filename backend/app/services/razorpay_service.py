import httpx
from fastapi import HTTPException

from app.core.config import settings

def create_razorpay_order(
    amount: int,
    receipt: str,
) -> dict:
    """
    Create a Razorpay order.

    amount must be provided in the smallest currency unit.
    For INR:
        ₹500 = 50000 paise
    """

    order_data = {
        "amount": amount,
        "currency": "INR",
        "receipt": receipt,
    }

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=503, detail="Razorpay test credentials are not configured")
    try:
        response = httpx.post(
            "https://api.razorpay.com/v1/orders",
            json=order_data,
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Payment provider could not create an order") from exc
