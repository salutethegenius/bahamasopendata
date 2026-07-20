"""Tests for the Intelligence snapshot API assembly helpers."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from app.api import intelligence as intel_api


CAPTURE_DATE = date(2026, 8, 15)


def _write_processed(tmp_path: Path, bank_id: str, payload: dict) -> None:
    folder = tmp_path / "data" / "intelligence" / "processed" / CAPTURE_DATE.isoformat()
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{bank_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_build_snapshot_reads_confirmed_metrics(monkeypatch, tmp_path):
    monkeypatch.setattr(intel_api, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence")
    _write_processed(
        tmp_path,
        "commonwealth_bank",
        {
            "bank_id": "commonwealth_bank",
            "capture_date": CAPTURE_DATE.isoformat(),
            "social_metrics": [
                {
                    "platform": "facebook",
                    "followers": 6650,
                    "source": {"method": "scrape", "url": "https://facebook.com/x"},
                },
                {
                    "platform": "youtube",
                    "followers": 843,
                    "source": {"method": "api", "url": "https://youtube.com"},
                },
            ],
            "web_metrics": [
                {
                    "authority_score": 48,
                    "top_keywords": ["performance:48", "seo:92"],
                    "source": {
                        "method": "api",
                        "url": "https://www.combankltd.com/",
                    },
                }
            ],
            "errors": [],
        },
    )

    # Minimal cohort stub — only one bank needed for assertion path
    class FakeEntry:
        id = "commonwealth_bank"
        display_name = "Commonwealth Bank"
        short_name = "Commonwealth"
        series_token = "--intel-series-3"
        domain = "combankltd.com"

    class FakeCohort:
        cohort = [FakeEntry()]

    monkeypatch.setattr(intel_api, "load_cohort_file", lambda: FakeCohort())

    snapshot = intel_api.build_snapshot(CAPTURE_DATE)
    assert snapshot["capture_date"] == "2026-08-15"
    assert snapshot["confirmed_bank_counts"]["facebook"] == 1
    assert snapshot["confirmed_bank_counts"]["youtube"] == 1
    assert snapshot["confirmed_bank_counts"]["pagespeed"] == 1
    bank = snapshot["banks"][0]
    assert bank["facebook_followers"] == 6650
    assert bank["youtube_subscribers"] == 843
    assert bank["pagespeed"]["performance"] == 48


def test_build_snapshot_raises_when_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(intel_api, "INTELLIGENCE_DATA_DIR", tmp_path / "data" / "intelligence")

    class FakeCohort:
        cohort = []

    monkeypatch.setattr(intel_api, "load_cohort_file", lambda: FakeCohort())
    with pytest.raises(FileNotFoundError):
        intel_api.build_snapshot(CAPTURE_DATE)
