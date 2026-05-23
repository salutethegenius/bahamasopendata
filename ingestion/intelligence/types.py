"""Pydantic contracts for the Intelligence imprint pipeline.

See intel/bod-intelligence-architecture.md §3. ``CaptureResult`` is the lingua
franca returned by each scraper's ``capture()`` and consumed by the registry,
validators, and exporters.
"""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import AwareDatetime, BaseModel, Field, HttpUrl


class Platform(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
    WEBSITE = "website"


class SourceProvenance(BaseModel):
    url: HttpUrl
    fetched_at: AwareDatetime
    http_status: int
    method: str
    archive_url: Optional[HttpUrl] = None


class SocialMetric(BaseModel):
    bank_id: str
    platform: Platform
    capture_date: date
    followers: Optional[int] = Field(default=None, ge=0)
    posts_in_window: Optional[int] = Field(default=None, ge=0)
    total_engagement: Optional[int] = Field(default=None, ge=0)
    reactions: Optional[int] = Field(default=None, ge=0)
    comments: Optional[int] = Field(default=None, ge=0)
    shares: Optional[int] = Field(default=None, ge=0)
    views: Optional[int] = Field(default=None, ge=0)
    source: SourceProvenance


class PostMetric(BaseModel):
    bank_id: str
    platform: Platform
    post_id: str
    posted_at: AwareDatetime
    format: str
    caption_excerpt: Optional[str] = Field(default=None, max_length=280)
    engagement: int = Field(ge=0)
    reactions: Optional[int] = Field(default=None, ge=0)
    comments: Optional[int] = Field(default=None, ge=0)
    shares: Optional[int] = Field(default=None, ge=0)
    views: Optional[int] = Field(default=None, ge=0)
    source: SourceProvenance


class WebMetric(BaseModel):
    bank_id: str
    capture_date: date
    organic_traffic_est: Optional[int] = Field(default=None, ge=0)
    authority_score: Optional[int] = Field(default=None, ge=0, le=100)
    backlinks: Optional[int] = Field(default=None, ge=0)
    referring_domains: Optional[int] = Field(default=None, ge=0)
    ranking_keywords: Optional[int] = Field(default=None, ge=0)
    branded_search_share: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    non_branded_search_share: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    top_keywords: list[str] = Field(default_factory=list)
    source: SourceProvenance


class CaptureResult(BaseModel):
    bank_id: str
    capture_date: date
    social_metrics: list[SocialMetric] = Field(default_factory=list)
    post_metrics: list[PostMetric] = Field(default_factory=list)
    web_metrics: list[WebMetric] = Field(default_factory=list)
    raw_artifacts: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    attempted_platforms: list[Platform] = Field(
        default_factory=list,
        description=(
            "Platforms this capture attempted, regardless of measurement success. "
            "Used to derive platforms_failed."
        ),
    )
