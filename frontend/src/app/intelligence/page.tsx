'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000/api/v1';

type Pagespeed = {
  performance: number | null;
  categories: Record<string, number>;
  source_url?: string;
};

type BankRow = {
  bank_id: string;
  display_name: string;
  short_name: string;
  series_token: string;
  domain: string | null;
  facebook_followers: number | null;
  instagram_followers: number | null;
  youtube_subscribers: number | null;
  twitter_followers: number | null;
  pagespeed: Pagespeed | null;
};

type Snapshot = {
  imprint: string;
  edition: string;
  capture_date: string;
  thin_data_note: string;
  confirmed_bank_counts: Record<string, number>;
  banks: BankRow[];
  missing_banks: string[];
};

const SERIES_COLOR: Record<string, string> = {
  '--intel-series-1': 'var(--intel-series-1)',
  '--intel-series-2': 'var(--intel-series-2)',
  '--intel-series-3': 'var(--intel-series-3)',
  '--intel-series-4': 'var(--intel-series-4)',
  '--intel-series-5': 'var(--intel-series-5)',
  '--intel-series-6': 'var(--intel-series-6)',
};

function formatCount(value: number | null): string {
  if (value == null) return '—';
  return new Intl.NumberFormat('en-US').format(value);
}

export default function IntelligencePage() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch(`${API_BASE}/intelligence/snapshot`);
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.detail || `HTTP ${response.status}`);
        }
        const payload = (await response.json()) as Snapshot;
        if (!cancelled) {
          setSnapshot(payload);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load snapshot');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div data-imprint="intelligence" className="min-h-screen">
      <div className="mx-auto max-w-6xl px-6 pb-20 pt-10 md:px-10">
        <motion.header
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="border-b border-[var(--intel-border)] pb-10"
        >
          <p className="font-mono text-[11px] uppercase tracking-[0.15em] text-[var(--intel-text-accent)]">
            Bahamas Open Data | Intelligence
          </p>
          <h1 className="mt-4 max-w-3xl text-4xl font-bold leading-tight md:text-5xl">
            Banking Sector 2026
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-[var(--intel-text-secondary)]">
            Public digital footprint snapshot for the six-bank cohort. Sparse signals
            stay blank — we do not invent coverage.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-4 font-mono text-sm text-[var(--intel-text-tertiary)]">
            <span>
              Capture{' '}
              <span className="text-[var(--intel-text-primary)]">
                {snapshot?.capture_date ?? '…'}
              </span>
            </span>
            <Link
              href="/"
              className="text-[var(--intel-text-accent)] underline-offset-4 hover:underline"
            >
              ← Civic dashboard
            </Link>
          </div>
        </motion.header>

        {loading && (
          <p className="mt-12 font-mono text-sm text-[var(--intel-text-secondary)]">
            Loading snapshot…
          </p>
        )}

        {error && (
          <p className="mt-12 font-mono text-sm text-[var(--intel-data-warning)]">
            {error}
          </p>
        )}

        {snapshot && (
          <>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.15, duration: 0.4 }}
              className="mt-8 max-w-3xl text-[15px] leading-6 text-[var(--intel-text-secondary)]"
            >
              {snapshot.thin_data_note}
            </motion.p>

            <motion.section
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.4 }}
              className="mt-12"
            >
              <h2 className="text-xl font-semibold">Confirmed coverage</h2>
              <p className="mt-2 font-mono text-sm text-[var(--intel-text-tertiary)]">
                Banks with a real public count on this capture date
              </p>
              <dl className="mt-6 grid grid-cols-2 gap-x-8 gap-y-4 md:grid-cols-4">
                {Object.entries(snapshot.confirmed_bank_counts).map(([key, count]) => (
                  <div key={key} className="border-t border-[var(--intel-border)] pt-3">
                    <dt className="font-mono text-xs uppercase tracking-wider text-[var(--intel-text-tertiary)]">
                      {key}
                    </dt>
                    <dd className="mt-1 font-mono text-3xl tabular-nums text-[var(--intel-text-accent)]">
                      {count}
                      <span className="text-base text-[var(--intel-text-tertiary)]">
                        /{snapshot.banks.length}
                      </span>
                    </dd>
                  </div>
                ))}
              </dl>
            </motion.section>

            <motion.section
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.4 }}
              className="mt-16"
            >
              <h2 className="text-xl font-semibold">Cohort metrics</h2>
              <div className="mt-6 overflow-x-auto">
                <table className="w-full min-w-[720px] border-collapse text-left">
                  <thead>
                    <tr className="border-b border-[var(--intel-border)] font-mono text-xs uppercase tracking-wider text-[var(--intel-text-tertiary)]">
                      <th className="py-3 pr-4 font-medium">Bank</th>
                      <th className="py-3 pr-4 font-medium">Facebook</th>
                      <th className="py-3 pr-4 font-medium">Instagram</th>
                      <th className="py-3 pr-4 font-medium">YouTube</th>
                      <th className="py-3 font-medium">PageSpeed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {snapshot.banks.map((bank) => (
                      <tr
                        key={bank.bank_id}
                        className="border-b border-[var(--intel-border)]/60"
                      >
                        <td className="py-4 pr-4">
                          <div className="flex items-center gap-3">
                            <span
                              className="inline-block h-2.5 w-2.5 shrink-0"
                              style={{
                                background:
                                  SERIES_COLOR[bank.series_token] ??
                                  'var(--intel-turquoise-500)',
                              }}
                            />
                            <div>
                              <div className="font-medium">{bank.short_name}</div>
                              <div className="font-mono text-xs text-[var(--intel-text-tertiary)]">
                                {bank.domain ?? 'no public site'}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 pr-4 font-mono tabular-nums">
                          {formatCount(bank.facebook_followers)}
                        </td>
                        <td className="py-4 pr-4 font-mono tabular-nums">
                          {formatCount(bank.instagram_followers)}
                        </td>
                        <td className="py-4 pr-4 font-mono tabular-nums">
                          {formatCount(bank.youtube_subscribers)}
                        </td>
                        <td className="py-4 font-mono tabular-nums">
                          {bank.pagespeed?.performance != null
                            ? bank.pagespeed.performance
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.section>
          </>
        )}
      </div>
    </div>
  );
}
