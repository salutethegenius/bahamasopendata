'use client';

import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { MinistryDetail, AskResponse } from '@/types';
import { formatCurrency, formatPercent } from '@/lib/format';
import { Activity, HeartPulse, FileText, AlertCircle, MapPin } from 'lucide-react';
import AskBar from '@/components/AskBar';
import { islands } from '@/data/islands';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

type SectorBreakdownResponse = {
  fiscal_year: string;
  sectors: { name: string; amount: number; color: string }[];
  total: number;
  source_document: string;
  source_page: number;
};

export default function HealthPage() {
  const [detail, setDetail] = useState<MinistryDetail | null>(null);
  const [sectorData, setSectorData] = useState<SectorBreakdownResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [healthProjects] = useState(() => {
    return islands.flatMap((island) =>
      island.projects
        .filter((p) => p.category === 'health')
        .map((p) => ({
          islandId: island.id,
          islandName: island.name,
          name: p.name,
          amount: p.amount,
        })),
    );
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const [ministryRes, sectorRes] = await Promise.all([
          fetch(`${API_BASE}/ministries/health`),
          fetch(`${API_BASE}/budget/sector-breakdown`),
        ]);

        if (!ministryRes.ok) {
          throw new Error('Failed to load Ministry of Health data.');
        }

        if (!sectorRes.ok) {
          throw new Error('Failed to load sector breakdown data.');
        }

        const ministryJson = await ministryRes.json();
        const sectorJson = (await sectorRes.json()) as SectorBreakdownResponse;

        setDetail(ministryJson);
        setSectorData(sectorJson);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unexpected error loading health data.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const healthSector = sectorData?.sectors.find(
    (s) => s.name.toLowerCase() === 'health',
  );

  const healthShare =
    sectorData && healthSector
      ? healthSector.amount / sectorData.total
      : null;

  const totalHealthProjectsAmount = useMemo(
    () =>
      healthProjects.reduce((sum, p) => sum + p.amount, 0),
    [healthProjects],
  );

  const handleAsk = async (question: string): Promise<AskResponse> => {
    try {
      const { askQuestion } = await import('@/lib/api');
      return await askQuestion(question);
    } catch (err) {
      return {
        answer:
          err instanceof Error
            ? err.message
            : "I'm having trouble connecting to the answer service. Please try again.",
        numbers: null,
        chart_data: null,
        citations: [],
        confidence: 0,
      };
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-turquoise/10 flex items-center justify-center">
            <HeartPulse className="w-5 h-5 text-turquoise" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Health <span className="text-turquoise">&amp; Wellness</span>
            </h1>
            <p className="text-gray-600">
              How the Bahamas invests in hospitals, clinics, public health, and environmental health services.
            </p>
          </div>
        </div>
        {detail && (
          <p className="text-sm text-gray-500 flex items-center gap-2">
            <Activity className="w-4 h-4 text-turquoise" />
            <span>Ministry of Health &amp; Wellness – Budget 2025/26</span>
          </p>
        )}
      </motion.div>

      {isLoading && (
        <div className="space-y-4">
          <div className="h-24 bg-gray-100 rounded-xl animate-pulse" />
          <div className="h-64 bg-gray-100 rounded-xl animate-pulse" />
        </div>
      )}

      {!isLoading && error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-8 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
          <div>
            <p className="font-semibold text-red-800">Could not load health data</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {!isLoading && detail && (
        <>
          {/* Key health tiles */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-gray-500">Total Allocation 2025/26</p>
              <p className="text-2xl md:text-3xl font-bold text-gray-900 tabular-nums">
                {formatCurrency(detail.allocation, true)}
              </p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-gray-500">Health Share of Recurrent Budget</p>
              <p className="text-2xl font-bold text-turquoise tabular-nums">
                {healthShare !== null ? formatPercent(healthShare * 100) : '—'}
              </p>
              {healthSector && sectorData && (
                <p className="text-xs text-gray-500 mt-1">
                  {formatCurrency(healthSector.amount, true)} of{' '}
                  {formatCurrency(sectorData.total, true)} across all sectors
                </p>
              )}
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-gray-500">Salaries &amp; Wages</p>
              <p className="text-2xl font-bold text-gray-900 tabular-nums">
                {formatCurrency(detail.salaries, true)}
              </p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-gray-500">Programs &amp; Capital</p>
              <p className="text-2xl font-bold text-gray-900 tabular-nums">
                {formatCurrency(detail.programs + detail.capital_projects, true)}
              </p>
            </div>
          </div>

          {/* Layout: left – breakdown, right – trend */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Breakdown */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-xl border border-gray-200 p-6"
            >
              <h2 className="text-lg font-semibold text-gray-900 mb-1">
                How health funds are used
              </h2>
              <p className="text-sm text-gray-500 mb-4">
                Breakdown of the Ministry of Health &amp; Wellness allocation.
              </p>
              <div className="grid grid-cols-2 gap-3 mb-6">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Salaries</p>
                  <p className="font-bold text-gray-900">
                    {formatCurrency(detail.salaries, true)}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Programs</p>
                  <p className="font-bold text-gray-900">
                    {formatCurrency(detail.programs, true)}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Capital Projects</p>
                  <p className="font-bold text-gray-900">
                    {formatCurrency(detail.capital_projects, true)}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500">Grants</p>
                  <p className="font-bold text-gray-900">
                    {formatCurrency(detail.grants, true)}
                  </p>
                </div>
              </div>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Salaries', value: detail.salaries },
                        { name: 'Programs', value: detail.programs },
                        { name: 'Capital', value: detail.capital_projects },
                        { name: 'Grants', value: detail.grants },
                      ]}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                    >
                      {['#00CED1', '#FCD116', '#3b82f6', '#10b981'].map((color, idx) => (
                        <Cell key={color} fill={color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number) => formatCurrency(value, true)}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </motion.div>

            {/* Historical allocation */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-xl border border-gray-200 p-6"
            >
              <h2 className="text-lg font-semibold text-gray-900 mb-1">
                Health spending over time
              </h2>
              <p className="text-sm text-gray-500 mb-4">
                Total allocation for the Ministry of Health &amp; Wellness across recent budgets.
              </p>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={detail.historical}>
                    <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                    <YAxis
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v) =>
                        `$${(v / 1_000_000).toFixed(0)}M`
                      }
                    />
                    <Tooltip
                      formatter={(value: number) => formatCurrency(value, true)}
                    />
                    <Bar
                      dataKey="allocation"
                      fill="#00CED1"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </motion.div>
          </div>

          {/* Line items */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl border border-gray-200 p-6 mb-8"
          >
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Key health programmes and services
            </h2>
            <div className="space-y-2">
              {detail.line_items.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0"
                >
                  <p className="text-sm text-gray-700">{item.name}</p>
                  <p className="font-medium text-gray-900 tabular-nums">
                    {formatCurrency(item.amount, true)}
                  </p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Health projects across islands */}
          {healthProjects.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-xl border border-gray-200 p-6 mb-8"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">
                  Health projects across islands
                </h2>
                <p className="text-xs text-gray-500">
                  Total capital across listed projects:{' '}
                  <span className="font-semibold text-gray-900">
                    {formatCurrency(totalHealthProjectsAmount, true)}
                  </span>
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {healthProjects.map((project) => (
                  <div
                    key={`${project.islandId}-${project.name}`}
                    className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 border border-gray-100"
                  >
                    <div className="w-8 h-8 rounded-full bg-turquoise/10 flex items-center justify-center flex-shrink-0">
                      <MapPin className="w-4 h-4 text-turquoise" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900">
                        {project.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {project.islandName}
                      </p>
                    </div>
                    <p className="text-sm font-medium text-gray-900 tabular-nums">
                      {formatCurrency(project.amount, true)}
                    </p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Source */}
          <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500 mb-8">
            <FileText className="w-4 h-4" />
            <span>
              Source: {detail.source_document}, page {detail.source_page}
            </span>
          </div>

          {/* Ask section */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="mt-4"
          >
            <p className="text-sm text-gray-600 mb-2">
              Have a question about health spending or projects? Ask below.
            </p>
            <AskBar onAsk={handleAsk} />
          </motion.div>
        </>
      )}
    </div>
  );
}

