from datetime import UTC, datetime

from app.services.trip_service import compute_in_trip_phase_completions


def _phase(id: str, phase_type: str, starts_at: datetime | None) -> dict:
    return {"id": id, "phase_type": phase_type, "starts_at": starts_at}


def test_in_trip_phase_before_start_not_complete():
    now = datetime(2026, 12, 25, 12, 0, 0, tzinfo=UTC)
    phases = [_phase("p1", "in-trip", datetime(2026, 12, 26, tzinfo=UTC))]
    result = compute_in_trip_phase_completions(phases, now)
    assert result == {"p1": False}


def test_in_trip_phase_on_start_day_complete():
    now = datetime(2026, 12, 26, 8, 0, 0, tzinfo=UTC)
    phases = [_phase("p1", "in-trip", datetime(2026, 12, 26, tzinfo=UTC))]
    result = compute_in_trip_phase_completions(phases, now)
    assert result == {"p1": True}


def test_in_trip_phase_after_start_complete():
    now = datetime(2026, 12, 27, 12, 0, 0, tzinfo=UTC)
    phases = [_phase("p1", "in-trip", datetime(2026, 12, 26, tzinfo=UTC))]
    result = compute_in_trip_phase_completions(phases, now)
    assert result == {"p1": True}


def test_pre_trip_phases_excluded():
    now = datetime(2026, 12, 27, 12, 0, 0, tzinfo=UTC)
    phases = [
        _phase("pre1", "pre-trip", None),
        _phase("p1", "in-trip", datetime(2026, 12, 26, tzinfo=UTC)),
    ]
    result = compute_in_trip_phase_completions(phases, now)
    assert "pre1" not in result
    assert result["p1"] is True


def test_in_trip_phase_no_starts_at_not_complete():
    now = datetime(2026, 12, 27, 12, 0, 0, tzinfo=UTC)
    phases = [_phase("p1", "in-trip", None)]
    result = compute_in_trip_phase_completions(phases, now)
    assert result == {"p1": False}


def test_multiple_days_partial_completion():
    now = datetime(2026, 12, 27, 12, 0, 0, tzinfo=UTC)
    phases = [
        _phase("d1", "in-trip", datetime(2026, 12, 26, tzinfo=UTC)),
        _phase("d2", "in-trip", datetime(2026, 12, 27, tzinfo=UTC)),
        _phase("d3", "in-trip", datetime(2026, 12, 28, tzinfo=UTC)),
    ]
    result = compute_in_trip_phase_completions(phases, now)
    assert result == {"d1": True, "d2": True, "d3": False}


def test_naive_now_does_not_crash():
    now = datetime(2026, 12, 27, 12, 0, 0)  # no tzinfo
    phases = [_phase("p1", "in-trip", datetime(2026, 12, 26, tzinfo=UTC))]
    result = compute_in_trip_phase_completions(phases, now)
    assert result == {"p1": True}


def test_starts_at_as_iso_string():
    now = datetime(2026, 12, 27, 12, 0, 0, tzinfo=UTC)
    phases = [{"id": "p1", "phase_type": "in-trip", "starts_at": "2026-12-26T00:00:00+00:00"}]
    result = compute_in_trip_phase_completions(phases, now)
    assert result == {"p1": True}


def test_empty_phases_returns_empty():
    now = datetime(2026, 12, 27, tzinfo=UTC)
    assert compute_in_trip_phase_completions([], now) == {}


def test_only_pre_trip_phases_returns_empty():
    now = datetime(2026, 12, 27, tzinfo=UTC)
    phases = [_phase("pre1", "pre-trip", None), _phase("pre2", "pre-trip", None)]
    assert compute_in_trip_phase_completions(phases, now) == {}
