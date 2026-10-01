import pytest

from app.services.geo import haversine_km


def test_same_point_has_zero_distance():
    assert haversine_km(12.9716, 77.5946, 12.9716, 77.5946) == pytest.approx(0)


def test_distance_is_symmetric_and_reasonable():
    bangalore_to_chennai = haversine_km(12.9716, 77.5946, 13.0827, 80.2707)
    reverse = haversine_km(13.0827, 80.2707, 12.9716, 77.5946)
    assert bangalore_to_chennai == pytest.approx(reverse)
    assert 280 < bangalore_to_chennai < 300


def test_antimeridian_uses_short_arc():
    assert haversine_km(0, 179.9, 0, -179.9) == pytest.approx(22.24, abs=0.2)
