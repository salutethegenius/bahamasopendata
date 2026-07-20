"""CLI entry for Intelligence delta validation against trial exports.

Usage (from repo root):

    python ingestion/intelligence/run_validate.py \\
      --trial data/intelligence/exports/rival_iq_commonwealth_bank_2026-08-15.json

    python ingestion/intelligence/run_validate.py --trial path.json --apply
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ingestion.intelligence.capture.delta_validator import (  # noqa: E402
    load_trial_export,
    validate_capture,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Intelligence captures against Rival IQ / SEMrush exports"
    )
    parser.add_argument(
        "--trial",
        required=True,
        type=Path,
        help="Path to trial export JSON (TrialExport schema)",
    )
    parser.add_argument(
        "--processed",
        type=Path,
        default=None,
        help="Optional processed capture JSON (default: resolve via registry)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write validation_status / delta_variance_pct into registry.json",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Override variance threshold percent (default: 5)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    trial = load_trial_export(args.trial)
    kwargs = {"processed_path": args.processed, "apply": args.apply}
    if args.threshold is not None:
        kwargs["threshold_pct"] = args.threshold
    report = validate_capture(trial, **kwargs)
    print(json.dumps(report.model_dump(mode="json"), indent=2))
    if report.validation_status == "validated":
        sys.exit(0)
    if report.validation_status == "pending":
        sys.exit(2)
    sys.exit(1)


if __name__ == "__main__":
    main()
