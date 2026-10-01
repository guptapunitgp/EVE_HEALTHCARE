from datetime import datetime, timezone

from app.services.availability import is_centre_open


def test_opening_hours_use_the_centres_local_timezone():
    hours = {"monday": "09:00-17:00"}
    # 03:30 UTC is 09:00 in Bengaluru.
    appointment = datetime(2026, 10, 5, 3, 30, tzinfo=timezone.utc)
    assert is_centre_open(hours, "Asia/Kolkata", appointment)


def test_closed_day_and_closed_interval_are_rejected():
    appointment = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)
    assert not is_centre_open({"monday": "closed"}, "Asia/Kolkata", appointment)
    assert not is_centre_open({"tuesday": "09:00-17:00"}, "Asia/Kolkata", appointment)


def test_opening_interval_is_start_inclusive_and_end_exclusive():
    hours = {"monday": {"open": "09:00", "close": "17:00"}}
    starts = datetime(2026, 10, 5, 3, 30, tzinfo=timezone.utc)
    ends = datetime(2026, 10, 5, 11, 30, tzinfo=timezone.utc)
    assert is_centre_open(hours, "Asia/Kolkata", starts)
    assert not is_centre_open(hours, "Asia/Kolkata", ends)


def test_missing_hours_are_unrestricted_but_invalid_hours_are_closed():
    appointment = datetime(2026, 10, 5, 3, 30, tzinfo=timezone.utc)
    assert is_centre_open(None, "Asia/Kolkata", appointment)
    assert not is_centre_open({"monday": "not-a-time"}, "Asia/Kolkata", appointment)
