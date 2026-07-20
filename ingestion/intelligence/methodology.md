# Intelligence Capture Methodology

Public transparency notes for the Bahamas Open Data | Intelligence imprint.
Grounded in the live scraper behaviour as of July 2026 (Banking Sector Issue 01).

## Scope

- **Cohort:** six banks in `ingestion/intelligence/cohort.yaml`
- **Measurement window:** 2025-10-01 → 2026-09-30 (`America/Nassau`)
- **Public drop:** 2026-10-05
- **Storage:** JSON-on-disk under `data/intelligence/` (no Postgres for Issue 01)

## What we collect

| Signal | Module | Method |
|---|---|---|
| Historical followers (FB / IG / X) | `social/wayback.py` | Wayback CDX ±7 days |
| YouTube channel stats | `social/youtube.py` | YouTube Data API v3 |
| Instagram / Facebook / TikTok / X | dedicated social scrapers | Public HTML only |
| Social Blade cross-check | `social/socialblade.py` | Public HTML |
| Traffic estimate | `web/similarweb.py` | Public HTML |
| Non-branded SERP | `web/bing_serp.py` | Bing Web Search API |
| Domain rating / backlinks | `web/ahrefs_free.py` | Ahrefs free tools (static HTML) |
| Lighthouse categories | `web/pagespeed.py` | PageSpeed Insights API |
| schema.org types | `web/structured_data.py` | Homepage JSON-LD / microdata / RDFa |

Every metric carries `SourceProvenance` (`url`, UTC `fetched_at`, `http_status`, `method`). Failures are `null` plus an entry in `CaptureResult.errors` — never inferred or interpolated.

## Known soft failures (accepted)

These are honest absences, not invented zeros:

1. **Ahrefs free tools** often ship Domain Rating / backlink counts only after client-side render. We fetch both the Website Authority Checker and Backlink Checker pages and parse static HTML; when numbers are absent we record `null` and a soft error (`metrics may be client-rendered only`). We do not run a headless browser against Ahrefs for Issue 01. Text parsers require the number immediately after the label — loose “within N characters” matching false-positived CSS class digits near the marketing SVG.
2. **schema.org detection** returns an empty type list when the homepage has no JSON-LD, microdata, or RDFa. That empty result is itself the measurement.
3. **PageSpeed `authority_score`** holds the Lighthouse *performance* score (0–100), not an SEO Domain Rating. Soft errors call this out so charts do not conflate the two.
4. **Wayback** yields `followers=null` when no snapshot exists in the ±7 day window or the archived HTML has no parseable follower string.
5. **Similarweb** free endpoint currently returns HTTP 403 for cohort domains (Jul 2026) — catastrophic for that scraper only; other scrapers continue.
6. **Bing SERP** requires `BING_SEARCH_API_KEY`; unset key fails that scraper only.
7. **Some bank domains** fail PageSpeed / homepage fetch (`fidelitybahamas.com` Lighthouse document error; `cibcfcib.com` connection failures; `bankbahamas.com` DNS NXDOMAIN as configured). Cohort domain verification is still open for those three.

## Rate limits & identity

- User-Agent: `BahamasOpenDataBot/1.0 (+https://bahamasopendata.com/intelligence)` (from cohort config)
- ≥2 seconds between requests to the same host where scrapers enforce politeness
- Exponential / hard fail on HTTP 429/503 — capture continues for other scrapers; failed scraper raises `CaptureError` and is logged
- `robots.txt` honoured where checked; deviations (if any) will be listed here before lockdown

## Validation

From 2026-09-14 we cross-check scraped values against Rival IQ (through 2026-09-27) and SEMrush (2026-09-21–27) trial exports via `capture/delta_validator.py`.

- Relative variance = `|scraped − reference| / |reference| × 100`
- Fields missing on either side are skipped (not failed)
- Any comparable field **> 5%** → `validation_status: failed` and manual review before Sep 28 lockdown
- CLI: `python ingestion/intelligence/run_validate.py --trial path.json [--apply]`

## Cadence

| Phase | Window | Action |
|---|---|---|
| Live capture | Aug 1 → Sep 13 | Weekly `run_capture.py`; daily in final two weeks |
| Wayback backfill | Aug 1 → Aug 20 | Historical follower trajectories Oct 2025 – Jul 2026 |
| Delta validation | Sep 14 → Sep 27 | Trial exports + `run_validate.py --apply` |
| Lockdown | Sep 28 | Freeze `data/intelligence/` for Issue 01 |

## How to reproduce a capture

```bash
backend/.venv/bin/python ingestion/intelligence/run_capture.py \
  --date 2026-08-15 \
  --scrapers wayback --scrapers youtube --scrapers similarweb \
  --scrapers instagram --scrapers facebook --scrapers tiktok \
  --scrapers bing_serp --scrapers twitter --scrapers socialblade \
  --scrapers ahrefs_free --scrapers pagespeed --scrapers structured_data
```

Omit `--bank` for the full cohort. Omit `--scrapers` to run every registered scraper.

## Change log

- **2026-07-19** — Initial draft after all twelve scrapers landed; full-cohort `2026-08-15` run completed (`complete=6`); Ahrefs DR false-positive fix; Similarweb 403 / missing Bing key / domain DNS issues documented.
