from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.permissions import require_role
from app.db.database import get_db
from app.models.booking import Booking
from app.models.centre_test import CentreTest
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.diagnostic_test import DiagnosticTest
from app.models.payment import Payment
from app.models.user import User
from app.models.webhook_event import WebhookEvent
from app.models.notification_outbox import NotificationOutbox
from app.schemas.booking import BookingResponse
from app.schemas.user import UserResponse
from app.services.booking_lifecycle import transition_booking
from app.models.booking_event import BookingEvent
from app.schemas.common import Page
from app.schemas.diagnostic_centre import DiagnosticCentreResponse
from app.schemas.diagnostic_test import DiagnosticTestResponse
from app.schemas.payment import PaymentResponse

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/centres", response_model=Page[DiagnosticCentreResponse])
def admin_centres(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), _: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    query = db.query(DiagnosticCentre).order_by(DiagnosticCentre.name)
    return {"items": query.offset(offset).limit(limit).all(), "total": query.count(), "offset": offset, "limit": limit}


@router.get("/tests", response_model=Page[DiagnosticTestResponse])
def admin_tests(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), _: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    query = db.query(DiagnosticTest).order_by(DiagnosticTest.name)
    return {"items": query.offset(offset).limit(limit).all(), "total": query.count(), "offset": offset, "limit": limit}


@router.get("/overview")
def overview(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    status_counts = dict(db.query(Booking.status, func.count(Booking.id)).group_by(Booking.status).all())
    return {
        "users": db.query(func.count(User.id)).scalar() or 0,
        "centres": db.query(func.count(DiagnosticCentre.id)).filter(DiagnosticCentre.is_active.is_(True)).scalar() or 0,
        "tests": db.query(func.count(DiagnosticTest.id)).filter(DiagnosticTest.is_active.is_(True)).scalar() or 0,
        "bookings": db.query(func.count(Booking.id)).scalar() or 0,
        "payments": db.query(func.count(Payment.id)).scalar() or 0,
        "bookings_by_status": status_counts,
    }


@router.get("/users", response_model=list[UserResponse])
def list_users(
    q: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if q:
        query = query.filter(User.email.ilike(f"%{q}%"))
    return query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()


@router.patch("/users/{user_id}/active", response_model=UserResponse)
def set_user_active(
    user_id: UUID,
    is_active: bool,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id and not is_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


@router.get("/bookings", response_model=Page[BookingResponse])
def list_bookings(
    booking_status: str | None = None,
    centre_id: UUID | None = None,
    patient_id: UUID | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    query = db.query(Booking)
    if booking_status:
        query = query.filter(Booking.status == booking_status)
    if centre_id:
        query = query.join(CentreTest).filter(CentreTest.centre_id == centre_id)
    if patient_id:
        query = query.filter(Booking.patient_id == patient_id)
    return {"items": query.order_by(Booking.appointment_at.desc()).offset(offset).limit(limit).all(), "total": query.count(), "offset": offset, "limit": limit}


@router.get("/audit/booking-events")
def booking_events(
    booking_id: UUID | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=250),
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    query = db.query(BookingEvent)
    if booking_id:
        query = query.filter(BookingEvent.booking_id == booking_id)
    return query.order_by(BookingEvent.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/payments", response_model=Page[PaymentResponse])
def admin_payments(
    payment_status: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    query = db.query(Payment)
    if payment_status:
        query = query.filter(Payment.status == payment_status)
    return {"items": query.order_by(Payment.created_at.desc()).offset(offset).limit(limit).all(), "total": query.count(), "offset": offset, "limit": limit}


@router.get("/notifications")
def notification_outbox(
    notification_status: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=250),
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    query = db.query(NotificationOutbox)
    if notification_status:
        query = query.filter(NotificationOutbox.status == notification_status)
    return {"items": query.order_by(NotificationOutbox.created_at.desc()).offset(offset).limit(limit).all(), "total": query.count(), "offset": offset, "limit": limit}


@router.get("/audit/webhook-events")
def webhook_events(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=250),
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    query = db.query(WebhookEvent)
    return {"items": query.order_by(WebhookEvent.created_at.desc()).offset(offset).limit(limit).all(), "total": query.count(), "offset": offset, "limit": limit}


@router.patch("/bookings/{booking_id}/complete", response_model=BookingResponse)
def complete_booking(
    booking_id: UUID,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).with_for_update().first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    transition_booking(booking, "completed", db=db, actor_id=current_user.id, note="Marked complete by administrator")
    db.commit()
    db.refresh(booking)
    return booking
