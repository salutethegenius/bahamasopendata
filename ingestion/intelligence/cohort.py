"""Load cohort definitions from cohort.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field

COHORT_FILE = Path(__file__).resolve().parent / "cohort.yaml"


class CohortSocial(BaseModel):
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    twitter: Optional[str] = None
    youtube: Optional[str] = None
    tiktok: Optional[str] = None
    linkedin: Optional[str] = None


class CohortEntry(BaseModel):
    id: str
    legal_name: str
    display_name: str
    short_name: str
    series_token: str
    parent_group: Optional[str] = None
    domain: Optional[str] = None
    social: CohortSocial = Field(default_factory=CohortSocial)
    wayback_seeds: list[str] = Field(default_factory=list)
    rebrand_note: Optional[str] = None


class CohortFile(BaseModel):
    cohort: list[CohortEntry] = Field(default_factory=list)
    methodology: dict[str, Any] = Field(default_factory=dict)


def load_cohort_file() -> CohortFile:
    """Load and validate the full cohort YAML."""
    with open(COHORT_FILE) as file_obj:
        payload = yaml.safe_load(file_obj)
    return CohortFile.model_validate(payload)


def get_cohort_entry(bank_id: str) -> CohortEntry:
    """Return one bank entry by id."""
    cohort_file = load_cohort_file()
    for entry in cohort_file.cohort:
        if entry.id == bank_id:
            return entry
    raise KeyError(f"Bank '{bank_id}' not found in cohort.yaml")


def get_user_agent() -> str:
    """Return the configured scraper User-Agent from cohort methodology."""
    cohort_file = load_cohort_file()
    rules = cohort_file.methodology.get("scraping_rules", {})
    return rules.get(
        "user_agent",
        "BahamasOpenDataBot/1.0 (+https://bahamasopendata.com/intelligence)",
    )


def get_rate_limit_seconds() -> float:
    """Return minimum seconds between requests to the same host."""
    cohort_file = load_cohort_file()
    rules = cohort_file.methodology.get("scraping_rules", {})
    return float(rules.get("rate_limit_seconds_min", 2))
