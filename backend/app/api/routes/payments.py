import json
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.models.booking import Booking
from app.models.notification_outbox import NotificationOutbox
from app.models.payment import Payment
from app.models.user import User
from app.models.webhook_event import WebhookEvent
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentVerifyRequest
from app.services.booking_lifecycle import transition_booking
from app.services.razorpay_service import create_razorpay_order
from app.services.payment_security import verify_checkout_signature, verify_webhook_signature

router = APIRouter(prefix="/payments", tags=["Payments"])


def _payment_response(payment: Payment) -> dict:
    return {
        "id": payment.id,
        "booking_id": payment.booking_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status,
        "transaction_id": payment.transaction_id,
        "idempotency_key": payment.idempotency_key,
        "razorpay_order_id": payment.razorpay_order_id,
        "razorpay_payment_id": payment.razorpay_payment_id,
        "attempt_number": payment.attempt_number,
        "created_at": payment.created_at,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID or None,
    }


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(
        Booking.id == payment_data.booking_id,
        Booking.patient_id == current_user.id,
    ).with_for_update().first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status not in {"pending", "payment_failed"}:
        raise HTTPException(status_code=409, detail="Payment cannot be created for this booking")

    existing_key = db.query(Payment).filter(Payment.idempotency_key == payment_data.idempotency_key).first()
    if existing_key:
        if existing_key.booking_id != booking.id:
            raise HTTPException(status_code=409, detail="Idempotency key is already in use")
        return _payment_response(existing_key)

    latest = db.query(Payment).filter(Payment.booking_id == booking.id).order_by(Payment.attempt_number.desc()).first()
    if latest and latest.status == "pending":
        return _payment_response(latest)
    if latest and latest.status == "success":
        raise HTTPException(status_code=409, detail="This booking is already paid")

    if booking.status == "payment_failed":
        transition_booking(booking, "pending", db=db, actor_id=current_user.id, note="Patient started a payment retry")
    amount_in_paise = int(Decimal(str(booking.amount)) * Decimal("100"))
    order = create_razorpay_order(amount=amount_in_paise, receipt=f"{booking.id}-{(latest.attempt_number + 1) if latest else 1}")
    if int(order.get("amount", -1)) != amount_in_paise or order.get("currency") != "INR" or not order.get("id"):
        raise HTTPException(status_code=502, detail="Payment provider returned an invalid order")

    payment = Payment(
        booking_id=booking.id,
        amount=booking.amount,
        currency="INR",
        status="pending",
        transaction_id=None,
        idempotency_key=payment_data.idempotency_key,
        razorpay_order_id=order["id"],
        razorpay_payment_id=None,
        attempt_number=(latest.attempt_number + 1) if latest else 1,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return _payment_response(payment)


@router.get("/", response_model=list[PaymentResponse])
def list_my_payments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payments = (
        db.query(Payment)
        .join(Booking, Payment.booking_id == Booking.id)
        .filter(Booking.patient_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .limit(100)
        .all()
    )
    return [_payment_response(p) for p in payments]


@router.post("/verify", response_model=PaymentResponse)
def verify_checkout_payment(
    data: PaymentVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = db.query(Payment).filter(Payment.razorpay_order_id == data.razorpay_order_id).first()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment order not found")
    booking = db.query(Booking).filter(Booking.id == payment.booking_id).with_for_update().first()
    if booking is None or booking.patient_id != current_user.id:
        raise HTTPException(status_code=404, detail="Payment order not found")
    payment = db.query(Payment).filter(Payment.id == payment.id).with_for_update().first()
    if not verify_checkout_signature(settings.RAZORPAY_KEY_SECRET, data.razorpay_order_id, data.razorpay_payment_id, data.razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid Razorpay payment signature")
    if payment.status == "failed":
        raise HTTPException(status_code=409, detail="This payment attempt has already failed")
    if payment.status != "success":
        payment.status = "success"
        payment.razorpay_payment_id = data.razorpay_payment_id
        payment.transaction_id = data.razorpay_payment_id
        if booking.status == "payment_failed":
            transition_booking(booking, "confirmed", db=db, actor_id=current_user.id, note="Verified Razorpay checkout capture")
        elif booking.status == "pending":
            transition_booking(booking, "confirmed", db=db, actor_id=current_user.id, note="Verified Razorpay checkout capture")
        else:
            raise HTTPException(status_code=409, detail="Booking is not eligible for payment confirmation")
        db.add(NotificationOutbox(event_type="payment_success", payload={"booking_id": str(booking.id), "status": "success"}))
        db.commit()
        db.refresh(payment)
        try:
            from app.services.notification_tasks import dispatch_outbox
            dispatch_outbox.delay()
        except Exception:
            pass
    return _payment_response(payment)


@router.post("/webhook/")
async def payment_webhook(
    request: Request,
    x_razorpay_signature: str = Header(...),
    x_razorpay_event_id: str = Header(...),
    db: Session = Depends(get_db),
):
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Payment webhook secret is not configured")
    raw = await request.body()
    if not verify_webhook_signature(settings.RAZORPAY_WEBHOOK_SECRET, raw, x_razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    try:
        body = json.loads(raw)
        event_type = body["event"]
        entity = body["payload"]["payment"]["entity"]
        order_id = entity["order_id"]
        provider_payment_id = entity["id"]
        amount = int(entity["amount"])
        currency = entity["currency"]
    except (ValueError, TypeError, KeyError):
        raise HTTPException(status_code=400, detail="Malformed Razorpay webhook payload") from None

    state = {"payment.captured": "success", "payment.failed": "failed"}.get(event_type)
    if state is None:
        raise HTTPException(status_code=400, detail="Unsupported Razorpay event")
    prior = db.query(WebhookEvent).filter(WebhookEvent.event_id == x_razorpay_event_id).first()
    if prior:
        return {"success": True, "message": "Webhook event already processed", "event_id": x_razorpay_event_id}

    payment = db.query(Payment).filter(Payment.razorpay_order_id == order_id).first()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment order not found")
    expected_amount = int(Decimal(str(payment.amount)) * Decimal("100"))
    if amount != expected_amount or currency != payment.currency:
        raise HTTPException(status_code=400, detail="Webhook amount or currency does not match the payment")
    booking = db.query(Booking).filter(Booking.id == payment.booking_id).with_for_update().first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    payment = db.query(Payment).filter(Payment.id == payment.id).with_for_update().first()
    # Another request may have claimed the provider event while this request waited on the row locks.
    prior = db.query(WebhookEvent).filter(WebhookEvent.event_id == x_razorpay_event_id).first()
    if prior:
        return {"success": True, "message": "Webhook event already processed", "event_id": x_razorpay_event_id}

    changed = False
    if payment.status not in {"success", "failed"}:
        payment.status = state
        payment.razorpay_payment_id = provider_payment_id
        payment.transaction_id = provider_payment_id
        if state == "success" and booking.status in {"pending", "payment_failed"}:
            transition_booking(booking, "confirmed", db=db, note="Razorpay payment captured")
            changed = True
        elif state == "failed" and booking.status == "pending":
            transition_booking(booking, "payment_failed", db=db, note="Razorpay payment failed")
            changed = True
    elif payment.status == "failed" and state == "success":
        # A signed capture event supersedes a delayed failure event for the same order.
        payment.status = "success"
        payment.razorpay_payment_id = provider_payment_id
        payment.transaction_id = provider_payment_id
        if booking.status == "payment_failed":
            transition_booking(booking, "confirmed", db=db, note="Late Razorpay capture event")
            changed = True

    db.add(WebhookEvent(event_id=x_razorpay_event_id, event_type=event_type, payment_id=payment.id, processed=changed))
    if changed:
        db.add(NotificationOutbox(event_type=f"payment_{payment.status}", payload={"booking_id": str(booking.id), "status": payment.status}))
    db.commit()
    if changed:
        try:
            from app.services.notification_tasks import dispatch_outbox
            dispatch_outbox.delay()
        except Exception:
            pass
    return {"success": True, "event_id": x_razorpay_event_id, "payment_status": payment.status, "booking_status": booking.status}
