"""CLI entry for Intelligence captures.

Usage (from repo root with PYTHONPATH including the repo):

    python ingestion/intelligence/run_capture.py --date 2026-08-15
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

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
