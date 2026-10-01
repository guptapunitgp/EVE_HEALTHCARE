from fastapi import HTTPException, status
from app.models.booking_event import BookingEvent

ALLOWED_TRANSITIONS = {
    "pending": {"confirmed", "payment_failed", "cancelled"},
    "payment_failed": {"pending", "confirmed", "cancelled"},
    "confirmed": {"completed"},
    "cancelled": set(),
    "completed": set(),
}


def transition_booking(booking, target: str, db=None, actor_id=None, note: str | None = None) -> None:
    """Apply one permitted booking-state transition or return a client error."""
    allowed = ALLOWED_TRANSITIONS.get(booking.status, set())
    if target not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Booking cannot transition from {booking.status} to {target}",
        )
    previous = booking.status
    booking.status = target
    if db is not None:
        db.add(BookingEvent(booking_id=booking.id, actor_id=actor_id, from_status=previous, to_status=target, note=note))
