"""Tests for ingestion.intelligence.types (architecture v0.2 §3)."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from ingestion.intelligence.types import (
    CaptureResult,
    Platform,
    PostMetric,
    SocialMetric,
    SourceProvenance,
    WebMetric,
)

UTC = timezone.utc
CAPTURE_DATE = date(2026, 8, 15)
AWARE_NOW = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
NAIVE_NOW = datetime(2026, 8, 15, 12, 0, 0)


def _provenance(**overrides) -> SourceProvenance:
    payload = {
        "url": "https://example.com/page",
        "fetched_at": AWARE_NOW,
        "http_status": 200,
        "method": "scrape",
    }
    payload.update(overrides)
    return SourceProvenance(**payload)


def _social_minimal() -> SocialMetric:
    return SocialMetric(
        bank_id="rbc_bahamas",
        platform=Platform.FACEBOOK,
        capture_date=CAPTURE_DATE,
        source=_provenance(),
    )


def _social_full() -> SocialMetric:
    return SocialMetric(
        bank_id="rbc_bahamas",
        platform=Platform.FACEBOOK,
        capture_date=CAPTURE_DATE,
        followers=10_000,
        posts_in_window=12,
        total_engagement=500,
        reactions=300,
        comments=100,
        shares=50,
        views=1_000,
        source=_provenance(
            archive_url="https://web.archive.org/web/20260815120000/https://example.com/page",
            method="wayback",
        ),
    )


def _post_minimal() -> PostMetric:
    return PostMetric(
        bank_id="rbc_bahamas",
        platform=Platform.INSTAGRAM,
        post_id="post-1",
        posted_at=AWARE_NOW,
        format="photo",
        engagement=42,
        source=_provenance(),
    )


def _post_full() -> PostMetric:
    return PostMetric(
        bank_id="rbc_bahamas",
        platform=Platform.INSTAGRAM,
        post_id="post-1",
        posted_at=AWARE_NOW,
        format="reel",
        caption_excerpt="Short caption",
        engagement=42,
        reactions=30,
        comments=8,
        shares=4,
        views=900,
        source=_provenance(method="api"),
    )


def _web_minimal() -> WebMetric:
    return WebMetric(
        bank_id="rbc_bahamas",
        capture_date=CAPTURE_DATE,
        source=_provenance(),
    )


def _web_full() -> WebMetric:
    return WebMetric(
        bank_id="rbc_bahamas",
        capture_date=CAPTURE_DATE,
        organic_traffic_est=50_000,
        authority_score=72,
        backlinks=1_200,
        referring_domains=340,
        ranking_keywords=890,
        branded_search_share=0.35,
        non_branded_search_share=0.65,
        top_keywords=["bahamas bank", "rbc bahamas"],
        source=_provenance(method="socialblade"),
    )


class TestValidConstruction:
    def test_source_provenance_minimal(self):
        p = _provenance()
        assert p.http_status == 200
        assert p.archive_url is None

    def test_source_provenance_full(self):
        p = _provenance(
            archive_url="https://web.archive.org/web/20260815120000/https://example.com/",
            method="wayback",
            http_status=404,
        )
        assert p.method == "wayback"
        assert p.http_status == 404

    def test_social_metric_minimal(self):
        m = _social_minimal()
        assert m.followers is None
        assert m.platform == Platform.FACEBOOK

    def test_social_metric_full(self):
        m = _social_full()
        assert m.followers == 10_000
        assert m.source.method == "wayback"

    def test_post_metric_minimal(self):
        m = _post_minimal()
        assert m.caption_excerpt is None
        assert m.engagement == 42

    def test_post_metric_full(self):
        m = _post_full()
        assert m.views == 900
        assert m.format == "reel"

    def test_web_metric_minimal(self):
        m = _web_minimal()
        assert m.top_keywords == []
        assert m.authority_score is None

    def test_web_metric_full(self):
        m = _web_full()
        assert m.branded_search_share == 0.35
        assert len(m.top_keywords) == 2

    def test_capture_result_minimal(self):
        r = CaptureResult(bank_id="rbc_bahamas", capture_date=CAPTURE_DATE)
        assert r.social_metrics == []
        assert r.raw_artifacts == {}
        assert r.errors == []

    def test_capture_result_composes_metric_lists(self):
        r = CaptureResult(
            bank_id="rbc_bahamas",
            capture_date=CAPTURE_DATE,
            social_metrics=[_social_minimal(), _social_full()],
            post_metrics=[_post_minimal(), _post_full()],
            web_metrics=[_web_minimal(), _web_full()],
            raw_artifacts={"facebook_html": "data/intelligence/raw/2026-08-15/rbc/facebook.html"},
            errors=["tiktok: rate limited"],
        )
        assert len(r.social_metrics) == 2
        assert len(r.post_metrics) == 2
        assert len(r.web_metrics) == 2
        assert r.raw_artifacts["facebook_html"].endswith(".html")
        assert r.errors[0].startswith("tiktok")


class TestRejections:
    @pytest.mark.parametrize(
        "field_name",
        [
            "followers",
            "posts_in_window",
            "total_engagement",
            "reactions",
            "comments",
            "shares",
            "views",
        ],
    )
    def test_social_metric_rejects_negative_counts(self, field_name: str):
        payload = _social_minimal().model_dump()
        payload[field_name] = -1
        with pytest.raises(ValidationError):
            SocialMetric.model_validate(payload)

    def test_web_metric_rejects_negative_organic_traffic(self):
        payload = _web_minimal().model_dump()
        payload["organic_traffic_est"] = -1
        with pytest.raises(ValidationError):
            WebMetric.model_validate(payload)

    def test_web_metric_rejects_authority_score_below_zero(self):
        payload = _web_minimal().model_dump()
        payload["authority_score"] = -1
        with pytest.raises(ValidationError):
            WebMetric.model_validate(payload)

    def test_web_metric_rejects_authority_score_above_100(self):
        payload = _web_minimal().model_dump()
        payload["authority_score"] = 101
        with pytest.raises(ValidationError):
            WebMetric.model_validate(payload)

    @pytest.mark.parametrize("field_name", ["branded_search_share", "non_branded_search_share"])
    @pytest.mark.parametrize("bad_value", [-0.01, 1.01])
    def test_web_metric_rejects_probability_out_of_range(
        self, field_name: str, bad_value: float
    ):
        payload = _web_minimal().model_dump()
        payload[field_name] = bad_value
        with pytest.raises(ValidationError):
            WebMetric.model_validate(payload)

    def test_post_metric_rejects_caption_excerpt_over_280(self):
        payload = _post_minimal().model_dump()
        payload["caption_excerpt"] = "x" * 281
        with pytest.raises(ValidationError):
            PostMetric.model_validate(payload)

    def test_source_provenance_rejects_naive_fetched_at(self):
        with pytest.raises(ValidationError):
            _provenance(fetched_at=NAIVE_NOW)

    def test_post_metric_rejects_naive_posted_at(self):
        payload = _post_minimal().model_dump()
        payload["posted_at"] = NAIVE_NOW
        with pytest.raises(ValidationError):
            PostMetric.model_validate(payload)

    def test_post_metric_engagement_rejects_negative(self):
        payload = _post_minimal().model_dump()
        payload["engagement"] = -1
        with pytest.raises(ValidationError):
            PostMetric.model_validate(payload)
