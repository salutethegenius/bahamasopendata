'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { formatCurrency } from '@/lib/format';
import type { Ministry } from '@/types';
import { initialBudgetSummary, initialMinistries } from '@/data/budget';
import V2AskBudgetPanel from '@/components/v2/V2AskBudgetPanel';
import styles from './v2.module.css';

type TickerItem = {
  text: string;
  source: string;
  url?: string;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

const TICKER_ITEMS: TickerItem[] = [
  {
    text: 'Historic first: Bahamas achieves $75.5M budget surplus — first since independence in 1973',
    source: 'Budget FY2025/26',
  },
  {
    text: 'Govt $357M claim against GBPA dismissed in full by Arbitration Tribunal',
    url: 'https://www.tribune242.com/news/2026/mar/03/govts-357m-claim-against-gbpa-dismissed-in-full/',
    source: 'Tribune242',
  },
  {
    text: 'National debt falls to 68.9% of GDP, down from 88.7% — significant fiscal improvement',
    source: 'Budget FY2025/26',
  },
  {
    text: 'PM opens $2.1M Mayaguana airport tied to 2,000-job seaport project',
    url: 'https://www.tribune242.com/news/2026/mar/02/pm-opens-21m-mayaguana-airport-tied-to-2000-job-seaport-project/',
    source: 'Tribune242',
  },
  {
    text: 'Education allocation FY2025/26: $493M · Health: $355M · National Security: $197M',
    source: 'Estimates of Expenditure',
  },
  {
    text: 'Total national debt: $11.4B · Debt service remains largest single budget line item',
    source: 'Budget FY2025/26',
  },
];

const EXPLORE_CARDS = [
  {
    icon: '🏥',
    label: 'Health Data',
    title: 'Health & Wellness',
    desc: 'Hospital allocations, clinic funding, public health spending, and health outcomes data across the islands.',
    stat: '$355M',
    statLabel: 'Health allocation FY2025/26',
    href: '/health',
  },
  {
    icon: '💰',
    label: 'Income Data',
    title: 'Income & Cost of Living',
    desc: 'Middle class income benchmarks, cost of living indices, and economic pressure indicators for Bahamian households.',
    stat: '$10,200',
    statLabel: 'Middle class monthly income',
    href: '/income',
  },
  {
    icon: '📊',
    label: 'Public Polls',
    title: 'What Bahamians Think',
    desc: 'Real-time polling on national priorities, policy opinions, and public satisfaction with government services.',
    stat: '3',
    statLabel: 'Active polls right now',
    href: '/polls',
  },
  {
    icon: '🗞️',
    label: 'News',
    title: 'Budget & Economic News',
    desc: 'Official budget updates, economic announcements, and government financial decisions — sourced and tracked.',
    stat: '2024/25',
    statLabel: 'Latest budget communication',
    href: '/news',
  },
  {
    icon: '🔥',
    label: 'Hot Topics',
    title: 'Accountability Reports',
    desc: 'Deep-dive reports on specific issues in Bahamian public finance — GBPA, national debt, surplus trajectory.',
    stat: '3',
    statLabel: 'Featured reports',
    href: '/hot',
  },
  {
    icon: '🏛️',
    label: 'Ministries',
    title: 'Ministry Overview',
    desc: 'See which ministries receive the most funding, track year-on-year changes, and understand allocation logic.',
    stat: '10',
    statLabel: 'Ministries tracked',
    href: '/ministries',
  },
];

const STORIES = [
  {
    tag: 'Feature · The Surplus',
    title: 'The first surplus since 1973 — what it means for every Bahamian',
    desc: "For 52 consecutive years, the Bahamas spent more than it earned. The $75.5M surplus isn't just a number — it's a turning point in the nation's fiscal history. Here's what changed, and what comes next.",
    source: 'Budget Communication 2025/26, pp. 8–15 · RAG retrieved',
  },
  {
    tag: 'Analysis · National Debt',
    title: 'Understanding the $11.4 billion debt — and why it\'s finally falling',
    desc: 'The national debt is real and significant. But debt-to-GDP falling from 88.7% to 68.9% in one year tells a story of structural improvement. What drove the accumulation, and what\'s the path out.',
    source: 'Debt Management Report 2025/26 · RAG retrieved',
  },
  {
    tag: 'Civic · Your Money',
    title: "Which ministry gets the most — and whether it's working",
    desc: 'Education gets $493M. Health gets $355M. Debt service gets more than both. A plain-language breakdown of who gets what, why allocations changed, and what you should be watching.',
    source: 'Estimates of Expenditure 2025/26 · RAG retrieved',
  },
];

const TIMELINE_YEARS = [
  1973, 1980, 1990, 2000, 2010, 2020, 2026,
] as const;

const MINISTRY_INSIGHTS: Record<string, string> = {
  health:
    'Includes storm preparedness and public health resilience investments across Family Islands.',
  finance:
    'Elevated by debt service obligations — the largest structural cost in the national budget.',
  education:
    'Allocation up from the prior year, with primary school infrastructure a key driver.',
  police:
    'Supports national security and policing capacity across the archipelago.',
};

const formatBillions = (value: number | null | undefined) => {
  if (!value || !Number.isFinite(value)) return '—';
  const billions = value / 1_000_000_000;
  return `$${billions.toFixed(1)}B`;
};

const formatMillionsWhole = (value: number | null | undefined) => {
  if (!value || !Number.isFinite(value)) return '—';
  const millions = Math.round(value / 1_000_000);
  return `$${millions}M`;
};

export default function V2HomePage() {
  const [navScrolled, setNavScrolled] = useState(false);
  const [shareExpanded, setShareExpanded] = useState(false);
  const [budgetSummary, setBudgetSummary] = useState(initialBudgetSummary);
  const [ministries, setMinistries] = useState<Ministry[]>(initialMinistries);

  useEffect(() => {
    const onScroll = () => {
      setNavScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [budgetRes, ministriesRes] = await Promise.allSettled([
          fetch(`${API_BASE}/budget/summary`),
          fetch(`${API_BASE}/ministries`),
        ]);

        if (budgetRes.status === 'fulfilled' && budgetRes.value.ok) {
          const json = await budgetRes.value.json();
          setBudgetSummary((prev) => ({
            ...prev,
            ...json,
          }));
        }

        if (ministriesRes.status === 'fulfilled' && ministriesRes.value.ok) {
          const json = await ministriesRes.value.json();
          if (Array.isArray(json)) {
            setMinistries(json);
          }
        }
      } catch (err) {
        console.error('Failed to load v2 budget data', err);
      }
    };

    fetchData();
  }, []);

  const topMinistries = ministries
    .slice()
    .sort((a, b) => b.allocation - a.allocation)
    .slice(0, 6);

  const maxAllocation = topMinistries.reduce(
    (max, m) => (m.allocation > max ? m.allocation : max),
    0,
  );

  const getTrend = (m: Ministry): 'over' | 'under' | 'on' => {
    if (m.change_percent > 7) return 'over';
    if (m.change_percent < 2) return 'under';
    return 'on';
  };

  return (
    <div className={styles.pageRoot}>
      {/* Ticker */}
      <div className={styles['ticker-bar']}>
        <div className={styles['ticker-label']}>🇧🇸 Bahamas</div>
        <div className={styles['ticker-scroll']}>
          {[...Array(2)].map((_, loopIndex) =>
            TICKER_ITEMS.map((item, idx) => (
              <span
                key={`${loopIndex}-${idx}`}
                className={styles['ticker-item']}
              >
                <span className={styles['t-dot']} />
                {item.url ? (
                  <a href={item.url} target="_blank" rel="noopener noreferrer">
                    {item.text}
                  </a>
                ) : (
                  <span>{item.text}</span>
                )}
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 8,
                    color: 'rgba(255,255,255,0.18)',
                    letterSpacing: '0.1em',
                    marginLeft: -8,
                  }}
                >
                  {item.source}
                </span>
              </span>
            )),
          )}
        </div>
      </div>

      {/* Nav */}
      <nav
        className={`${styles.nav} ${navScrolled ? styles.navScrolled : ''}`}
      >
        <Link href="/" className={styles['nav-logo']}>
          {/* Keep the static mark SVG for now */}
          <span className={styles['nav-mark']}>
            Bahamas
            <em>OpenData</em>
          </span>
        </Link>
        <ul className={styles['nav-links']}>
          <li>
            <a href="#ministries" className={styles['nav-link']}>
              Budget
            </a>
          </li>
          <li>
            <Link href="/health" className={styles['nav-link']}>
              Health
            </Link>
          </li>
          <li>
            <Link href="/income" className={styles['nav-link']}>
              Income
            </Link>
          </li>
          <li>
            <Link href="/polls" className={styles['nav-link']}>
              Polls
            </Link>
          </li>
          <li>
            <div className={styles['source-pill']}>
              <div className={styles['source-pulse']} />
              <span>12 official docs · FY2025/26</span>
            </div>
          </li>
          <li>
            <Link href="/export" className={styles['btn-export']}>
              Export Data
            </Link>
          </li>
        </ul>
      </nav>

      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles['hero-inner']}>
          <div className={styles['hero-eyebrow']}>
            Fiscal Year 2025/26 · Official Budget Documents
          </div>
          <h1 className={styles['hero-headline']}>
            Your government spent
            <br />
            <em>{formatBillions(budgetSummary.total_expenditure)}</em> this year.
          </h1>
          <p className={styles['hero-sub']}>
            Real-time insights into the Bahamas national budget — sourced from
            official Parliament documents, processed by RAG, verified against
            primary records. Every number traceable.
          </p>

          {/* Stat pillars */}
          <div className={styles['hero-stats']}>
            <div className={styles['stat-card']}>
              <div className={styles['stat-label']}>Total Budget</div>
              <div className={styles['stat-value']}>
                {formatBillions(budgetSummary.total_expenditure)}
              </div>
              <div className={styles['stat-sub']}>Fiscal Year 2025/26</div>
              <div className={styles['stat-source']}>
                Budget Communication, p.12
              </div>
            </div>
            <div className={styles['stat-card']}>
              <div className={styles['stat-label']}>Revenue</div>
              <div className={styles['stat-value']}>
                {formatBillions(budgetSummary.total_revenue)}
              </div>
              <div className={styles['stat-sub']}>Projected FY2025/26</div>
              <div className={styles['stat-source']}>
                Budget Communication, p.14
              </div>
            </div>
            <div className={styles['stat-card']}>
              <div className={styles['stat-label']}>National Debt</div>
              <div className={styles['stat-value']}>
                {formatBillions(budgetSummary.national_debt)}
              </div>
              <div className={styles['stat-sub']}>
                {budgetSummary.debt_to_gdp_ratio ?? '—'}% of GDP
              </div>
              <div className={styles['stat-source']}>Debt Report, p.3</div>
            </div>
            <div
              className={`${styles['stat-card']} ${styles['stat-card-surplus']}`}
            >
              <div className={styles['stat-label']}>Budget Surplus</div>
              <div
                className={`${styles['stat-value']} ${styles['stat-value-surplus']}`}
              >
                {formatCurrency(budgetSummary.deficit_surplus, true)}
              </div>
              <div className={styles['stat-sub']}>
                First surplus since independence 🎉
              </div>
              <div className={styles['stat-source']}>
                Budget Communication, p.8
              </div>
            </div>
          </div>

          {/* Your share */}
          <div className={styles['share-calc']}>
            <div className={styles['share-calc-header']}>
              <div>
                <div className={styles['share-calc-title']}>
                  Your Share of the National Budget
                </div>
                <div className={styles['share-calc-headline']}>
                  409,000 Bahamians. Your share:{' '}
                  <em id="shareTotal">$9,288</em>
                </div>
                <div className={styles['share-calc-sub']}>
                  Based on FY2025/26 budget. Hover any number to see its source
                  document.
                </div>
              </div>
            </div>

            <div className={styles['share-grid']}>
              <div className={styles['share-item']}>
                <div className={styles['si-label']}>🎓 Education</div>
                <div
                  className={`${styles['si-value']} ${styles['si-value-teal']}`}
                >
                  $1,204
                </div>
                <div className={styles['si-sub']}>of your annual share</div>
              </div>
              <div className={styles['share-item']}>
                <div className={styles['si-label']}>🏥 Health</div>
                <div
                  className={`${styles['si-value']} ${styles['si-value-teal']}`}
                >
                  $867
                </div>
                <div className={styles['si-sub']}>of your annual share</div>
              </div>
              <div className={styles['share-item']}>
                <div className={styles['si-label']}>🏗️ Infrastructure</div>
                <div
                  className={`${styles['si-value']} ${styles['si-value-teal']}`}
                >
                  $743
                </div>
                <div className={styles['si-sub']}>of your annual share</div>
              </div>
              <div className={styles['share-item']}>
                <div className={styles['si-label']}>📊 Budget surplus</div>
                <div
                  className={`${styles['si-value']} ${styles['si-value-teal']}`}
                >
                  +$184
                </div>
                <div className={styles['si-sub']}>
                  your share of the historic surplus
                </div>
              </div>
            </div>

            <button
              type="button"
              className={styles['share-expand-btn']}
              onClick={() => setShareExpanded((v) => !v)}
            >
              {shareExpanded
                ? 'Hide debt service & full breakdown'
                : 'Show debt service & full breakdown'}
            </button>

            <div
              className={`${styles['share-expanded']} ${
                shareExpanded ? styles['share-expanded-show'] : ''
              }`}
            >
              <div className={styles['debt-warning']}>
                <div className={styles['dw-text']}>
                  <strong>
                    Debt service is the largest single line item
                  </strong>{' '}
                  in the Bahamian budget. Every year, a significant portion of
                  government revenue goes not to services — but to servicing the
                  $11.4B national debt accumulated since independence. The
                  surplus is a turning point. But the debt load remains.
                </div>
                <div>
                  <div className={styles['dw-label']}>
                    Your debt service share
                  </div>
                  <div className={styles['dw-num']}>$1,847</div>
                </div>
              </div>
              <div className={styles['share-note']}>
                Full breakdown: Education $1,204 · Health $867 · Infrastructure
                $743 · Social Services $612 · National Security $480 · Debt
                Service $1,847 · Tourism $188 · Other $1,347 = Total $7,288
                direct services + $1,847 debt = $9,135 approx. Figures based on
                FY2025/26 Estimates of Expenditure divided by 409,000
                population.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Surplus monument & timeline (simplified) */}
      <section className={styles.monument}>
        <div className={styles['monument-intro']}>
          <div className={styles['monument-eyebrow']}>The historic moment</div>
          <h2 className={styles['monument-headline']}>
            52 years of deficits.
            <br />
            <em>One balanced budget.</em>
          </h2>
          <p className={styles['monument-sub']}>
            Every year since Bahamian independence in 1973, the government
            spent more than it earned. Each bar below represents a year in the
            red. Until now.
          </p>
        </div>

        <div className={styles['timeline-section']}>
          <div className={styles['timeline-legend']}>
            <div className={styles['legend-item']}>
              <span
                className={`${styles['legend-dot']} ${styles['legend-dot-deficit']}`}
              />
              Deficit year
            </div>
            <div className={styles['legend-item']}>
              <span
                className={`${styles['legend-dot']} ${styles['legend-dot-surplus']}`}
              />
              Surplus — FY2025/26
            </div>
          </div>

          <div className={styles['timeline-labels']}>
            <span>1973 — Independence</span>
            <span>1990</span>
            <span>2000</span>
            <span>2010</span>
            <span>2020</span>
            <span>2025/26 ★</span>
          </div>

          <div className={styles['timeline-bars']}>
            {/* Roughly represent many deficit years plus one surplus bar */}
            {Array.from({ length: 20 }).map((_, i) => (
              <div
                key={`def-${i}`}
                className={`${styles['t-bar']} ${styles['t-bar-deficit']}`}
                style={{ height: `${40 + (i % 10) * 3}%` }}
              >
                <div className={styles['t-bar-tooltip']}>Deficit year</div>
              </div>
            ))}
            <div
              className={`${styles['t-bar']} ${styles['t-bar-surplus']}`}
              style={{ height: '85%' }}
            >
              <div className={styles['t-bar-tooltip']}>
                2025/26
                <br />
                ✓ Surplus: $75.5M
              </div>
            </div>
          </div>

          <div className={styles['timeline-axis']} />

          <div className={styles['timeline-year-labels']}>
            {TIMELINE_YEARS.map((year) => (
              <span key={year}>
                {year === 2026 ? '2025/26 ★' : year}
              </span>
            ))}
          </div>

          <div className={styles['timeline-callout']}>
            <div className={styles['tc-text']}>
              <strong>
                2025/26 — The Bahamas records its first budget surplus since
                independence.
              </strong>{' '}
              A $75.5M surplus on a $3.8B budget. National debt-to-GDP falls
              from 88.7% to 68.9%. For the first time in 52 years, the
              government earned more than it spent. This is what fiscal
              discipline looks like — and BahamasOpenData will be the public
              record of it.
            </div>
            <div className={styles['tc-num']}>
              <div className={styles['tc-num-val']}>$75.5M</div>
              <div className={styles['tc-num-label']}>
                First surplus · 52 years
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Ask the Budget */}
      <V2AskBudgetPanel />

      {/* Ministries */}
      <section className={styles.ministries} id="ministries">
        <div className={styles['section-eyebrow']}>Where the money goes</div>
        <h2 className={styles['section-title']}>
          Ministry <em>Breakdown</em>
        </h2>
        <div className={styles['ministry-grid']}>
          {topMinistries.map((m) => {
            const trend = getTrend(m);
            const badgeClass =
              trend === 'over'
                ? styles['mc-badge-over']
                : trend === 'under'
                ? styles['mc-badge-under']
                : styles['mc-badge-on'];
            const barClass =
              trend === 'over'
                ? styles['mc-bar-fill-coral']
                : styles['mc-bar-fill-teal'];
            const widthPct =
              maxAllocation > 0 ? (m.allocation / maxAllocation) * 100 : 0;
            const insight =
              MINISTRY_INSIGHTS[m.id] ??
              'Allocation drawn from the official Estimates of Expenditure 2025/26.';
            return (
              <div key={m.id} className={styles['ministry-card']}>
                <div className={styles['mc-header']}>
                  <div className={styles['mc-name']}>{m.name}</div>
                  <div className={`${styles['mc-badge']} ${badgeClass}`}>
                    {trend === 'over'
                      ? 'Over budget'
                      : trend === 'under'
                      ? 'Under budget'
                      : 'On target'}
                  </div>
                </div>
                <div className={styles['mc-amount']}>
                  {formatMillionsWhole(m.allocation)}
                </div>
                <div className={styles['mc-sub']}>FY2025/26 Allocation</div>
                <div className={styles['mc-bar-track']}>
                  <div
                    className={`${styles['mc-bar-fill']} ${barClass}`}
                    style={{ width: `${widthPct}%` }}
                  />
                </div>
                <div className={styles['mc-insight']}>{insight}</div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Explore */}
      <section className={styles.explore} id="explore">
        <div className={styles['section-eyebrow']}>Explore the data</div>
        <h2 className={styles['section-title']}>
          Beyond the <em>budget</em>
        </h2>
        <div className={styles['explore-grid']}>
          {EXPLORE_CARDS.map((c) => (
            <Link
              key={c.title}
              href={c.href}
              className={styles['explore-card']}
            >
              <div className={styles['ec-icon']}>{c.icon}</div>
              <div className={styles['ec-label']}>{c.label}</div>
              <div className={styles['ec-title']}>{c.title}</div>
              <div className={styles['ec-desc']}>{c.desc}</div>
              <div className={styles['ec-stat']}>{c.stat}</div>
              <div className={styles['ec-stat-label']}>{c.statLabel}</div>
              <div className={styles['ec-link']}>
                Explore details →
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Stories */}
      <section className={styles.stories}>
        <div
          className={styles['section-eyebrow']}
          style={{ color: 'var(--teal-l)' }}
        >
          Data stories
        </div>
        <h2
          className={styles['section-title']}
          style={{ color: 'white' }}
        >
          What the numbers
          <br />
          <em>mean for you</em>
        </h2>
        <div className={styles['stories-grid']}>
          {STORIES.map((s) => (
            <article key={s.tag} className={styles['story-card']}>
              <div className={styles['sc-tag']}>{s.tag}</div>
              <div className={styles['sc-title']}>{s.title}</div>
              <p className={styles['sc-desc']}>{s.desc}</p>
              <div className={styles['sc-source']}>{s.source}</div>
            </article>
          ))}
        </div>
      </section>

      {/* Pro strip */}
      <div className={styles['pro-strip']} id="pro">
        <div className={styles['pro-strip-inner']}>
          <div>
            <div className={styles['pro-eyebrow']}>
              For Analysts &amp; Journalists
            </div>
            <div className={styles['pro-title']}>Download the raw data.</div>
            <p className={styles['pro-desc']}>
              Every dataset on this platform is available for export. CSV,
              Excel, JSON. Source documents linked. Methodology documented. Cite
              with confidence.
            </p>
          </div>
          <div className={styles['pro-actions']}>
            <Link href="/export" className={styles['pro-btn']}>
              <span className={styles['pro-btn-icon']}>📊</span>
              Download CSV
            </Link>
            <Link href="/export" className={styles['pro-btn']}>
              <span className={styles['pro-btn-icon']}>📄</span>
              Source Documents
            </Link>
            <Link href="/export" className={styles['pro-btn']}>
              <span className={styles['pro-btn-icon']}>⚙️</span>
              API Access
            </Link>
            <Link href="/export" className={styles['pro-btn']}>
              <span className={styles['pro-btn-icon']}>📋</span>
              Methodology
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles['footer-grid']}>
          <div>
            <div className={styles['footer-brand-name']}>
              Bahamas<em>OpenData</em>
            </div>
            <p className={styles['footer-text']}>
              Making Bahamian public finance clear and accessible. All data
              sourced from official government documents published by Parliament
              of The Bahamas.
            </p>
            <div className={styles['footer-legal']}>
              Data sourced from Official Bahamas Publications. © 2026
              Registered. Development by Kemis Group of Companies Inc.
            </div>
          </div>
          <div>
            <div className={styles['footer-col-title']}>Budget</div>
            <ul className={styles['footer-links']}>
              <li>
                <Link href="/" className={styles['footer-link']}>
                  Dashboard
                </Link>
              </li>
              <li>
                <Link href="/ministries" className={styles['footer-link']}>
                  National Budget
                </Link>
              </li>
              <li>
                <Link href="/ministries" className={styles['footer-link']}>
                  Ministry Breakdown
                </Link>
              </li>
              <li>
                <Link href="/debt" className={styles['footer-link']}>
                  Debt &amp; Revenue
                </Link>
              </li>
              <li>
                <Link href="/revenue" className={styles['footer-link']}>
                  Historical Data
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <div className={styles['footer-col-title']}>Data</div>
            <ul className={styles['footer-links']}>
              <li>
                <Link href="/health" className={styles['footer-link']}>
                  Health
                </Link>
              </li>
              <li>
                <Link href="/income" className={styles['footer-link']}>
                  Income &amp; Cost of Living
                </Link>
              </li>
              <li>
                <Link href="/polls" className={styles['footer-link']}>
                  Public Polls
                </Link>
              </li>
              <li>
                <Link href="/hot" className={styles['footer-link']}>
                  Hot Topics
                </Link>
              </li>
              <li>
                <Link href="/news" className={styles['footer-link']}>
                  News &amp; Updates
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <div className={styles['footer-col-title']}>Sources</div>
            <ul className={styles['footer-links']}>
              <li>
                <a
                  href="https://laws.bahamas.gov.bs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles['footer-link']}
                >
                  laws.bahamas.gov.bs
                </a>
              </li>
              <li>
                <a
                  href="https://courts.bs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles['footer-link']}
                >
                  courts.bs
                </a>
              </li>
              <li>
                <a
                  href="https://tribune242.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles['footer-link']}
                >
                  Tribune242
                </a>
              </li>
              <li>
                <a
                  href="https://thenassauguardian.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles['footer-link']}
                >
                  Nassau Guardian
                </a>
              </li>
              <li>
                <a
                  href="https://kemisdigital.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles['footer-link']}
                  style={{ color: 'var(--teal-l)' }}
                >
                  KemisDigital
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className={styles['footer-bottom']}>
          <p className={styles['footer-bottom-text']}>
            © 2026 BahamasOpenData · Nassau, The Bahamas · All figures from
            official Parliament documents
          </p>
          <p className={styles['footer-bottom-domain']}>bahamasopendata.com</p>
        </div>
      </footer>
    </div>
  );
}

