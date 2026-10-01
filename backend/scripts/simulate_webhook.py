"""Send a real-format, correctly signed Razorpay test webhook to local EVE."""
import argparse
import hashlib
import hmac
import json
from uuid import uuid4

import httpx

from app.core.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--order-id", required=True, help="Razorpay order ID returned by EVE")
    parser.add_argument("--payment-id", required=True, help="Synthetic provider payment ID")
    parser.add_argument("--amount-paise", required=True, type=int)
    parser.add_argument("--status", choices=["captured", "failed"], default="captured")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000/api/v1/payments/webhook/")
    args = parser.parse_args()
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        parser.error("Set RAZORPAY_WEBHOOK_SECRET in backend/.env first")

    event_type = "payment.captured" if args.status == "captured" else "payment.failed"
    event_id = f"local_sim_{uuid4().hex}"
    payload = {
        "entity": "event",
        "account_id": "acc_local_simulation",
        "event": event_type,
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": args.payment_id,
                    "entity": "payment",
                    "amount": args.amount_paise,
                    "currency": "INR",
                    "order_id": args.order_id,
                    "status": args.status,
                }
            }
        },
        "created_at": 0,
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    signature = hmac.new(settings.RAZORPAY_WEBHOOK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    response = httpx.post(
        args.api_url,
        content=raw,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": signature, "X-Razorpay-Event-Id": event_id},
        timeout=15,
    )
    print(response.status_code)
    print(response.text)
    response.raise_for_status()


if __name__ == "__main__":
    main()
