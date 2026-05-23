"""Run the full Intelligence capture for a given date across cohort banks."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import date

from backend.app.services.document_ingestion import INTELLIGENCE_DATA_DIR, REPO_ROOT
from ingestion.intelligence.capture.registry import ScrapeStatus, mark_capture
from ingestion.intelligence.cohort import get_cohort_entry, load_cohort_file
from ingestion.intelligence.errors import CaptureError
from ingestion.intelligence.logging_config import get_logger
from ingestion.intelligence.social import wayback
from ingestion.intelligence.types import CaptureResult

SCRAPERS: dict[str, Callable[..., Awaitable[CaptureResult]]] = {
    "wayback": wayback.capture,
}

logger = get_logger(__name__)


def merge_capture_results(results: list[CaptureResult]) -> CaptureResult:
    """Combine multiple scraper results for the same bank and capture date."""
    if not results:
        raise ValueError("merge_capture_results requires at least one CaptureResult")

    bank_id = results[0].bank_id
    capture_date = results[0].capture_date

    social_metrics: list = []
    post_metrics: list = []
    web_metrics: list = []
    raw_artifacts: dict[str, str] = {}
    errors: list[str] = []

    for result in results:
        if result.bank_id != bank_id:
            raise ValueError(
                f"bank_id mismatch: expected {bank_id!r}, got {result.bank_id!r}"
            )
        if result.capture_date != capture_date:
            raise ValueError(
                f"capture_date mismatch: expected {capture_date!r}, "
                f"got {result.capture_date!r}"
            )
        social_metrics.extend(result.social_metrics)
        post_metrics.extend(result.post_metrics)
        web_metrics.extend(result.web_metrics)
        # Prefer scraper-prefixed keys (e.g. youtube_profile_html); namespacing
        # is deferred — raise on collision rather than silently overwrite.
        for key, path in result.raw_artifacts.items():
            if key in raw_artifacts:
                raise ValueError(f"raw_artifacts key collision: {key!r}")
            raw_artifacts[key] = path
        errors.extend(result.errors)

    return CaptureResult(
        bank_id=bank_id,
        capture_date=capture_date,
        social_metrics=social_metrics,
        post_metrics=post_metrics,
        web_metrics=web_metrics,
        raw_artifacts=raw_artifacts,
        errors=errors,
    )


def _scrape_status(
    platforms_captured: list[str],
    platforms_failed: list[str],
) -> ScrapeStatus:
    if not platforms_failed:
        return "complete"
    if platforms_captured:
        return "partial"
    return "failed"


async def capture_one(
    bank_id: str,
    capture_date: date,
    scrapers: list[str] | None = None,
) -> tuple[CaptureResult, ScrapeStatus]:
    """Run selected scrapers for one bank and persist the merged result."""
    cohort_entry = get_cohort_entry(bank_id)
    scraper_names = scrapers if scrapers is not None else list(SCRAPERS.keys())

    for name in scraper_names:
        if name not in SCRAPERS:
            raise ValueError(f"Unknown scraper: {name!r}")

    successful: list[CaptureResult] = []
    platforms_captured: list[str] = []
    platforms_failed: list[str] = []
    failure_errors: list[str] = []

    for name in scraper_names:
        try:
            result = await SCRAPERS[name](bank_id, cohort_entry, capture_date)
            successful.append(result)
            platforms_captured.append(name)
        except CaptureError as exc:
            logger.warning("Scraper %s failed for %s: %s", name, bank_id, exc)
            failure_errors.append(str(exc))
            platforms_failed.append(name)
        except Exception as exc:
            logger.exception("Unexpected error in scraper %s for %s", name, bank_id)
            failure_errors.append(str(exc))
            platforms_failed.append(name)

    if successful:
        merged = merge_capture_results(successful)
    else:
        merged = CaptureResult(bank_id=bank_id, capture_date=capture_date)

    merged.errors.extend(failure_errors)

    processed_path = (
        INTELLIGENCE_DATA_DIR / "processed" / capture_date.isoformat() / f"{bank_id}.json"
    )
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    processed_path.write_text(merged.model_dump_json(indent=2), encoding="utf-8")
    rel_processed = str(processed_path.relative_to(REPO_ROOT))

    scrape_status = _scrape_status(platforms_captured, platforms_failed)
    mark_capture(
        bank_id,
        capture_date,
        platforms_captured=platforms_captured,
        platforms_failed=platforms_failed,
        raw_artifact_paths=dict(merged.raw_artifacts),
        processed_path=rel_processed,
        scrape_status=scrape_status,
    )

    return merged, scrape_status


async def capture_run(
    capture_date: date,
    bank_ids: list[str] | None = None,
    scrapers: list[str] | None = None,
) -> tuple[list[CaptureResult], list[ScrapeStatus]]:
    """Run capture_one sequentially for each bank on the given date."""
    if bank_ids is None:
        bank_ids = [entry.id for entry in load_cohort_file().cohort]

    scraper_names = scrapers if scrapers is not None else list(SCRAPERS.keys())
    logger.info(
        "Starting capture run for %s: %d bank(s), scrapers=%s",
        capture_date.isoformat(),
        len(bank_ids),
        scraper_names,
    )

    results: list[CaptureResult] = []
    statuses: list[ScrapeStatus] = []
    status_counts = {"complete": 0, "partial": 0, "failed": 0}

    for bank_id in bank_ids:
        result, status = await capture_one(bank_id, capture_date, scrapers=scrapers)
        results.append(result)
        statuses.append(status)
        status_counts[status] += 1

    logger.info(
        "Capture run finished for %s: complete=%d partial=%d failed=%d",
        capture_date.isoformat(),
        status_counts["complete"],
        status_counts["partial"],
        status_counts["failed"],
    )

    return results, statuses
