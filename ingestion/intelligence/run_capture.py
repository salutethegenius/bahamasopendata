"""CLI entry for Intelligence captures.

Usage (from repo root):

    python -m ingestion.intelligence.run_capture --date 2026-08-15

Or:

    PYTHONPATH=. python ingestion/intelligence/run_capture.py --date 2026-08-15
"""
from __future__ import annotations

import os
import sys

# When executed as a file, sys.path[0] is this package dir and shadows the
# stdlib ``types`` module with ``ingestion.intelligence.types``. Fix that
# before importing pathlib / argparse (which pull in stdlib types via enum).
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if sys.path and os.path.abspath(sys.path[0]) == _SCRIPT_DIR:
    sys.path.pop(0)

ROOT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import argparse
import asyncio
from datetime import date

from ingestion.intelligence.capture.orchestrator import capture_run


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Run Intelligence capture pipeline")
    parser.add_argument("--date", required=True, type=date.fromisoformat, help="Capture date (YYYY-MM-DD)")
    parser.add_argument("--bank", action="append", dest="banks", help="Bank id (repeatable; default: all cohort banks)")
    parser.add_argument("--scrapers", action="append", dest="scrapers", help="Scraper name (repeatable; default: all)")
    return parser


def main() -> None:
    """Run capture pipeline from the command line."""
    args = build_parser().parse_args()
    _, statuses = asyncio.run(
        capture_run(args.date, bank_ids=args.banks, scrapers=args.scrapers)
    )
    if all(status == "complete" for status in statuses):
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
