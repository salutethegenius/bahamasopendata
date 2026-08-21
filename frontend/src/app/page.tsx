'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { formatCurrency } from '@/lib/format';
import { CURRENT_FISCAL_YEAR } from '@/lib/fiscal-year';
import type { IncomeComparison, Ministry, NewsItem, Poll } from '@/types';
import { initialBudgetSummary, initialMinistries } from '@/data/budget';
import { newsItems } from '@/data/news';
import { grandBahamaDataset } from '@/data/grandBahama';
import { currentScorecard } from '@/data/scorecards';
import V2AskBudgetPanel from '@/components/v2/V2AskBudgetPanel';
import styles from './home.module.css';

type TickerItem = {
  text: string;
  source: string;
  url?: string;
};

type SectorSlice = {
  name: string;
  value: number;
};

type HotTopicSummary = {
  slug: string;
  title: string;
  source: string;
  year: string;
  summary: string;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

const POPULATION = 409_000;
const FALLBACK_INCOME_MONTH = 10_200;

const INITIAL_SECTORS: SectorSlice[] = [
  { name: 'Public Debt Service', value: 732_203_258 },
  { name: 'Health', value: 400_228_827 },
  { name: 'Education', value: 383_555_171 },
  { name: 'Security', value: 247_645_168 },
  { name: 'Tourism', value: 98_089_530 },
  { name: 'Social Services', value: 64_224_852 },
  { name: 'Other', value: 1_213_832_850 },
];

const TIMELINE_YEARS = [1973, 1980, 1990, 2000, 2010, 2020, 2026] as const;

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
  if (value == null || !Number.isFinite(value)) return '—';
  const billions = value / 1_000_000_000;
  return `$${billions.toFixed(1)}B`;
};

const formatMillionsWhole = (value: number | null | undefined) => {
  if (value == null || !Number.isFinite(value)) return '—';
  const millions = Math.round(value / 1_000_000);
  return `$${millions}M`;
};

const perPerson = (value: number) => value / POPULATION;

const findSector = (sectors: SectorSlice[], needle: string) =>
  sectors.find((s) => s.name.toLowerCase().includes(needle.toLowerCase()));

