# BOD Intelligence — Build Architecture v0.2
**Banking Sector 2026 · Inaugural Issue**
**Revised against REPO_AUDIT.md**

This document is the build plan for the Bahamas Open Data Intelligence imprint pipeline. Hand it to Cursor / Claude Code as project context. It defines where files go, what each module promises, what the data looks like at every stage, and what the methodology gates are.

This pipeline is an **extension of `ingestion/`**, not a separate project. It reuses the existing patterns (Playwright scraping, Gemini/OpenAI normalization through `ai_normalizer.py`, the `document_metadata.json` registry pattern, repo-root PYTHONPATH imports) and adds two new domains of capture: social-platform metrics and competitive web intelligence.

### Changes from v0.1
- **Storage scope clarified:** Issue 01 ships JSON-only on disk. No new Postgres tables, no Alembic migrations. Postgres + Alembic + dashboard surfacing comes in v2.
- **Frontend and backend API paths removed from this scope.** Section 1 of v0.1 listed `frontend/src/app/intelligence/` and `backend/app/api/intelligence.py` as part of the scaffold. Those build windows open later (mid-August). Resolves Cursor's clarifying question: **Option A is correct** — scaffold only `ingestion/intelligence/` and `data/intelligence/`.
- **Logging convention specified:** Use Python `logging` (not `print()` with emoji as in existing ingestion). The elevated transparency discipline of this pipeline warrants durable, queryable observability.
- **Test discipline introduced:** Existing codebase has no automated tests. The intelligence module starts this discipline — every commit ships with tests. Tests live at `tests/intelligence/`.
- **Registry pattern aligned:** Intelligence captures register in `data/intelligence/registry.json` modeled on the existing `data/document_metadata.json` state machine.
- **Pinecone strategy clarified:** Existing index `national-pulse` (1536 dims, `text-embedding-3-small`) is reused for any future RAG embedding of report content, distinguished by `document_type: "intel_report"`. No new index in v1.

---

## 1. Repository Placement (Issue 01 scope)

Only the paths below are in scope for the v0.2 scaffold. Frontend and backend API routes for `/intelligence` are deferred to a separate spec opening mid-August.

```
bahamasopedata/                            # Note: workspace folder is bahamasopedata, not bahamasopendata
├── ingestion/
│   ├── scraper.py                         # EXISTING — govt PDF scraper
│   ├── parser.py                          # EXISTING
│   ├── ai_normalizer.py                   # EXISTING — reuse NormalizedDocument patterns
│   ├── embeddings.py                      # EXISTING — reuse for future RAG over reports
│   ├── run_pipeline.py                    # EXISTING — CLI for existing pipeline
│   │
│   └── intelligence/                      # NEW — Intelligence imprint pipeline
│       ├── __init__.py
│       ├── cohort.yaml                    # the six banks — source of truth (already drafted)
│       ├── cohort.py                      # Pydantic loader for cohort.yaml (load_cohort_file, get_cohort_entry)
│       ├── errors.py                      # CaptureError — raised on rate-limit, paywall, auth-required surfaces
│       ├── types.py                       # pydantic models for normalized data
│       ├── logging_config.py              # shared logger setup for the imprint
│       ├── methodology.md                 # public-facing transparency doc (drafted after first scraper lands)
│       │
│       ├── social/
│       │   ├── __init__.py
│       │   ├── wayback.py                 # historical follower counts via archive.org
│       │   ├── facebook.py                # public page scraping (Playwright)
│       │   ├── instagram.py               # public business profile scraping
│       │   ├── youtube.py                 # YouTube Data API v3 (free quota)
│       │   ├── tiktok.py                  # Playwright on public profile pages
│       │   ├── twitter.py                 # mostly Wayback for history
│       │   └── socialblade.py             # cross-reference for TikTok / YouTube historicals
│       │
│       ├── web/
│       │   ├── __init__.py
│       │   ├── similarweb.py              # free tier — traffic, demographics, top keywords
│       │   ├── ahrefs_free.py             # backlink checker free tool
│       │   ├── bing_serp.py               # Bing Web Search API — non-branded queries
│       │   ├── pagespeed.py               # Google PageSpeed Insights API (free)
│       │   └── structured_data.py         # schema.org markup detection
│       │
│       ├── capture/
│       │   ├── __init__.py
│       │   ├── orchestrator.py            # runs the full capture for a given date
│       │   ├── delta_validator.py         # compares scraped vs Rival IQ / SEMrush trial pulls
│       │   └── registry.py                # read/write data/intelligence/registry.json
│       │
│       └── run_capture.py                 # CLI entry: `python ingestion/intelligence/run_capture.py --date 2026-08-15`
│
├── data/
│   └── intelligence/                      # NEW
│       ├── raw/                           # raw HTML / JSON snapshots, by capture date and bank
│       ├── processed/                     # normalized per-bank metrics by capture date
│       ├── exports/                       # publication-ready CSV / JSON
│       └── registry.json                  # capture state machine (mirrors document_metadata.json pattern)
│
└── tests/                                 # NEW directory at repo root — establishes test discipline
    └── intelligence/
        ├── __init__.py
        ├── test_types.py
        ├── test_registry.py
        ├── fixtures/                      # static HTML/JSON samples for scraper tests
        └── test_<scraper>.py              # one per scraper module
```

