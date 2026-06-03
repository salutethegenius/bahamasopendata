'use client';

import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, Calendar, FileText } from 'lucide-react';
import FiscalYearSelector from '@/components/FiscalYearSelector';
import { formatCurrency } from '@/lib/format';
import { fiscalYearSearchParam, useFiscalYear, withFiscalYear } from '@/lib/fiscal-year';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

type YearSummary = {
  fiscal_year: string;
  total_revenue: number;
  total_expenditure: number;
  deficit_surplus: number;
  national_debt: number;
  source_document: string;
};

function PastBudgetsContent() {
  const { years, fiscalYear } = useFiscalYear();
  const [summaries, setSummaries] = useState<YearSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const results = await Promise.all(
          years.map(async (year) => {
            const res = await fetch(
              `${API_BASE}/budget/summary${fiscalYearSearchParam(year)}`,
            );
            if (!res.ok) {
              return null;
            }
            return res.json() as Promise<YearSummary>;
          }),
        );
        setSummaries(
          results.filter((row): row is YearSummary => row !== null).reverse(),
        );
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [years]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-turquoise font-semibold">
            National Budget
          </p>
          <h1 className="mt-2 text-3xl md:text-4xl font-bold text-gray-900">
            Past Budgets
          </h1>
          <p className="mt-3 max-w-2xl text-gray-600">
            Browse published fiscal years. Select a year to open the dashboard with
            that budget in view.
          </p>
        </div>
        <FiscalYearSelector label="View as" />
      </div>

      {loading ? (
        <p className="mt-10 text-gray-500">Loading budget history…</p>
      ) : (
        <div className="mt-10 grid gap-6 md:grid-cols-2">
          {summaries.map((summary) => {
            const isCurrent = summary.fiscal_year === fiscalYear;
            return (
              <motion.article
                key={summary.fiscal_year}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                className={`rounded-2xl border p-6 shadow-sm ${
                  isCurrent
                    ? 'border-turquoise/40 bg-turquoise/5'
                    : 'border-gray-200 bg-white'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Calendar className="h-4 w-4" />
                      FY {summary.fiscal_year}
                    </div>
                    <h2 className="mt-2 text-2xl font-bold text-gray-900">
                      {formatCurrency(summary.total_revenue)}
                    </h2>
                    <p className="text-sm text-gray-500">Total revenue</p>
                  </div>
                  {isCurrent ? (
                    <span className="rounded-full bg-turquoise/15 px-3 py-1 text-xs font-semibold text-turquoise">
                      Selected
                    </span>
                  ) : null}
                </div>

                <dl className="mt-6 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <dt className="text-gray-500">Expenditure</dt>
                    <dd className="font-semibold text-gray-900">
                      {formatCurrency(summary.total_expenditure)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Surplus / deficit</dt>
                    <dd
                      className={`font-semibold ${
                        summary.deficit_surplus >= 0 ? 'text-emerald-600' : 'text-rose-600'
                      }`}
                    >
                      {formatCurrency(Math.abs(summary.deficit_surplus))}
                      {summary.deficit_surplus >= 0 ? ' surplus' : ' deficit'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">National debt</dt>
                    <dd className="font-semibold text-gray-900">
                      {formatCurrency(summary.national_debt)}
                    </dd>
                  </div>
                  <div className="col-span-2 flex items-start gap-2 text-gray-500">
                    <FileText className="mt-0.5 h-4 w-4 shrink-0" />
                    <span className="break-all">{summary.source_document}</span>
                  </div>
                </dl>

                <Link
                  href={withFiscalYear('/', summary.fiscal_year)}
                  className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-turquoise hover:text-turquoise-dark"
                >
                  Open FY {summary.fiscal_year} dashboard
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </motion.article>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function PastBudgetsPage() {
  return (
    <Suspense fallback={<div className="max-w-7xl mx-auto px-4 py-10">Loading…</div>}>
      <PastBudgetsContent />
    </Suspense>
  );
}