export default function MarketingHomePage() {
  const [navScrolled, setNavScrolled] = useState(false);
  const [shareExpanded, setShareExpanded] = useState(false);
  const [budgetSummary, setBudgetSummary] = useState(initialBudgetSummary);
  const [ministries, setMinistries] = useState<Ministry[]>(initialMinistries);
  const [sectors, setSectors] = useState<SectorSlice[]>(INITIAL_SECTORS);
  const [incomeComparisons, setIncomeComparisons] = useState<
    IncomeComparison[] | null
  >(null);
  const [activePoll, setActivePoll] = useState<Poll | null>(null);
  const [hotTopics, setHotTopics] = useState<HotTopicSummary[]>([]);
  const [latestNewsItems, setLatestNewsItems] = useState<NewsItem[]>(
    newsItems.map((item) => ({
      id: item.id,
      title: item.title,
      source: item.source,
      url: item.url,
      summary: item.summary,
      category: item.category,
      published_date: item.date,
    })),
  );

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
        const [
          budgetRes,
          ministriesRes,
          sectorRes,
          economicRes,
          pollsRes,
          hotTopicsRes,
          newsRes,
        ] = await Promise.allSettled([
          fetch(`${API_BASE}/budget/summary`),
          fetch(`${API_BASE}/ministries`),
          fetch(`${API_BASE}/budget/sector-breakdown`),
          fetch(`${API_BASE}/economic/comparison`),
          fetch(`${API_BASE}/polls/active`),
          fetch(`${API_BASE}/hot-topics/reports`),
          fetch(`${API_BASE}/news`),
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

        if (sectorRes.status === 'fulfilled' && sectorRes.value.ok) {
          const json = await sectorRes.value.json();
          if (Array.isArray(json.sectors)) {
            type SectorApi = { name: string; amount: number };
            setSectors(
              (json.sectors as SectorApi[]).map((s) => ({
                name: s.name,
                value: s.amount,
              })),
            );
          }
        }

        if (economicRes.status === 'fulfilled' && economicRes.value.ok) {
          const json = await economicRes.value.json();
          if (Array.isArray(json)) {
            setIncomeComparisons(json);
          }
        }

        if (pollsRes.status === 'fulfilled' && pollsRes.value.ok) {
          const json = await pollsRes.value.json();
          setActivePoll(json);
        }

        if (hotTopicsRes.status === 'fulfilled' && hotTopicsRes.value.ok) {
          const json = await hotTopicsRes.value.json();
          if (Array.isArray(json)) {
            setHotTopics(json);
          }
        }

        if (newsRes.status === 'fulfilled' && newsRes.value.ok) {
          const json = await newsRes.value.json();
          if (Array.isArray(json) && json.length > 0) {
            setLatestNewsItems(json as NewsItem[]);
          }
        }
      } catch (err) {
        console.error('Failed to load marketing home data', err);
      }
    };

    fetchData();
  }, []);

  const fiscalYear = budgetSummary.fiscal_year || CURRENT_FISCAL_YEAR;
  const isSurplus = budgetSummary.deficit_surplus >= 0;

  const topMinistries = useMemo(
    () =>
      ministries
        .slice()
        .sort((a, b) => b.allocation - a.allocation)
        .slice(0, 6),
    [ministries],
  );

  const maxAllocation = topMinistries.reduce(
    (max, m) => (m.allocation > max ? m.allocation : max),
    0,
  );

  const healthMinistry = useMemo(
    () =>
      ministries.find(
        (m) => m.id === 'health' || m.sector?.toLowerCase() === 'health',
      ),
    [ministries],
  );

  const incomeSnapshot =
    incomeComparisons && incomeComparisons.length > 0
      ? incomeComparisons[0]
      : null;

  const educationSector = findSector(sectors, 'education');
  const healthSector = findSector(sectors, 'health');
  const securitySector = findSector(sectors, 'security');
  const debtSector = findSector(sectors, 'debt');

  const shareTotal = perPerson(budgetSummary.total_expenditure);
  const shareEducation = perPerson(educationSector?.value ?? 0);
  const shareHealth = perPerson(healthSector?.value ?? 0);
  const shareSecurity = perPerson(securitySector?.value ?? 0);
  const shareDebt = perPerson(debtSector?.value ?? 0);
  const shareSurplus = perPerson(budgetSummary.deficit_surplus);

  const getTrend = (m: Ministry): 'up' | 'down' | 'flat' => {
    if (m.change_percent > 1) return 'up';
    if (m.change_percent < -1) return 'down';
    return 'flat';
  };

  const tickerItems: TickerItem[] = [
    {
      text: `FY${fiscalYear} draft estimates: ${formatBillions(budgetSummary.total_expenditure)} expenditure · ${formatBillions(budgetSummary.total_revenue)} revenue`,
      source: `Budget FY${fiscalYear}`,
    },
    {
      text: `Projected ${isSurplus ? 'surplus' : 'deficit'}: ${formatCurrency(budgetSummary.deficit_surplus, true)} on the current budget`,
      source: `Budget FY${fiscalYear}`,
    },
    {
      text: `National debt ${formatBillions(budgetSummary.national_debt)} · ${budgetSummary.debt_to_gdp_ratio ?? '—'}% of GDP`,
      source: `Budget FY${fiscalYear}`,
    },
    {
      text: 'Historic first: Bahamas recorded a budget surplus in FY2025/26 — first since independence in 1973',
      source: 'Budget FY2025/26',
    },
    {
      text: 'Govt $357M claim against GBPA dismissed in full by Arbitration Tribunal',
      url: 'https://www.tribune242.com/news/2026/mar/03/govts-357m-claim-against-gbpa-dismissed-in-full/',
      source: 'Tribune242',
    },
    {
      text: `Health allocation: ${formatCurrency(healthMinistry?.allocation ?? healthSector?.value ?? 0, true)} · Education sector: ${formatCurrency(educationSector?.value ?? 0, true)}`,
      source: 'Estimates of Expenditure',
    },
  ];

  const exploreCards = [
    {
      icon: '🏥',
      label: 'Health Data',
      title: 'Health & Wellness',
      desc: 'Hospital allocations, clinic funding, public health spending, and health outcomes data across the islands.',
      stat: healthMinistry
        ? formatCurrency(healthMinistry.allocation, true)
        : '—',
      statLabel: `Health allocation FY${fiscalYear}`,
      href: '/health',
    },
    {
      icon: '💰',
      label: 'Income Data',
      title: 'Income & Cost of Living',
      desc: 'Middle class income benchmarks, cost of living indices, and economic pressure indicators for Bahamian households.',
      stat: formatCurrency(
        incomeSnapshot?.middle_class?.month_amount ?? FALLBACK_INCOME_MONTH,
      ),
      statLabel: 'Middle class monthly income',
      href: '/income',
    },
    {
      icon: '🏛️',
      label: 'Grand Bahama',
      title: 'Grand Bahama Platform',
      desc: 'Digital government infrastructure for Grand Bahama — institutional reference, districts, and parliamentary seats.',
      stat: `${grandBahamaDataset.districts.length}`,
      statLabel: `Districts · ${grandBahamaDataset.mps.length} parliamentary seats`,
      href: '/grand-bahama',
    },
    {
      icon: '📊',
      label: 'Public Polls',
      title: 'What Bahamians Think',
      desc: 'Real-time polling on national priorities, policy opinions, and public satisfaction with government services.',
      stat: activePoll ? 'Active' : 'None',
      statLabel: activePoll
        ? activePoll.question
        : 'No active poll at the moment',
      href: '/polls',
    },
    {
      icon: '🗞️',
      label: 'News',
      title: 'Budget & Economic News',
      desc: 'Official budget updates, economic announcements, and government financial decisions — sourced and tracked.',
      stat: `${latestNewsItems.length}`,
      statLabel:
        latestNewsItems.length > 0
          ? latestNewsItems[0].title
          : 'No news yet',
      href: '/news',
    },
    {
      icon: '🔥',
      label: 'Hot Topics',
      title: 'Accountability Reports',
      desc: 'Deep-dive reports on specific issues in Bahamian public finance — GBPA, national debt, surplus trajectory.',
      stat: `${hotTopics.length}`,
      statLabel: `${hotTopics.length} report${hotTopics.length === 1 ? '' : 's'} available`,
      href: '/hot',
    },
    {
      icon: '📋',
      label: 'Scorecards',
      title: 'Government Scorecards',
      desc: 'Independent grades on delivery versus announcements across the Davis administration.',
      stat: currentScorecard.overall.firstTerm,
      statLabel: currentScorecard.thesis,
      href: '/scorecards',
    },
    {
      icon: '🏛️',
      label: 'Ministries',
      title: 'Ministry Overview',
      desc: 'See which ministries receive the most funding, track year-on-year changes, and understand allocation logic.',
      stat: `${ministries.length}`,
      statLabel:
        ministries.length > 0
          ? `Top: ${ministries.slice().sort((a, b) => b.allocation - a.allocation)[0].name}`
          : 'Ministries tracked',
      href: '/ministries',
    },
  ];

  const stories = [
    {
      tag: 'History · The Surplus',
      title: `The first surplus since 1973 — and what FY${fiscalYear} continues`,
      desc: `FY2025/26 broke 52 years of deficits with a $75.5M surplus. The current draft estimates project ${formatCurrency(budgetSummary.deficit_surplus, true)} — the follow-through year. Here's what changed, and what still has to hold.`,
      source: 'Budget Communication 2025/26 & Draft Estimates 2026/27',
      href: '/hot',
    },
    {
      tag: 'Analysis · National Debt',
      title: `Understanding the ${formatBillions(budgetSummary.national_debt)} debt — and why the ratio is falling`,
      desc: `Debt is still large. Debt-to-GDP at ${budgetSummary.debt_to_gdp_ratio ?? '—'}% is the number to watch. What drove the accumulation, and what the current path out looks like.`,
      source: 'Debt Management Report · Dashboard debt overview',
      href: '/debt',
    },
    {
      tag: 'Civic · Your Money',
      title: 'Which ministry gets the most — and whether allocations moved',
      desc:
        topMinistries.length > 0
          ? `${topMinistries[0].name} leads this year's allocations. Education sector ${formatCurrency(educationSector?.value ?? 0, true)}. Health ${formatCurrency(healthMinistry?.allocation ?? 0, true)}. Debt service remains the largest structural cost.`
          : 'A plain-language breakdown of who gets what, why allocations changed, and what you should be watching.',
      source: `Estimates of Expenditure ${fiscalYear}`,
      href: '/ministries',
    },
  ];

  const shareBreakdownNote = [
    ...sectors.map(
      (s) => `${s.name} ${formatCurrency(perPerson(s.value))}`,
    ),
    `${isSurplus ? 'Surplus' : 'Deficit'} ${formatCurrency(shareSurplus)}`,
    `Total ${formatCurrency(shareTotal)} per person`,
  ].join(' · ');

  return (
    <div className={styles.pageRoot}>
      <div className={styles['ticker-bar']}>
        <div className={styles['ticker-label']}>Bahamas</div>
        <div className={styles['ticker-scroll']}>
          {[...Array(2)].map((_, loopIndex) =>
            tickerItems.map((item, idx) => (
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

      <nav
        className={`${styles.nav} ${navScrolled ? styles.navScrolled : ''}`}
      >
        <Link href="/" className={styles['nav-logo']}>
          <span className={styles['nav-mark']}>
            Bahamas
            <em>OpenData</em>
          </span>
        </Link>
        <div className={styles['nav-right']}>
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
                <span>Draft estimates · FY{fiscalYear}</span>
              </div>
            </li>
            <li>
              <Link href="/export" className={styles['nav-link']}>
                Export
              </Link>
            </li>
          </ul>
          <Link href="/dashboard" className={styles['btn-export']}>
            Open dashboard
          </Link>
        </div>
      </nav>

      <section className={styles.hero}>
        <div className={styles['hero-inner']}>
          <div className={styles['hero-eyebrow']}>
            Fiscal Year {fiscalYear} · Official Budget Documents
          </div>
          <h1 className={styles['hero-headline']}>
            Your government plans to spend
            <br />
            <em>{formatBillions(budgetSummary.total_expenditure)}</em> this year.
          </h1>
          <p className={styles['hero-sub']}>
            Real-time insights into the Bahamas national budget — sourced from
            official Parliament documents, processed by RAG, verified against
            primary records. Every number traceable.
          </p>
          <div className={styles['hero-cta-row']}>
            <Link href="/dashboard" className={styles['btn-dashboard']}>
              Open dashboard
            </Link>
            <a href="#explore" className={styles['btn-dashboard-ghost']}>
              Explore the data
            </a>
          </div>

          <div className={styles['hero-stats']}>
            <div className={styles['stat-card']}>
              <div className={styles['stat-label']}>Total Budget</div>
              <div className={styles['stat-value']}>
                {formatBillions(budgetSummary.total_expenditure)}
              </div>
              <div className={styles['stat-sub']}>Fiscal Year {fiscalYear}</div>
              <div className={styles['stat-source']}>
                {budgetSummary.source_document || 'Draft Estimates'}
              </div>
            </div>
            <div className={styles['stat-card']}>
              <div className={styles['stat-label']}>Revenue</div>
              <div className={styles['stat-value']}>
                {formatBillions(budgetSummary.total_revenue)}
              </div>
              <div className={styles['stat-sub']}>Projected FY{fiscalYear}</div>
              <div className={styles['stat-source']}>
                {budgetSummary.source_document || 'Draft Estimates'}
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
              <div className={styles['stat-source']}>Debt overview</div>
            </div>
            <div
              className={`${styles['stat-card']} ${styles['stat-card-surplus']}`}
            >
              <div className={styles['stat-label']}>
                {isSurplus ? 'Budget Surplus' : 'Budget Deficit'}
              </div>
              <div
                className={`${styles['stat-value']} ${styles['stat-value-surplus']}`}
              >
                {formatCurrency(budgetSummary.deficit_surplus, true)}
              </div>
              <div className={styles['stat-sub']}>
                Draft estimates FY{fiscalYear}
              </div>
              <div className={styles['stat-source']}>
                {budgetSummary.source_document || 'Draft Estimates'}
              </div>
            </div>
          </div>

          <div className={styles['share-calc']}>
            <div className={styles['share-calc-header']}>
              <div>
                <div className={styles['share-calc-title']}>
                  Your Share of the National Budget
                </div>
                <div className={styles['share-calc-headline']}>
                  {POPULATION.toLocaleString()} Bahamians. Your share:{' '}
                  <em>{formatCurrency(shareTotal)}</em>
                </div>
                <div className={styles['share-calc-sub']}>
                  Based on FY{fiscalYear} expenditure divided by population.
                  Sector shares use the same breakdown as the dashboard.
                </div>
              </div>
            </div>

            <div className={styles['share-grid']}>
              <div className={styles['share-item']}>
                <div className={styles['si-label']}>Education</div>
                <div
                  className={`${styles['si-value']} ${styles['si-value-teal']}`}
                >
                  {formatCurrency(shareEducation)}
                </div>
                <div className={styles['si-sub']}>of your annual share</div>
              </div>
              <div className={styles['share-item']}>
                <div className={styles['si-label']}>Health</div>
                <div
                  className={`${styles['si-value']} ${styles['si-value-teal']}`}
                >
                  {formatCurrency(shareHealth)}
                </div>
                <div className={styles['si-sub']}>of your annual share</div>
              </div>
              <div className={styles['share-item']}>
                <div className={styles['si-label']}>Security</div>
                <div
                  className={`${styles['si-value']} ${styles['si-value-teal']}`}
                >
                  {formatCurrency(shareSecurity)}
                </div>
                <div className={styles['si-sub']}>of your annual share</div>
              </div>
              <div className={styles['share-item']}>
                <div className={styles['si-label']}>
                  {isSurplus ? 'Budget surplus' : 'Budget deficit'}
                </div>
                <div
                  className={`${styles['si-value']} ${styles['si-value-teal']}`}
                >
                  {isSurplus ? '+' : ''}
                  {formatCurrency(shareSurplus)}
                </div>
                <div className={styles['si-sub']}>
                  your share of the {isSurplus ? 'surplus' : 'deficit'}
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
                  government revenue goes not to services — but to servicing the{' '}
                  {formatBillions(budgetSummary.national_debt)} national debt.
                  The surplus path is a turning point. The debt load remains.
                </div>
                <div>
                  <div className={styles['dw-label']}>
                    Your debt service share
                  </div>
                  <div className={styles['dw-num']}>
                    {formatCurrency(shareDebt)}
                  </div>
                </div>
              </div>
              <div className={styles['share-note']}>
                Full breakdown: {shareBreakdownNote}. Figures based on FY
                {fiscalYear} estimates divided by {POPULATION.toLocaleString()}{' '}
                population.
              </div>
            </div>
          </div>
        </div>
      </section>

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
            spent more than it earned — until FY2025/26. The current year
            continues that surplus path. The bars below are the historical
            record, not this year&apos;s dashboard totals.
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
              First surplus — FY2025/26
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
              A $75.5M surplus on a $3.8B budget. That year is the turning
              point this platform exists to keep on the public record. FY
              {fiscalYear} figures above are the live dashboard totals — not
              this historical bar.
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

      <V2AskBudgetPanel />

      <section className={styles.ministries} id="ministries">
        <div className={styles['section-eyebrow']}>Where the money goes</div>
        <h2 className={styles['section-title']}>
          Ministry <em>Breakdown</em>
        </h2>
        <div className={styles['ministry-grid']}>
          {topMinistries.map((m) => {
            const trend = getTrend(m);
            const badgeClass =
              trend === 'up'
                ? styles['mc-badge-over']
                : trend === 'down'
                ? styles['mc-badge-under']
                : styles['mc-badge-on'];
            const barClass =
              trend === 'down'
                ? styles['mc-bar-fill-coral']
                : styles['mc-bar-fill-teal'];
            const widthPct =
              maxAllocation > 0 ? (m.allocation / maxAllocation) * 100 : 0;
            const insight =
              MINISTRY_INSIGHTS[m.id] ??
              `Allocation drawn from the official Estimates of Expenditure ${fiscalYear}.`;
            return (
              <Link
                key={m.id}
                href="/ministries"
                className={styles['ministry-card']}
              >
                <div className={styles['mc-header']}>
                  <div className={styles['mc-name']}>{m.name}</div>
                  <div className={`${styles['mc-badge']} ${badgeClass}`}>
                    {trend === 'up'
                      ? `Up ${m.change_percent.toFixed(1)}% YoY`
                      : trend === 'down'
                      ? `Down ${Math.abs(m.change_percent).toFixed(1)}% YoY`
                      : 'Flat YoY'}
                  </div>
                </div>
                <div className={styles['mc-amount']}>
                  {formatMillionsWhole(m.allocation)}
                </div>
                <div className={styles['mc-sub']}>FY{fiscalYear} Allocation</div>
                <div className={styles['mc-bar-track']}>
                  <div
                    className={`${styles['mc-bar-fill']} ${barClass}`}
                    style={{ width: `${widthPct}%` }}
                  />
                </div>
                <div className={styles['mc-insight']}>{insight}</div>
              </Link>
            );
          })}
        </div>
      </section>

      <section className={styles.explore} id="explore">
        <div className={styles['section-eyebrow']}>Explore the data</div>
        <h2 className={styles['section-title']}>
          Beyond the <em>budget</em>
        </h2>
        <div className={styles['explore-grid']}>
          {exploreCards.map((c) => (
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
              <div className={styles['ec-link']}>Explore details →</div>
            </Link>
          ))}
        </div>
      </section>

      <section className={styles.stories}>
        <div
          className={styles['section-eyebrow']}
          style={{ color: 'var(--teal-l)' }}
        >
          Data stories
        </div>
        <h2 className={styles['section-title']} style={{ color: 'white' }}>
          What the numbers
          <br />
          <em>mean for you</em>
        </h2>
        <div className={styles['stories-grid']}>
          {stories.map((s) => (
            <Link key={s.tag} href={s.href} className={styles['story-card']}>
              <div className={styles['sc-tag']}>{s.tag}</div>
              <div className={styles['sc-title']}>{s.title}</div>
              <p className={styles['sc-desc']}>{s.desc}</p>
              <div className={styles['sc-source']}>{s.source}</div>
              <div className={styles['sc-link']}>Open in the dashboard →</div>
            </Link>
          ))}
        </div>
      </section>

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
            <Link href="/dashboard" className={styles['pro-btn']}>
              <span className={styles['pro-btn-icon']}>📋</span>
              Open dashboard
            </Link>
          </div>
        </div>
      </div>

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
                <Link href="/dashboard" className={styles['footer-link']}>
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
                <Link href="/grand-bahama" className={styles['footer-link']}>
                  Grand Bahama
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
                <Link href="/scorecards" className={styles['footer-link']}>
                  Scorecards
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
