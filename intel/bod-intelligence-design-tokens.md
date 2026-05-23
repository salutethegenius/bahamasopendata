# Bahamas Open Data | Intelligence
## Design Tokens v0.2 — Inaugural Issue: Banking Sector 2026

**Status:** Pre-build scoping draft, revised against REPO_AUDIT.md
**Intended use:** Hand-off spec for the `/intelligence` route on bahamasopendata.com and the downloadable PDF report
**Parent platform:** bahamasopendata.com (unchanged — bright civic register, existing `globals.css` tokens)
**This document scopes:** The Intelligence imprint only — a darker, analyst-grade sub-brand of BOD

### Changes from v0.1
- **Typography corrected to Sora + DM Mono** (matches parent platform via `--font-sora` and `--font-dm-mono` already loaded in `frontend/src/app/globals.css`). v0.1 specified Geist Sans/Mono in error.
- **Implementation pattern updated for Tailwind v4 + `@theme inline`** (the platform does not use `tailwind.config.js`; tokens live in `globals.css`).
- **Scoping mechanism specified:** Intelligence palette activated via `[data-imprint="intelligence"]` attribute selector on the route segment, so parent dashboard tokens are not overwritten.

---

## 1. Brand Positioning

Bahamas Open Data | Intelligence is the analytical publishing imprint of the BOD civic data platform. Where the parent platform answers *"where does the public money go?"*, the Intelligence imprint answers *"how is each sector of the Bahamian economy actually performing?"* — through annual sector-by-sector competitive intelligence reports.

The visual register sits two clicks more institutional than the parent: darker surfaces, denser data displays, monospace numerics. Reads as if it came off an analyst's terminal rather than a citizen dashboard. Parent brand connection is preserved through **shared typography (Sora + DM Mono)** and accent colour (turquoise) — the two products are clearly siblings, not strangers.

---

## 2. Colour Tokens

### Core palette

| Token | Hex | Role |
|---|---|---|
| `--intel-navy-900` | `#08152B` | Primary surface / page background |
| `--intel-navy-800` | `#0F2140` | Card / panel background |
| `--intel-navy-700` | `#172E55` | Elevated card / hover state |
| `--intel-graphite-600` | `#1E2A3E` | Data surface (chart background) |
| `--intel-border` | `#243352` | Hairlines, dividers, chart grid |
| `--intel-turquoise-500` | `#00CED1` | Accent — **parent BOD link** (same hex as `--turquoise`) |
| `--intel-turquoise-300` | `#5EE6E8` | Accent hover / highlight |
| `--intel-yellow-400` | `#FCD116` | Rare highlight — **parent BOD link**, use sparingly |

### Text

| Token | Hex | Role |
|---|---|---|
| `--intel-text-primary` | `#F8FAFC` | Headings, body |
| `--intel-text-secondary` | `#94A3B8` | Captions, axis labels, secondary metadata |
| `--intel-text-tertiary` | `#64748B` | Disabled, footnotes |
| `--intel-text-accent` | `#00CED1` | Linked text, callout numerals |

### Data / semantic

| Token | Hex | Role |
|---|---|---|
| `--intel-data-positive` | `#10B981` | Growth, gain, favourable change |
| `--intel-data-negative` | `#F43F5E` | Decline, loss, unfavourable change |
| `--intel-data-neutral` | `#94A3B8` | Unchanged, baseline, competitor average |
| `--intel-data-warning` | `#F59E0B` | Anomaly, flag, audit note |

### Chart series palette (categorical, 6-bank cohort)

WCAG AA contrast on `--intel-graphite-600`. Order is the *legibility ranking*; final per-institution assignment is locked at cohort sign-off (currently provisional in `cohort.yaml` via `series_token`).

| Token | Hex | Provisional bank |
|---|---|---|
| `--intel-series-1` | `#00CED1` | RBC Royal Bank Bahamas |
| `--intel-series-2` | `#FCD116` | Scotiabank Bahamas |
| `--intel-series-3` | `#A78BFA` | Commonwealth Bank |
| `--intel-series-4` | `#FB923C` | Fidelity Bank Bahamas |
| `--intel-series-5` | `#F472B6` | CIBC Caribbean |
| `--intel-series-6` | `#34D399` | Bank of The Bahamas |

---

## 3. Typography

### Families (UNCHANGED from parent platform)

