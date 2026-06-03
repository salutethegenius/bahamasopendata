'use client';

import { useEffect, useMemo, useState, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { X, FileText, TrendingUp, Users, Building, Wallet, AlertCircle } from 'lucide-react';

import MinistryCard from '@/components/MinistryCard';
import FiscalYearSelector from '@/components/FiscalYearSelector';
import ResponsiveContainer from '@/components/SafeResponsiveContainer';
import { Ministry, MinistryDetail } from '@/types';
import { formatCurrency, formatPercent } from '@/lib/format';
import { fiscalYearSearchParam, useFiscalYear } from '@/lib/fiscal-year';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

const CHART_COLORS = ['#00CED1', '#FCD116', '#3b82f6', '#10b981'];
const HISTORY_YEARS = ['2022/23', '2023/24', '2024/25', '2025/26'];

function createFallbackDetail(ministry: Ministry): MinistryDetail {
  return {
    id: ministry.id,
    name: ministry.name,
    allocation: ministry.allocation,
    salaries: 0,
    programs: 0,
    capital_projects: 0,
    grants: 0,
    line_items: [],
    historical: ministry.sparkline.map((value, index) => ({
      year: HISTORY_YEARS[index] ?? `Year ${index + 1}`,
      allocation: value * 1_000_000,
    })),
    source_document: 'Published ministry allocation',
    source_page: 0,
  };
}

function MinistriesPageContent() {
  const { fiscalYear } = useFiscalYear();
  const [selectedMinistry, setSelectedMinistry] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'allocation' | 'change'>('allocation');
  const [ministries, setMinistries] = useState<Ministry[]>([]);
  const [ministryDetails, setMinistryDetails] = useState<Record<string, MinistryDetail>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMinistries = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const fy = fiscalYearSearchParam(fiscalYear);
        const response = await fetch(`${API_BASE}/ministries${fy}`);
        if (!response.ok) {
          throw new Error('Failed to load ministry allocations.');
        }

        const payload: Ministry[] = await response.json();
        if (!Array.isArray(payload) || payload.length === 0) {
          throw new Error('No published ministry data is available yet.');
        }

        setMinistries(payload);
        setSelectedMinistry((current) => current ?? payload[0]?.id ?? null);

        const detailEntries = await Promise.all(
          payload.map(async (ministry) => {
            try {
              const detailResponse = await fetch(
                `${API_BASE}/ministries/${ministry.id}${fy}`,
              );
              if (!detailResponse.ok) {
                return [ministry.id, createFallbackDetail(ministry)] as const;
              }

              const detailPayload: MinistryDetail = await detailResponse.json();
              return [ministry.id, detailPayload] as const;
            } catch {
              return [ministry.id, createFallbackDetail(ministry)] as const;
            }
          }),
        );

        setMinistryDetails(Object.fromEntries(detailEntries));
      } catch (fetchError) {
        setError(
          fetchError instanceof Error
            ? fetchError.message
            : 'Unexpected error loading ministries.',
        );
      } finally {
        setIsLoading(false);
      }
    };

    void fetchMinistries();
  }, [fiscalYear]);

  const filteredMinistries = useMemo(() => {
    return ministries
      .filter((ministry) =>
        ministry.name.toLowerCase().includes(searchTerm.toLowerCase()),
      )
      .sort((a, b) =>
        sortBy === 'allocation'
          ? b.allocation - a.allocation
          : b.change_percent - a.change_percent,
      );
  }, [ministries, searchTerm, sortBy]);

  const totalAllocation = useMemo(
    () => ministries.reduce((sum, ministry) => sum + ministry.allocation, 0),
    [ministries],
  );

  const averageChange = ministries.length
    ? ministries.reduce((sum, ministry) => sum + ministry.change_percent, 0) /
      ministries.length
    : 0;

  const selectedMinistryData = selectedMinistry
    ? ministries.find((ministry) => ministry.id === selectedMinistry) ?? null
    : null;

  const selectedDetail = selectedMinistryData
    ? ministryDetails[selectedMinistryData.id] ?? createFallbackDetail(selectedMinistryData)
    : null;

  const breakdownData = selectedDetail
    ? [
        { name: 'Salaries', value: selectedDetail.salaries },
        { name: 'Programs', value: selectedDetail.programs },
        { name: 'Capital', value: selectedDetail.capital_projects },
        { name: 'Grants', value: selectedDetail.grants },
      ]
    : [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Ministry <span className="text-turquoise">Allocations</span>
          </h1>
          <p className="text-gray-600">
            Explore published budget allocations for government ministries and departments.
          </p>
        </div>
        <FiscalYearSelector />
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
            <p className="font-semibold text-red-800">Could not load ministries</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {!isLoading && !error && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-gray-500">Total Ministries</p>
              <p className="text-2xl font-bold text-gray-900">{ministries.length}</p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-gray-500">Total Allocation</p>
              <p className="text-2xl font-bold text-turquoise">
                {formatCurrency(totalAllocation, true)}
              </p>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-gray-500">Average YoY Change</p>
              <p
                className={`text-2xl font-bold ${
                  averageChange >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {averageChange >= 0 ? '+' : ''}
                {formatPercent(averageChange)}
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <input
              type="text"
              placeholder="Search ministries..."
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              className="flex-1 px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-turquoise focus:border-transparent"
            />
            <div className="flex gap-2">
              <button
                onClick={() => setSortBy('allocation')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  sortBy === 'allocation'
                    ? 'bg-turquoise text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                By Allocation
              </button>
              <button
                onClick={() => setSortBy('change')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  sortBy === 'change'
                    ? 'bg-turquoise text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                By Change
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredMinistries.map((ministry, index) => (
              <MinistryCard
                key={ministry.id}
                ministry={ministry}
                index={index}
                onClick={() => setSelectedMinistry(ministry.id)}
              />
            ))}
          </div>

          <AnimatePresence>
            {selectedDetail && selectedMinistryData && (
              <>
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  onClick={() => setSelectedMinistry(null)}
                  className="fixed inset-0 bg-black/50 z-50"
                />
                <motion.div
                  initial={{ x: '100%' }}
                  animate={{ x: 0 }}
                  exit={{ x: '100%' }}
                  transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                  className="fixed top-0 right-0 bottom-0 w-full max-w-lg bg-white z-50 overflow-y-auto shadow-2xl"
                >
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-6">
                      <div>
                        <p className="text-sm font-medium text-turquoise uppercase tracking-wide mb-1">
                          {selectedMinistryData.sector || 'Ministry'}
                        </p>
                        <h2 className="text-2xl font-bold text-gray-900">
                          {selectedDetail.name}
                        </h2>
                      </div>
                      <button
                        onClick={() => setSelectedMinistry(null)}
                        className="p-2 hover:bg-gray-100 rounded-full"
                      >
                        <X className="w-5 h-5 text-gray-500" />
                      </button>
                    </div>

                    <div className="bg-turquoise/10 rounded-xl p-4 mb-6">
                      <p className="text-sm text-turquoise font-medium">
                        Total Allocation
                      </p>
                      <p className="text-3xl font-bold text-gray-900">
                        {formatCurrency(selectedDetail.allocation, true)}
                      </p>
                      <p
                        className={`text-sm mt-1 ${
                          selectedMinistryData.change_percent >= 0
                            ? 'text-green-600'
                            : 'text-red-600'
                        }`}
                      >
                        {selectedMinistryData.change_percent >= 0 ? '+' : ''}
                        {formatPercent(selectedMinistryData.change_percent)} from last year
                      </p>
                    </div>

                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Budget Breakdown
                      </h3>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="bg-gray-50 rounded-lg p-3">
                          <Users className="w-5 h-5 text-turquoise mb-2" />
                          <p className="text-xs text-gray-500">Salaries</p>
                          <p className="font-bold text-gray-900">
                            {formatCurrency(selectedDetail.salaries, true)}
                          </p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-3">
                          <Wallet className="w-5 h-5 text-yellow-500 mb-2" />
                          <p className="text-xs text-gray-500">Programs</p>
                          <p className="font-bold text-gray-900">
                            {formatCurrency(selectedDetail.programs, true)}
                          </p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-3">
                          <Building className="w-5 h-5 text-blue-500 mb-2" />
                          <p className="text-xs text-gray-500">Capital Projects</p>
                          <p className="font-bold text-gray-900">
                            {formatCurrency(selectedDetail.capital_projects, true)}
                          </p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-3">
                          <TrendingUp className="w-5 h-5 text-green-500 mb-2" />
                          <p className="text-xs text-gray-500">Grants</p>
                          <p className="font-bold text-gray-900">
                            {formatCurrency(selectedDetail.grants, true)}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="mb-6">
                      <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={breakdownData}
                              cx="50%"
                              cy="50%"
                              innerRadius={40}
                              outerRadius={70}
                              dataKey="value"
                            >
                              {breakdownData.map((_, index) => (
                                <Cell
                                  key={`cell-${index}`}
                                  fill={CHART_COLORS[index % CHART_COLORS.length]}
                                />
                              ))}
                            </Pie>
                            <Tooltip
                              formatter={(value: number) =>
                                formatCurrency(value, true)
                              }
                            />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Line Items
                      </h3>
                      {selectedDetail.line_items.length ? (
                        <div className="space-y-2">
                          {selectedDetail.line_items.map((item, index) => (
                            <div
                              key={`${item.name}-${index}`}
                              className="flex justify-between items-center py-2 border-b border-gray-100"
                            >
                              <span className="text-gray-700">{item.name}</span>
                              <span className="font-medium text-gray-900 tabular-nums">
                                {formatCurrency(item.amount, true)}
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">
                          No detailed line items were published for this ministry yet.
                        </p>
                      )}
                    </div>

                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Historical Allocation
                      </h3>
                      <div className="h-40">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={selectedDetail.historical}>
                            <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                            <YAxis
                              tick={{ fontSize: 11 }}
                              tickFormatter={(value) =>
                                `$${(value / 1_000_000).toFixed(0)}M`
                              }
                            />
                            <Tooltip
                              formatter={(value: number) =>
                                formatCurrency(value, true)
                              }
                            />
                            <Bar
                              dataKey="allocation"
                              fill="#00CED1"
                              radius={[4, 4, 0, 0]}
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    <div className="border-t border-gray-200 pt-4">
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <FileText className="w-4 h-4" />
                        <span>
                          {selectedDetail.source_document}
                          {selectedDetail.source_page
                            ? `, page ${selectedDetail.source_page}`
                            : ''}
                        </span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>
        </>
      )}
    </div>
  );
}

export default function MinistriesPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-4" />
            <div className="h-4 bg-gray-200 rounded w-1/2" />
          </div>
        </div>
      }
    >
      <MinistriesPageContent />
    </Suspense>
  );
}
