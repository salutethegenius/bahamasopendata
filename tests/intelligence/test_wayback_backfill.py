"""Tests for Wayback backfill date planning."""
from __future__ import annotations

from datetime import date

import pytest

from ingestion.intelligence.run_wayback_backfill import (
    _is_rate_limited_result,
    month_midpoint_dates,
)


def test_rate_limited_detection():
    assert _is_rate_limited_result(
        ["Wayback CDX rate-limited or unavailable (503)"]
    )
    assert not _is_rate_limited_result(
        ["wayback: no snapshot within ±7 days of 2025-10-15 for https://example.com"]
    )


def test_month_midpoint_dates_default_window():
    dates = month_midpoint_dates(date(2025, 10, 1), date(2026, 7, 31))
    assert dates[0] == date(2025, 10, 15)
    assert dates[-1] == date(2026, 7, 15)
    assert len(dates) == 10


def test_month_midpoint_dates_clamps_short_months():
    dates = month_midpoint_dates(date(2026, 2, 1), date(2026, 2, 28), day=31)
    assert dates == [date(2026, 2, 28)]


def test_month_midpoint_dates_rejects_inverted_range():
    with pytest.raises(ValueError, match="before start"):
        month_midpoint_dates(date(2026, 7, 1), date(2026, 1, 1))