- **Sora** (display and body) — already loaded as `--font-sora` in parent platform
- **DM Mono** (data labels, metrics, axis ticks, table cells, captions) — already loaded as `--font-dm-mono`

These are the same families the parent dashboard uses. The Intelligence imprint differentiates through weight, scale, and the systematic application of monospace for numerics — not through different fonts. Visual coherence between parent and sub-imprint pages is non-negotiable.

The mono treatment is the heaviest carrier of the "analyst's terminal" register. Switching any data element to sans collapses the visual difference between the two products.

### Scale (desktop baseline; scales 0.875× on mobile)

| Token | Size / Line | Family / Weight | Use |
|---|---|---|---|
| `--intel-type-display` | 56 / 64 | Sora 700 | Report title, section openers |
| `--intel-type-h1` | 40 / 48 | Sora 700 | Page title |
| `--intel-type-h2` | 28 / 36 | Sora 600 | Section heading |
| `--intel-type-h3` | 20 / 28 | Sora 600 | Chart title, callout heading |
| `--intel-type-body-lg` | 18 / 28 | Sora 400 | Lead paragraph, key takeaway |
| `--intel-type-body` | 15 / 24 | Sora 400 | Body copy |
| `--intel-type-eyebrow` | 11 / 14 | DM Mono 500, uppercase, +1.5 tracking | Section tag |
| `--intel-type-metric-hero` | 48 / 56 | DM Mono 500, tabular-nums | Hero KPI numerals |
| `--intel-type-metric` | 24 / 32 | DM Mono 500, tabular-nums | Card metric numerals |
| `--intel-type-label` | 13 / 18 | DM Mono 400 | Axis labels, chart legends |
| `--intel-type-caption` | 12 / 16 | DM Mono 400 | Footnotes, source attribution |

Apply `font-feature-settings: "tnum" 1` on DM Mono for all numeric contexts. Tabular figures are mandatory in tables and charts.

---

## 4. Chart Styling

Same rules as v0.1 — chart background `--intel-graphite-600`, never black; gridlines `--intel-border` at 40% opacity; tick labels in DM Mono 13/18; bar corners square (1px max); line weight 2px standard, 3px for emphasis; annotations side-pulled with leader lines, never overlaid.

Number formatting: comma thousands separator, 1 decimal for %, 0 for raw counts, K/M/B compaction above 100K. Always DM Mono, always tabular figures.

Sparklines: 64×16, single colour from cohort palette, no axes, final-point marker only, source data adjacent in mono.

---

## 5. Implementation Pattern (Tailwind v4)

The platform's `frontend/src/app/globals.css` defines tokens as CSS variables on `:root` and exposes them to Tailwind via `@theme inline`. The Intelligence imprint extends this pattern, scoped to the `/intelligence` route segment.

### globals.css additions

```css
/* ============================================================
   Intelligence imprint tokens — scoped to /intelligence routes
   ============================================================ */

[data-imprint="intelligence"] {
  /* Surfaces */
  --intel-navy-900: #08152B;
  --intel-navy-800: #0F2140;
  --intel-navy-700: #172E55;
  --intel-graphite-600: #1E2A3E;
  --intel-border: #243352;

  /* Accent — same hex as parent --turquoise, namespaced for clarity */
  --intel-turquoise-500: #00CED1;
  --intel-turquoise-300: #5EE6E8;
  --intel-yellow-400: #FCD116;

  /* Text */
  --intel-text-primary: #F8FAFC;
  --intel-text-secondary: #94A3B8;
  --intel-text-tertiary: #64748B;
  --intel-text-accent: #00CED1;

  /* Data / semantic */
  --intel-data-positive: #10B981;
  --intel-data-negative: #F43F5E;
  --intel-data-neutral: #94A3B8;
  --intel-data-warning: #F59E0B;

  /* Chart series */
  --intel-series-1: #00CED1;
  --intel-series-2: #FCD116;
  --intel-series-3: #A78BFA;
  --intel-series-4: #FB923C;
  --intel-series-5: #F472B6;
  --intel-series-6: #34D399;

  /* Override the page background for the whole imprint */
  background-color: var(--intel-navy-900);
  color: var(--intel-text-primary);
}

@theme inline {
  /* Existing parent tokens (unchanged) */
  /* ... --color-turquoise, --color-yellow, etc ... */

  /* Intelligence additions — accessible via Tailwind utilities */
  --color-intel-navy-900: var(--intel-navy-900);
  --color-intel-navy-800: var(--intel-navy-800);
  --color-intel-navy-700: var(--intel-navy-700);
  --color-intel-graphite-600: var(--intel-graphite-600);
  --color-intel-border: var(--intel-border);
  --color-intel-turquoise-500: var(--intel-turquoise-500);
  --color-intel-turquoise-300: var(--intel-turquoise-300);
  --color-intel-yellow-400: var(--intel-yellow-400);
  --color-intel-text-primary: var(--intel-text-primary);
  --color-intel-text-secondary: var(--intel-text-secondary);
  --color-intel-text-tertiary: var(--intel-text-tertiary);
  --color-intel-text-accent: var(--intel-text-accent);
  --color-intel-data-positive: var(--intel-data-positive);
  --color-intel-data-negative: var(--intel-data-negative);
  --color-intel-data-neutral: var(--intel-data-neutral);
  --color-intel-data-warning: var(--intel-data-warning);
  --color-intel-series-1: var(--intel-series-1);
  --color-intel-series-2: var(--intel-series-2);
  --color-intel-series-3: var(--intel-series-3);
  --color-intel-series-4: var(--intel-series-4);
  --color-intel-series-5: var(--intel-series-5);
  --color-intel-series-6: var(--intel-series-6);
}
```

