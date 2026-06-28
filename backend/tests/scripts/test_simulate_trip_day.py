import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.simulate_trip_day import (
    calculate_reset_starts_at,
    calculate_simulated_starts_at,
    validate_target_day,
)


def test_validate_target_day_allows_zero_and_total_days():
    validate_target_day(0, 7)
    validate_target_day(7, 7)


def test_validate_target_day_rejects_negative_day():
    with pytest.raises(ValueError, match="between 0 and 7"):
        validate_target_day(-1, 7)


def test_validate_target_day_rejects_day_after_trip_length():
    with pytest.raises(ValueError, match="between 0 and 7"):
        validate_target_day(8, 7)


def test_calculate_simulated_starts_at_sets_started_days_in_the_past():
    now = datetime(2026, 6, 28, 12, 0, tzinfo=UTC)

    assert calculate_simulated_starts_at(1, 3, now) == now - timedelta(days=3)
    assert calculate_simulated_starts_at(2, 3, now) == now - timedelta(days=2)
    assert calculate_simulated_starts_at(3, 3, now) == now - timedelta(days=1)


def test_calculate_simulated_starts_at_sets_future_days_in_the_future():
    now = datetime(2026, 6, 28, 12, 0, tzinfo=UTC)

    assert calculate_simulated_starts_at(4, 3, now) == now + timedelta(days=1)
    assert calculate_simulated_starts_at(5, 3, now) == now + timedelta(days=2)


def test_calculate_reset_starts_at_uses_trip_start_date():
    trip_start = date(2026, 7, 10)

    assert calculate_reset_starts_at(trip_start, 1) == datetime(2026, 7, 10, 0, 0, tzinfo=UTC)
    assert calculate_reset_starts_at(trip_start, 3) == datetime(2026, 7, 12, 0, 0, tzinfo=UTC)

