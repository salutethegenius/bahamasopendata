"""CLI entrypoint for the Bahamas Open Data ingestion pipeline."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.ingestion_pipeline import IngestionRunOptions, run_ingestion_pipeline


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Run the Bahamas Open Data ingestion pipeline")
    parser.add_argument("--skip-scraper", action="store_true", help="Skip source discovery and download")
    parser.add_argument("--skip-parser", action="store_true", help="Skip PDF parsing and chunk generation")
    parser.add_argument("--skip-normalizer", action="store_true", help="Skip Gemini normalization")
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip embeddings upload")
    parser.add_argument("--force", action="store_true", help="Re-run stages even if document status is already success")
    return parser


def main() -> int:
    """Run the ingestion pipeline from the command line."""
    parser = build_parser()
    args = parser.parse_args()

    options = IngestionRunOptions(
        run_scraper=not args.skip_scraper,
        run_parser=not args.skip_parser,
        run_normalizer=not args.skip_normalizer,
        run_embeddings=not args.skip_embeddings,
        force=args.force,
    )

    summary = run_ingestion_pipeline(options)
    print(json.dumps(summary, indent=2))
    return 0 if summary.get("status") in {"success", "partial_success"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