### Route-level activation

The `/intelligence` route segment (Next.js App Router at `frontend/src/app/intelligence/layout.tsx` once it exists) wraps its children in a container with the data attribute:

```tsx
export default function IntelligenceLayout({ children }: { children: React.ReactNode }) {
  return (
    <div data-imprint="intelligence" className="min-h-screen">
      {children}
    </div>
  );
}
```

Any page or component beneath this layout inherits the Intelligence palette. Pages outside `/intelligence/*` are unaffected.

### Usage in components

```tsx
// Tailwind utilities use the namespaced tokens
<div className="bg-intel-navy-800 border border-intel-border text-intel-text-primary">
  <span className="font-mono text-intel-text-accent">+1.66%</span>
</div>
```

---

## 6. Masthead Reference

Page-1 lockup follows the Edelman Trust Barometer convention — publisher prominent, issue specifics secondary.

```
SECTION TAG           --intel-type-eyebrow, --intel-text-accent
SECTION 01 / BENCHMARKING

PUBLISHER             --intel-type-display, --intel-text-primary
Bahamas Open Data
                      --intel-type-h2, --intel-turquoise-500
Intelligence

ISSUE                 --intel-type-h3, --intel-text-secondary
Digital Intelligence Annual Report
2026 · Banking Sector

MEASUREMENT WINDOW    --intel-type-label, --intel-text-secondary
October 1, 2025 — September 30, 2026
```

Vertical hairline (`--intel-border`, 1px) separates publisher block from a right-side institutional logo strip showing the six tracked banks.

---

## 7. Closing Colophon

Single line, `--intel-type-caption`, `--intel-text-tertiary`:

> *Bahamas Open Data is built by The Kemis Group of Companies. Explore the platform at bahamasopendata.com. Other KGC products: GrandBridge · LawBey · KemisPay · PileIt.*

No CTA. No QR code. Reads as a publisher's imprint footer.

---

## 8. Implementation Notes

- Tokens live in `frontend/src/app/globals.css`, scoped via `[data-imprint="intelligence"]`. Do not create a separate stylesheet — the parent platform's tokens stay co-located, and Tailwind v4's `@theme inline` does not split cleanly across multiple files.
- DM Mono numeric features (`tnum`) must be enabled in the `font-feature-settings` declaration on any element using DM Mono in a tabular context. Add a utility class `.font-mono-tabular` if multiple components need it.
- PDF export: Sora and DM Mono ship under the SIL OFL, safe to embed.
- Dark-only by design — no light-mode variant for the Intelligence imprint in v0.1.

---

## 9. Open Questions Before Build

1. Final per-institution assignment of `--intel-series-1` through `--intel-series-6` to the six banks (locks the colour each institution carries through all charts and across future annual issues)
2. Whether to localise number formatting to Bahamian conventions (BSD currency symbol placement)
3. Confirmation that no light-mode variant is needed for v0.1

---

*Document owner: KGC / Bahamas Open Data*
*Version 0.2 — drafted May 2026, revised against REPO_AUDIT.md — for Banking Sector inaugural issue, October 5, 2026 release*
