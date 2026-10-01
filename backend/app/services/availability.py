from datetime import datetime, time
from zoneinfo import ZoneInfo


def is_centre_open(opening_hours: dict | None, timezone_name: str, appointment_at: datetime) -> bool:
    """Check a local appointment against centre hours; absent hours mean no configured restriction."""
    if not opening_hours:
        return True
    local_time = appointment_at.astimezone(ZoneInfo(timezone_name))
    day_name = local_time.strftime("%A").casefold()
    hours = next((value for key, value in opening_hours.items() if key.casefold() == day_name), None)
    if hours is None:
        return False
    if isinstance(hours, dict):
        if hours.get("closed") is True:
            return False
        opening, closing = hours.get("open"), hours.get("close")
    elif isinstance(hours, str):
        normalized = hours.strip().casefold()
        if normalized in {"closed", "close", "off"}:
            return False
        if normalized in {"open 24 hours", "24 hours"}:
            return True
        if "-" not in normalized:
            return True
        opening, closing = (part.strip() for part in normalized.split("-", 1))
    else:
        return False
    try:
        start = time.fromisoformat(opening)
        end = time.fromisoformat(closing)
    except (TypeError, ValueError):
        return False
    current = local_time.timetz().replace(tzinfo=None)
    return start <= current < end if start <= end else current >= start or current < end
