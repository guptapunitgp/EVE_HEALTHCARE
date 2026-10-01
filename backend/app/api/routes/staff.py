from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.booking import Booking
from app.models.centre_staff import CentreStaff
from app.models.centre_test import CentreTest
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.user import User
from app.schemas.booking import BookingResponse
from app.schemas.diagnostic_centre import DiagnosticCentreResponse
from app.services.booking_lifecycle import transition_booking
from app.schemas.common import Page
from app.schemas.centre_test import CentreTestResponse
from sqlalchemy import func

router = APIRouter(prefix="/staff", tags=["Centre Staff"])


def _centre_ids(db: Session, user: User) -> list[UUID]:
    if user.role == "admin":
        return [row[0] for row in db.query(DiagnosticCentre.id).all()]
    if user.role != "staff":
        raise HTTPException(status_code=403, detail="Centre staff role required")
    return [row[0] for row in db.query(CentreStaff.centre_id).filter(CentreStaff.user_id == user.id).all()]


@router.get("/centres", response_model=list[DiagnosticCentreResponse])
def my_centres(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ids = _centre_ids(db, current_user)
    return db.query(DiagnosticCentre).filter(DiagnosticCentre.id.in_(ids)).order_by(DiagnosticCentre.name).all()


@router.get("/overview")
def staff_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ids = _centre_ids(db, current_user)
    bookings = db.query(Booking).join(CentreTest).filter(CentreTest.centre_id.in_(ids))
    return {
        "centres": len(ids),
        "bookings": bookings.count(),
        "today": bookings.filter(func.date(Booking.appointment_at) == func.current_date()).count(),
        "confirmed": bookings.filter(Booking.status == "confirmed").count(),
        "pending": bookings.filter(Booking.status == "pending").count(),
        "offerings": db.query(CentreTest).filter(CentreTest.centre_id.in_(ids)).count(),
    }


@router.get("/bookings", response_model=Page[BookingResponse])
def centre_bookings(
    centre_id: UUID | None = None,
    booking_status: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ids = _centre_ids(db, current_user)
    if centre_id:
        if centre_id not in ids:
            raise HTTPException(status_code=403, detail="Not authorized for this centre")
        ids = [centre_id]
    query = db.query(Booking).join(CentreTest).filter(CentreTest.centre_id.in_(ids))
    if booking_status:
        query = query.filter(Booking.status == booking_status)
    return {"items": query.order_by(Booking.appointment_at.desc()).offset(offset).limit(limit).all(), "total": query.count(), "offset": offset, "limit": limit}


@router.get("/offerings", response_model=Page[CentreTestResponse])
def centre_offerings(
    centre_id: UUID | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ids = _centre_ids(db, current_user)
    if centre_id:
        if centre_id not in ids:
            raise HTTPException(status_code=403, detail="Not authorized for this centre")
        ids = [centre_id]
    query = db.query(CentreTest).filter(CentreTest.centre_id.in_(ids))
    return {"items": query.order_by(CentreTest.created_at.desc()).offset(offset).limit(limit).all(), "total": query.count(), "offset": offset, "limit": limit}


@router.patch("/bookings/{booking_id}/complete", response_model=BookingResponse)
def complete_centre_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).with_for_update().first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    _centre_ids(db, current_user)
    centre_test = db.get(CentreTest, booking.centre_test_id)
    if current_user.role != "admin" and centre_test.centre_id not in _centre_ids(db, current_user):
        raise HTTPException(status_code=403, detail="Not authorized for this centre")
    transition_booking(booking, "completed", db=db, actor_id=current_user.id, note="Marked complete by centre staff")
    db.commit()
    db.refresh(booking)
    return booking
