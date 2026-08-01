# Intelligence Capture Methodology

Public transparency notes for the Bahamas Open Data | Intelligence imprint.
Grounded in the live scraper behaviour as of July 2026 (Banking Sector Issue 01).

## Scope

- **Cohort:** six banks in `ingestion/intelligence/cohort.yaml`
- **Measurement window:** 2025-10-01 → 2026-09-30 (`America/Nassau`)
- **Public drop:** 2026-10-05
- **Storage:** JSON-on-disk under `data/intelligence/` (no Postgres for Issue 01)

## Thin-data market (Bahamas)

Bahamian institutional digital footprints are uneven. Issue 01 publishes **confirmed public signals only** (today: Facebook for all six banks; Instagram / YouTube / PageSpeed where reachable). Empty cells for Ahrefs, Similarweb, Wayback density, schema.org, TikTok, and Bing are documented absences — not defects to paper over. The report and `/intelligence` UI must show `—` / `null`, never interpolated coverage.

## What we collect

| Signal | Module | Method |
|---|---|---|
| Historical followers (FB / IG / X) | `social/wayback.py` | Wayback CDX ±7 days |
| YouTube channel stats | `social/youtube.py` | YouTube Data API v3 |
| Instagram / Facebook / TikTok / X | dedicated social scrapers | Public HTML only |
| Social Blade cross-check | `social/socialblade.py` | Public HTML |
| Traffic estimate | `web/similarweb.py` | Public HTML |
| Non-branded SERP | `web/bing_serp.py` | **Skipped Issue 01** (Bing Web Search API discontinued) |
| Domain rating / backlinks | `web/ahrefs_free.py` | Ahrefs free tools (static HTML) |
| Lighthouse categories | `web/pagespeed.py` | PageSpeed Insights API |
| schema.org types | `web/structured_data.py` | Homepage JSON-LD / microdata / RDFa |

Every metric carries `SourceProvenance` (`url`, UTC `fetched_at`, `http_status`, `method`). Failures are `null` plus an entry in `CaptureResult.errors` — never inferred or interpolated.

## Known soft failures (accepted)

These are honest absences, not invented zeros:

1. **Ahrefs free tools** often ship Domain Rating / backlink counts only after client-side render. We fetch both the Website Authority Checker and Backlink Checker pages and parse static HTML; when numbers are absent we record `null` and a soft error (`metrics may be client-rendered only`). We do not run a headless browser against Ahrefs for Issue 01. Text parsers require the number immediately after the label — loose “within N characters” matching false-positived CSS class digits near the marketing SVG.
2. **schema.org detection** returns an empty type list when the homepage has no JSON-LD, microdata, or RDFa. That empty result is itself the measurement.
3. **PageSpeed `authority_score`** holds the Lighthouse *performance* score (0–100), not an SEO Domain Rating. Soft errors call this out so charts do not conflate the two.
4. **Wayback** yields `followers=null` when no snapshot exists in the ±7 day window or the archived HTML has no parseable follower string. The Oct 2025 – Jul 2026 month-midpoint backfill (`run_wayback_backfill.py`) found **zero** in-window snapshots for cohort Facebook/Instagram seeds — honest empty trajectory until denser archives or a wider window is approved.
5. **Similarweb** free endpoint returns HTTP 403 for cohort domains (Jul 2026). **Accepted Issue 01 gap** — leave ``organic_traffic_est`` as ``null``; do not invent traffic or browser-bypass the WAF. Revisit post-Issue 01 if a public source appears.
6. **Bing SERP** is unregistered for Issue 01 (API discontinued). Module kept in-tree for tests only.
7. **Fidelity** has no public marketing website (Jul 2026) — `domain: null` in cohort; web scrapers soft-skip.
8. **Bank of The Bahamas** apex `bankbahamas.com` lacks A/AAAA in some resolvers; homepage scrapers use `https://www.bankbahamas.com/` via `homepage_url(prefer_www=True)`.
9. **CIBC** (`cibcfcib.com`) had intermittent homepage/PageSpeed failures in the Jul 19 trial run — re-check on next capture.

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
| Live capture | Aug 1 → Sep 13 | Weekly `./scripts/run_intelligence_weekly_capture.sh`; daily in final two weeks |
| Wayback backfill | Aug 1 → Aug 20 (tooling ready earlier) | `run_wayback_backfill.py` — month-midpoint (day 15) dates Oct 2025 – Jul 2026 |
| Delta validation | Sep 14 → Sep 27 | Trial exports + `run_validate.py --apply` |
| Lockdown | Sep 28 | Freeze `data/intelligence/` for Issue 01 |

## How to reproduce a capture

```bash
python -m ingestion.intelligence.run_capture \
  --date 2026-08-15 \
  --scrapers wayback --scrapers youtube --scrapers similarweb \
  --scrapers instagram --scrapers facebook --scrapers tiktok \
  --scrapers twitter --scrapers socialblade \
  --scrapers ahrefs_free --scrapers pagespeed --scrapers structured_data
```

Or via the weekly wrapper (sets ``PYTHONPATH`` and uses ``-m``):

```bash
./scripts/run_intelligence_weekly_capture.sh 2026-08-01
```

Processed cohort JSON under ``data/intelligence/processed/`` is committed so
``/intelligence`` can render without a fresh scrape. Raw HTML under
``data/intelligence/raw/`` stays gitignored.

Omit `--bank` for the full cohort. Omit `--scrapers` to run every registered scraper (`bing_serp` is not registered).

## Change log

- **2026-07-19** — Scrapers landed; full-cohort `2026-08-15` run; Bing unregistered; Fidelity `domain: null`; homepage `www.` preference; Similarweb 403 accepted; Wayback backfill Oct 2025 – Jul 2026 completed (0 in-window snapshots).
- **2026-07-20** — Thin-data acceptance explicit; weekly capture script; read-only `/intelligence` snapshot API + UI scaffold.