**Out of scope for the v0.2 scaffold (deferred to later specs):**
- `backend/app/api/intelligence.py` — built once captures are flowing and we know what to expose
- `frontend/src/app/intelligence/` — built mid-August once data shape is locked
- Postgres tables, Alembic migrations — v2 after Issue 01 ships
- `methodology.md` — drafted after the first scraper produces real data so the language is grounded

---

## 2. Module Contracts

Every scraper module exports a single async function with this signature:

```python
async def capture(
    bank_id: str,                      # e.g. "rbc_bahamas"
    cohort_entry: CohortEntry,         # the parsed YAML entry
    capture_date: date,                # the date this snapshot represents
) -> CaptureResult:
    """
    Returns a CaptureResult containing:
      - normalized metrics for this bank from this platform/source on this date
      - the raw source artifacts (HTML, JSON) for audit
      - source URL and HTTP status for every datum
      - timestamps in UTC
    Raises CaptureError on rate-limit, paywall, or auth-required surfaces —
    NEVER silently substitutes synthetic data.
    """
```

The `CaptureResult` is the lingua franca of the pipeline. Every downstream consumer operates on this shape.

---

## 3. Data Shapes — `types.py`

```python
from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field

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
    fetched_at: datetime              # UTC; timezone-aware required
    http_status: int
    method: str                       # "scrape" | "api" | "wayback" | "socialblade"
    archive_url: Optional[HttpUrl] = None  # Wayback snapshot if applicable

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
    posted_at: datetime               # UTC
    format: str                       # "photo" | "video" | "reel" | "carousel" | "link" | "text"
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
    raw_artifacts: dict[str, str] = Field(default_factory=dict)  # logical name → path under data/intelligence/raw/
    errors: list[str] = Field(default_factory=list)              # non-fatal failures, logged not raised
    attempted_platforms: list[Platform] = Field(default_factory=list)  # platforms attempted regardless of measurement success; used to derive platforms_failed
```

All `Optional` fields default to `None` — the distinction between "measured zero" and "couldn't measure" must survive into the published dataset.

---

## 4. Registry — `data/intelligence/registry.json`

Mirrors the existing `data/document_metadata.json` pattern. Each capture is a row tracked through a state machine.

```json
{
  "captures": [
    {
      "capture_id": "rbc_bahamas_2026-08-15",
      "bank_id": "rbc_bahamas",
      "capture_date": "2026-08-15",
      "platforms_captured": ["facebook", "instagram", "youtube", "website"],
      "platforms_failed": ["tiktok"],
      "raw_artifact_paths": {
        "facebook_profile": "data/intelligence/raw/2026-08-15/rbc_bahamas/facebook_profile.html",
        "instagram_profile": "data/intelligence/raw/2026-08-15/rbc_bahamas/instagram_profile.json"
      },
      "processed_path": "data/intelligence/processed/2026-08-15/rbc_bahamas.json",
      "scrape_status": "complete",
      "validation_status": "pending",
      "validated_at": null,
      "delta_variance_pct": null
    }
  ]
}
```

`capture/registry.py` exposes `load_registry()`, `save_registry()`, `mark_capture()`, `mark_validation()` — same style as `parser.load_metadata` / `save_metadata`.

---

## 5. Methodology Gates

Non-negotiables baked into scrapers, not just documented:

| Gate | Enforcement |
|---|---|
| Publicly visible content only | No scraper may use authenticated cookies, OAuth tokens, or session storage |
| Rate-limited politeness | Minimum 2 seconds between requests to the same host; exponential backoff on 429/503 |
| Honest User-Agent | `BahamasOpenDataBot/1.0 (+https://bahamasopendata.com/intelligence)` |
| `robots.txt` respected | Where it exists, we honour it; deviations require methodology.md disclosure |
| Provenance per datum | Every metric carries source URL, fetched-at timestamp, HTTP status — no metric without provenance enters the dataset |
| Two-year raw retention | Raw HTML / JSON snapshots stored two years for audit |
| No synthetic substitution | If capture fails, metric is `None` — never inferred, never interpolated |
| No mock fallback at API layer | When `/api/v1/intelligence/*` routes ship later, they raise HTTPException on data unavailability — they do NOT mock-respond the way `/ask` does |

---

## 6. Conventions to Follow (from REPO_AUDIT)

Adopting these from the existing codebase, not reinventing:

