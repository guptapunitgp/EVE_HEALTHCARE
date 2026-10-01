
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.booking import Booking
from app.models.centre_test import CentreTest
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.diagnostic_test import DiagnosticTest
from app.services.availability import is_centre_open
from app.models.payment import Payment
from app.models.user import User
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingUpdate,
)
from app.services.booking_lifecycle import transition_booking
from app.models.booking_event import BookingEvent
from app.models.notification_outbox import NotificationOutbox
from app.schemas.common import Page

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"],
)


@router.post(
    "",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Find the centre-test mapping
    centre_test = db.get(CentreTest, booking_data.centre_test_id)

    if centre_test is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Centre test not found",
        )

    # Do not allow booking an unavailable test
    if not centre_test.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This diagnostic test is currently unavailable",
        )

    if booking_data.appointment_at.tzinfo is None:
        raise HTTPException(status_code=422, detail="appointment_at must include a timezone")
    if booking_data.appointment_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Appointments must be in the future")

    # Serialize allocations on the centre-test row, then reject occupied slots.
    centre_test = (
        db.query(CentreTest).filter(CentreTest.id == centre_test.id)
        .with_for_update().one()
    )
    centre = db.get(DiagnosticCentre, centre_test.centre_id)
    diagnostic_test = db.get(DiagnosticTest, centre_test.test_id)
    if not centre or not centre.is_active or not diagnostic_test or not diagnostic_test.is_active or not centre_test.is_available:
        raise HTTPException(status_code=400, detail="This test offering is no longer available")
    if not is_centre_open(centre.opening_hours, centre.timezone, booking_data.appointment_at):
        raise HTTPException(status_code=409, detail="The centre is closed at the selected appointment time")
    appointment_utc = booking_data.appointment_at.astimezone(timezone.utc).replace(tzinfo=None)
    occupied = db.query(Booking).filter(
        Booking.centre_test_id == centre_test.id,
        Booking.appointment_at == appointment_utc,
        Booking.status.in_(["pending", "confirmed"]),
    ).first()
    if occupied:
        raise HTTPException(status_code=409, detail="This appointment slot is already booked")

    # Create booking using trusted server-side values
    booking = Booking(
        patient_id=current_user.id,
        centre_test_id=centre_test.id,
        appointment_at=appointment_utc,
        amount=centre_test.price,
        status="pending",
    )

    db.add(booking)
    db.flush()
    db.add(BookingEvent(booking_id=booking.id, actor_id=current_user.id, from_status=None, to_status="pending", note="Appointment requested"))
    db.add(NotificationOutbox(event_type="booking_created", payload={"booking_id": str(booking.id), "status": "pending"}))
    db.commit()
    db.refresh(booking)

    # Queue notification after booking is saved
    try:
        from app.services.notification_tasks import dispatch_outbox
        dispatch_outbox.delay()
    except Exception:
        pass

    return booking


@router.get(
    "",
    response_model=Page[BookingResponse],
)
def list_my_bookings(
    booking_status: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Booking).filter(Booking.patient_id == current_user.id)
    if booking_status:
        query = query.filter(Booking.status == booking_status)
    if start_at:
        query = query.filter(Booking.appointment_at >= start_at.astimezone(timezone.utc).replace(tzinfo=None))
    if end_at:
        query = query.filter(Booking.appointment_at <= end_at.astimezone(timezone.utc).replace(tzinfo=None))
    total = query.count()
    bookings = query.order_by(Booking.appointment_at.desc()).offset(offset).limit(limit).all()
    return {"items": bookings, "total": total, "offset": offset, "limit": limit}


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
)
def get_my_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id,
            Booking.patient_id == current_user.id,
        )
        .first()
    )

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    return booking


@router.patch(
    "/{booking_id}",
    response_model=BookingResponse,
)
def update_my_booking(
    booking_id: UUID,
    booking_data: BookingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id,
            Booking.patient_id == current_user.id,
        )
        .with_for_update()
        .first()
    )

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if booking.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending bookings can be modified",
        )

    if booking_data.appointment_at is not None:
        if booking_data.appointment_at.tzinfo is None or booking_data.appointment_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=422, detail="A future timezone-aware appointment is required")
        payment = db.query(Payment).filter(Payment.booking_id == booking.id).order_by(Payment.attempt_number.desc()).first()
        if payment is not None and payment.status == "pending":
            raise HTTPException(status_code=409, detail="Resolve payment before changing appointment")
        conflict = db.query(Booking).filter(
            Booking.id != booking.id,
            Booking.centre_test_id == booking.centre_test_id,
            Booking.appointment_at == booking_data.appointment_at.astimezone(timezone.utc).replace(tzinfo=None),
            Booking.status.in_(["pending", "confirmed"]),
        ).first()
        if conflict:
            raise HTTPException(status_code=409, detail="This appointment slot is already booked")

    update_data = booking_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "appointment_at" and value is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        setattr(booking, field, value)

    db.commit()
    db.refresh(booking)

    return booking


@router.patch(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
)
def cancel_my_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Find booking owned by the authenticated patient
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id,
            Booking.patient_id == current_user.id,
        )
        .with_for_update()
        .first()
    )

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Only pending or payment-failed bookings can be cancelled
    if booking.status not in {"pending", "payment_failed"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This booking cannot be cancelled",
        )

    # Check the associated payment, if one exists
    payment = (
        db.query(Payment)
        .filter(Payment.booking_id == booking.id)
        .order_by(Payment.attempt_number.desc())
        .first()
    )

    # Only allow cancellation when there is no payment
    # or the payment has failed
    if payment is not None and payment.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Payment must be resolved before "
                "this booking can be cancelled"
            ),
        )

    # Update booking status
    transition_booking(booking, "cancelled", db=db, actor_id=current_user.id, note="Patient cancelled booking")
    db.add(NotificationOutbox(event_type="booking_cancelled", payload={"booking_id": str(booking.id), "status": "cancelled"}))

    db.commit()
    db.refresh(booking)

    # Queue mock notification after successful commit
    try:
        from app.services.notification_tasks import dispatch_outbox
        dispatch_outbox.delay()
    except Exception:
        pass

    return booking
