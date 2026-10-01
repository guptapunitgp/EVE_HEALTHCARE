import math


def haversine_km(latitude: float, longitude: float, other_latitude: float, other_longitude: float) -> float:
    """Return great-circle distance between validated WGS84 coordinates."""
    lat1, lat2 = math.radians(latitude), math.radians(other_latitude)
    delta_lat = lat2 - lat1
    delta_lon = math.radians(other_longitude - longitude)
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    return 2 * 6371.0 * math.atan2(math.sqrt(max(0.0, min(1.0, a))), math.sqrt(max(0.0, 1.0 - a)))
