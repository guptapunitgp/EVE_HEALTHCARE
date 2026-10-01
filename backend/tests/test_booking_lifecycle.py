from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.booking_lifecycle import transition_booking


@pytest.mark.parametrize(
    ("source", "target"),
    [("pending", "confirmed"), ("pending", "payment_failed"), ("pending", "cancelled"), ("payment_failed", "cancelled"), ("confirmed", "completed")],
)
def test_allowed_booking_transitions(source, target):
    booking = SimpleNamespace(status=source)
    transition_booking(booking, target)
    assert booking.status == target


def test_paid_booking_cannot_be_cancelled_by_generic_transition():
    booking = SimpleNamespace(status="confirmed")
    with pytest.raises(HTTPException) as exc:
        transition_booking(booking, "cancelled")
    assert exc.value.status_code == 409
