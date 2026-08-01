"""CLI: Wayback follower backfill across the measurement window.

Pulls historical FB/IG/X follower snapshots via the ``wayback`` scraper for
each month-midpoint date from ``--start`` to ``--end`` (defaults cover
Oct 2025 – Jul 2026 per architecture §7).

Usage (from repo root):

    backend/.venv/bin/python ingestion/intelligence/run_wayback_backfill.py
    backend/.venv/bin/python ingestion/intelligence/run_wayback_backfill.py \\
      --start 2025-10-01 --end 2026-07-31 --bank commonwealth_bank --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import date, timedelta
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if sys.path and os.path.abspath(sys.path[0]) == _SCRIPT_DIR:
    sys.path.pop(0)

ROOT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ingestion.intelligence.capture.orchestrator import capture_run  # noqa: E402
from ingestion.intelligence.cohort import load_cohort_file  # noqa: E402
from ingestion.intelligence.logging_config import get_logger  # noqa: E402
from ingestion.intelligence.types import CaptureResult  # noqa: E402

logger = get_logger(__name__)

DEFAULT_START = date(2025, 10, 1)
DEFAULT_END = date(2026, 7, 31)
DEFAULT_DAY = 15
DEFAULT_RETRIES = 3
DEFAULT_RETRY_SLEEP_SECONDS = 60.0
DEFAULT_BETWEEN_DATES_SLEEP = 20.0
DEFAULT_BETWEEN_BANKS_SLEEP = 10.0


def _is_rate_limited_result(errors: list[str]) -> bool:
    """True when Wayback CDX/snapshot rate-limit hard-failed this bank."""
    joined = " ".join(errors).lower()
    return (
        "rate-limited" in joined
        or "unavailable (503)" in joined
        or "unavailable (429)" in joined
    )


def month_midpoint_dates(
    start: date,
    end: date,
    *,
    day: int = DEFAULT_DAY,
) -> list[date]:
    """Return ``day``-of-month dates for each month overlapping [start, end].

    Clamps ``day`` to the last day of short months (e.g. day=31 → Feb 28/29).
    """
    if end < start:
        raise ValueError(f"end {end} is before start {start}")
    if day < 1 or day > 31:
        raise ValueError(f"day must be 1–31, got {day}")

    dates: list[date] = []
    year, month = start.year, start.month
    while True:
        # Advance to next month to discover last day of current month.
        if month == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, month + 1
        last_day = (date(next_year, next_month, 1) - timedelta(days=1)).day
        candidate = date(year, month, min(day, last_day))
        if candidate > end:
            break
        if candidate >= start:
            dates.append(candidate)
        year, month = next_year, next_month
        if date(year, month, 1) > end and candidate >= end:
            break
        # Safety: stop if we moved past end's month without adding
        if (year, month) > (end.year, end.month):
            break
    return dates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Wayback backfill for Intelligence follower trajectories"
    )
    parser.add_argument(
        "--start",
        type=date.fromisoformat,
        default=DEFAULT_START,
        help=f"Inclusive window start (default {DEFAULT_START.isoformat()})",
    )
    parser.add_argument(
        "--end",
        type=date.fromisoformat,
        default=DEFAULT_END,
        help=f"Inclusive window end (default {DEFAULT_END.isoformat()})",
    )
    parser.add_argument(
        "--day",
        type=int,
        default=DEFAULT_DAY,
        help="Day-of-month midpoint to sample (default 15)",
    )
    parser.add_argument(
        "--bank",
        action="append",
        dest="banks",
        help="Bank id (repeatable; default: all cohort banks)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help="Retries per capture date on hard failure (default 3)",
    )
    parser.add_argument(
        "--retry-sleep",
        type=float,
        default=DEFAULT_RETRY_SLEEP_SECONDS,
        help="Seconds to sleep between rate-limit retries (default 60)",
    )
    parser.add_argument(
        "--between-dates-sleep",
        type=float,
        default=DEFAULT_BETWEEN_DATES_SLEEP,
        help="Seconds to sleep between capture dates (default 20)",
    )
    parser.add_argument(
        "--between-banks-sleep",
        type=float,
        default=DEFAULT_BETWEEN_BANKS_SLEEP,
        help="Seconds to sleep between banks within a date (default 10)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned dates and exit without capturing",
    )
    return parser


async def backfill_bank_date(
    capture_date: date,
    bank_id: str,
    *,
    retries: int,
    retry_sleep: float,
) -> bool:
    """Run wayback-only capture for one bank/date.

    Empty ±7-day CDX windows are success (honest nulls). Retry only on
    Wayback 429/503 rate-limit hard failures.
    """
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            results, statuses = await capture_run(
                capture_date,
                bank_ids=[bank_id],
                scrapers=["wayback"],
            )
            result: CaptureResult = results[0]
            if not _is_rate_limited_result(result.errors):
                logger.info(
                    "Wayback backfill %s / %s ok (status=%s)",
                    capture_date.isoformat(),
                    bank_id,
                    statuses[0],
                )
                return True
            logger.warning(
                "Wayback backfill %s / %s attempt %d/%d rate-limited",
                capture_date.isoformat(),
                bank_id,
                attempt,
                retries,
            )
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Wayback backfill %s / %s attempt %d/%d failed: %s",
                capture_date.isoformat(),
                bank_id,
                attempt,
                retries,
                exc,
            )
        if attempt < retries:
            await asyncio.sleep(retry_sleep)
    if last_error is not None:
        logger.error(
            "Wayback backfill exhausted retries for %s / %s: %s",
            capture_date.isoformat(),
            bank_id,
            last_error,
        )
    return False


async def run_backfill(args: argparse.Namespace) -> int:
    dates = month_midpoint_dates(args.start, args.end, day=args.day)
    bank_ids = args.banks or [entry.id for entry in load_cohort_file().cohort]
    logger.info(
        "Wayback backfill plan: %d date(s) × %d bank(s) from %s to %s (day=%d)",
        len(dates),
        len(bank_ids),
        args.start.isoformat(),
        args.end.isoformat(),
        args.day,
    )
    for capture_date in dates:
        logger.info("  planned %s", capture_date.isoformat())

    if args.dry_run:
        return 0

    failures: list[str] = []
    for date_index, capture_date in enumerate(dates):
        if date_index > 0 and args.between_dates_sleep > 0:
            await asyncio.sleep(args.between_dates_sleep)
        for bank_index, bank_id in enumerate(bank_ids):
            if bank_index > 0 and args.between_banks_sleep > 0:
                await asyncio.sleep(args.between_banks_sleep)
            ok = await backfill_bank_date(
                capture_date,
                bank_id,
                retries=args.retries,
                retry_sleep=args.retry_sleep,
            )
            if not ok:
                failures.append(f"{bank_id}@{capture_date.isoformat()}")

    if failures:
        logger.error(
            "Wayback backfill finished with %d failure(s): %s",
            len(failures),
            ", ".join(failures),
        )
        return 1

    logger.info(
        "Wayback backfill finished successfully for %d date(s) × %d bank(s)",
        len(dates),
        len(bank_ids),
    )
    return 0


def main() -> None:
    args = build_parser().parse_args()
    sys.exit(asyncio.run(run_backfill(args)))


if __name__ == "__main__":
    main()