1. **PYTHONPATH = repo root.** Intelligence modules import `from backend.app.core.config import settings` and `from ingestion.intelligence.types import CaptureResult`. Match the import style of `run_pipeline.py`.
2. **Paths via constants.** Reuse `REPO_ROOT` and `DATA_DIR` from `backend.app.services.document_ingestion` rather than recomputing `Path(__file__).parent.parent / "data"`. Add `INTELLIGENCE_DATA_DIR = DATA_DIR / "intelligence"` as a sibling constant.
3. **Pydantic at every boundary.** All structured outputs are `BaseModel` subclasses. `None` for unknown, not zero.
4. **httpx for simple HTTP, Playwright async for scraping.** Match `ingestion/scraper.py` patterns.
5. **No retry magic.** `tenacity` is in requirements but unused — do not assume retries exist. Implement explicit backoff in `capture/orchestrator.py` for the rate-limit gate.
6. **Embeddings reuse.** If we later embed report text for the RAG `/ask` endpoint, use the existing `national-pulse` Pinecone index with `document_type: "intel_report"` discriminator. Call into `ingestion/embeddings.py` via its existing helpers and apply `sanitize_metadata_string()` to all metadata.
7. **Logging via Python `logging`**, not `print()`. Define logger in `ingestion/intelligence/logging_config.py` with handlers writing to both stdout and `data/intelligence/logs/capture.log`. Use semantic levels (`info` for run lifecycle, `warning` for soft failures the dataset survives, `error` for hard failures that abort a capture).
8. **Registry platform attribution.** `platforms_captured` and `platforms_failed` are `Platform.value` strings (e.g. `"facebook"`, `"website"`), not scraper dispatch keys. The orchestrator derives them from `CaptureResult.attempted_platforms` and the union of platforms appearing in merged `social_metrics` and `web_metrics`.

---

## 7. Capture Cadence

| Phase | Window | What runs |
|---|---|---|
| Setup | Now → Jun 30 | cohort.yaml verification, scraper skeletons, types lock-in, tests passing |
| Pipeline build | Jul | All scraper modules implemented and fixture-tested |
| Live capture | Aug 1 → Sep 13 | `run_capture.py` runs weekly via cron; daily on the final two weeks |
| Wayback backfill | Aug 1 → Aug 20 | One-time historical pull for Oct 2025 – Jul 2026 follower trajectories |
| Delta validation | Sep 14 → Sep 27 | Rival IQ 14-day + SEMrush 7-day trials active; comparison reports generated |
| Lockdown | Sep 28 | Dataset frozen for Issue 01 publication |
| Frontend / backend | Sep 14 → Oct 2 | `/intelligence` route built against locked data shapes |
| Press pre-brief | Sep 28 → Oct 2 | Embargoed copies to Tribune / Guardian / Eyewitness / EFTV |
| **Public release** | **Oct 5, 2026** | Report + dataset + open-source code, single drop |

---

## 8. Build Order for Cursor

1. **Scaffold commit** — `ingestion/intelligence/` Python tree, `data/intelligence/` directories with `.gitkeep`, `tests/intelligence/` directory. No logic yet.
2. **Cohort verification commit** — Kenneth manually fills `# verify` lines in cohort.yaml with actual social handles for the six banks. Commit message: `cohort: verify social handles for 2026 banking issue`.
3. **types.py commit** — Implement pydantic models per section 3. Add `tests/intelligence/test_types.py` with passing tests for valid construction, negative rejection, probability bounds, timezone-aware datetime enforcement.
4. **registry.py commit** — Implement `capture/registry.py` per section 4, with tests in `tests/intelligence/test_registry.py`.
5. **First reference scraper** — `social/wayback.py`. Proves the contract end-to-end before replicating across nine other modules. Tests use fixture HTML stored in `tests/intelligence/fixtures/`.
6. **Orchestrator + run_capture.py** — Pipeline runs end-to-end on one bank, one platform.
7. **Remaining scrapers** — In order: `youtube.py` (free API, easiest), `similarweb.py`, `instagram.py`, `facebook.py`, `tiktok.py`, `bing_serp.py`, then the rest.
8. **delta_validator.py** — Last code module.
9. **methodology.md** — Drafted after first real data lands so language is grounded in actual capture behaviour.

Each commit ships with tests. Each scraper has a fixture-based test pinning expected output shape so Cursor doesn't drift contracts mid-build.

---

## 9. Open Decisions Before Build

1. **Naming policy** for any future intelligence-related namespaces (Postgres tables in v2, log file names, Pinecone metadata `document_type` value). Current default in this doc: `bod_intel_*` aligned to public brand. Alternative: `np_intel_*` aligned to internal codename `nationalpulse` / `national-pulse`. Mixed is also viable.
2. **Final per-institution colour assignment** for `--intel-series-1` through `--intel-series-6` (locks the colour each bank carries through all charts and future annual issues).
3. **Bahamian number formatting localisation** (BSD currency, comma vs period as decimal separator).

---

*Document owner: KGC / Bahamas Open Data*
*v0.2 — drafted May 2026, revised against REPO_AUDIT.md — for Banking Sector inaugural issue, October 5, 2026 release*
