'use client';

import { Suspense, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import StatCard from '@/components/StatCard';
import FiscalYearSelector from '@/components/FiscalYearSelector';
import { formatCurrency, formatPercent } from '@/lib/format';
import { fiscalYearSearchParam, useFiscalYear, CURRENT_FISCAL_YEAR } from '@/lib/fiscal-year';
import { RevenueBreakdown } from '@/types';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip,
  PieChart, Pie, Cell, LineChart, Line, CartesianGrid, Legend
} from 'recharts';
import { TrendingUp, Calendar, FileText } from 'lucide-react';
import ResponsiveContainer from '@/components/SafeResponsiveContainer';

const revenueData = [
  { name: "Value Added Tax (VAT)", amount: 1_100_000_000, percent: 38.6, change: 6.5, color: "#00CED1" },
  { name: "Customs & Import Duties", amount: 650_000_000, percent: 22.8, change: 4.2, color: "#FCD116" },
  { name: "Tourism Taxes & Fees", amount: 420_000_000, percent: 14.7, change: 12.5, color: "#3b82f6" },
  { name: "Business License Fees", amount: 280_000_000, percent: 9.8, change: 3.8, color: "#10b981" },
  { name: "Property Tax", amount: 150_000_000, percent: 5.3, change: 2.1, color: "#f59e0b" },
  { name: "Stamp Tax", amount: 120_000_000, percent: 4.2, change: 1.5, color: "#8b5cf6" },
  { name: "Other Revenue", amount: 130_000_000, percent: 4.6, change: 5.0, color: "#ec4899" },
];

const monthlyData = [
  { month: "Jul", vat: 85, customs: 52, tourism: 35, other: 48 },
  { month: "Aug", vat: 90, customs: 54, tourism: 40, other: 51 },
  { month: "Sep", vat: 92, customs: 55, tourism: 42, other: 56 },
  { month: "Oct", vat: 95, customs: 56, tourism: 45, other: 54 },
  { month: "Nov", vat: 98, customs: 58, tourism: 48, other: 56 },
  { month: "Dec", vat: 105, customs: 62, tourism: 55, other: 58 },
];

const historicalData = [
  { year: "2020/21", total: 2.1, vat: 0.78, customs: 0.52, tourism: 0.28 },
  { year: "2021/22", total: 2.4, vat: 0.90, customs: 0.58, tourism: 0.34 },
  { year: "2022/23", total: 2.65, vat: 1.00, customs: 0.62, tourism: 0.38 },
  { year: "2023/24", total: 2.75, vat: 1.05, customs: 0.64, tourism: 0.40 },
  { year: "2024/25", total: 2.85, vat: 1.10, customs: 0.65, tourism: 0.42 },
];

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

export default function RevenuePage() {
  return (
    <Suspense fallback={<div className="max-w-7xl mx-auto px-4 py-8">Loading revenue…</div>}>
      <RevenuePageContent />
    </Suspense>
  );
}

function RevenuePageContent() {
  const { fiscalYear } = useFiscalYear();
  const [view, setView] = useState<'breakdown' | 'monthly' | 'historical'>('breakdown');
  const [breakdown, setBreakdown] = useState<RevenueBreakdown>({
    fiscal_year: CURRENT_FISCAL_YEAR,
    total_revenue: revenueData.reduce((sum, r) => sum + r.amount, 0),
    sources: revenueData.map((item) => ({
      name: item.name,
      amount: item.amount,
      percent_of_total: item.percent,
      change_yoy: item.change,
    })),
    last_updated: new Date().toISOString(),
    source_document: 'FY2026-27_Draft_Estimates_of_Revenue_and_Expenditure.pdf',
  });
  const [monthly, setMonthly] = useState(monthlyData);
  const [historical, setHistorical] = useState(historicalData);

  useEffect(() => {
    const fetchRevenue = async () => {
      try {
        const fy = fiscalYearSearchParam(fiscalYear);
        const [breakdownRes, monthlyRes, historicalRes] = await Promise.allSettled([
          fetch(`${API_BASE}/revenue${fy}`),
          fetch(`${API_BASE}/revenue/monthly${fy}`),
          fetch(`${API_BASE}/revenue/historical`),
        ]);

        if (breakdownRes.status === 'fulfilled' && breakdownRes.value.ok) {
          setBreakdown(await breakdownRes.value.json());
        }

        if (monthlyRes.status === 'fulfilled' && monthlyRes.value.ok) {
          const payload = await monthlyRes.value.json();
          if (Array.isArray(payload.monthly_data)) {
            setMonthly(
              payload.monthly_data.map((row: Record<string, number | string>) => ({
                month: String(row.month ?? ''),
                vat: Number(row.vat ?? 0),
                customs: Number(row.customs ?? 0),
                tourism: Number(row.tourism ?? 0),
                other: Number(row.other ?? 0),
              })),
            );
          }
        }

        if (historicalRes.status === 'fulfilled' && historicalRes.value.ok) {
          const payload = await historicalRes.value.json();
          if (Array.isArray(payload.years)) {
            setHistorical(
              payload.years.map((row: Record<string, number | string>) => ({
                year: String(row.year ?? ''),
                total: Number(row.total ?? 0) / 1_000_000_000,
                vat: Number(row.vat ?? 0) / 1_000_000_000,
                customs: Number(row.customs ?? 0) / 1_000_000_000,
                tourism: Number(row.tourism ?? 0) / 1_000_000_000,
              })),
            );
          }
        }
      } catch (error) {
        console.error('Failed to load revenue data', error);
      }
    };

    void fetchRevenue();
  }, [fiscalYear]);

  const revenueChartData = breakdown.sources.map((source, index) => ({
    name: source.name,
    amount: source.amount,
    percent: source.percent_of_total,
    change: source.change_yoy,
    color: revenueData[index]?.color ?? "#00CED1",
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Government <span className="text-turquoise">Revenue</span>
          </h1>
          <p className="text-gray-600">
            Where the money comes from — tax collections, fees, and other government income.
          </p>
          <div className="mt-2 flex items-center gap-2 text-sm text-gray-500">
            <Calendar className="w-4 h-4" />
            <span>Fiscal Year {breakdown.fiscal_year}</span>
          </div>
        </div>
        <FiscalYearSelector />
      </motion.div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Revenue"
          value={breakdown.total_revenue}
          change={5.2}
          sourceDocument={breakdown.source_document}
        />
        <StatCard
          title="VAT Collection"
          value={revenueChartData.find((source) => source.name.toLowerCase().includes('vat'))?.amount ?? 0}
          change={revenueChartData.find((source) => source.name.toLowerCase().includes('vat'))?.change ?? 0}
          subtitle={`${revenueChartData.find((source) => source.name.toLowerCase().includes('vat'))?.percent ?? 0}% of total`}
        />
        <StatCard
          title="Tourism Revenue"
          value={revenueChartData.find((source) => source.name.toLowerCase().includes('tour'))?.amount ?? 0}
          change={revenueChartData.find((source) => source.name.toLowerCase().includes('tour'))?.change ?? 0}
          subtitle={`${revenueChartData.find((source) => source.name.toLowerCase().includes('tour'))?.percent ?? 0}% of total`}
        />
        <StatCard
          title="Customs Duties"
          value={revenueChartData.find((source) => source.name.toLowerCase().includes('custom'))?.amount ?? 0}
          change={revenueChartData.find((source) => source.name.toLowerCase().includes('custom'))?.change ?? 0}
          subtitle={`${revenueChartData.find((source) => source.name.toLowerCase().includes('custom'))?.percent ?? 0}% of total`}
        />
      </div>

      {/* View Tabs */}
      <div className="flex gap-2 mb-6">
        {['breakdown', 'monthly', 'historical'].map((v) => (
          <button
            key={v}
            onClick={() => setView(v as typeof view)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
              view === v 
                ? 'bg-turquoise text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {v}
          </button>
        ))}
      </div>

      {/* Content */}
      {view === 'breakdown' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pie Chart */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue Sources</h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={revenueChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="amount"
                  >
                    {revenueChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: number) => formatCurrency(value, true)}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {/* Revenue List */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">By Source</h3>
            <div className="space-y-3">
              {revenueChartData.map((source, i) => (
                <div key={i} className="flex items-center gap-4">
                  <div 
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: source.color }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-baseline">
                      <span className="text-gray-700 truncate">{source.name}</span>
                      <span className="font-medium text-gray-900 tabular-nums ml-2">
                        {formatCurrency(source.amount, true)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center mt-1">
                      <div className="w-full bg-gray-100 rounded-full h-1.5 mr-2">
                        <div 
                          className="h-1.5 rounded-full" 
                          style={{ width: `${source.percent}%`, backgroundColor: source.color }}
                        />
                      </div>
                      <span className={`text-xs font-medium ${source.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercent(source.change)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      )}

      {view === 'monthly' && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-xl border border-gray-200 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Monthly Collection (Millions)</h3>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Calendar className="w-4 h-4" />
              <span>FY {breakdown.fiscal_year}</span>
            </div>
          </div>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthly}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(v) => `$${v}M`} />
                <Tooltip formatter={(value: number) => `$${value}M`} />
                <Legend />
                <Bar dataKey="vat" name="VAT" fill="#00CED1" stackId="a" />
                <Bar dataKey="customs" name="Customs" fill="#FCD116" stackId="a" />
                <Bar dataKey="tourism" name="Tourism" fill="#3b82f6" stackId="a" />
                <Bar dataKey="other" name="Other" fill="#10b981" stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      )}

      {view === 'historical' && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-xl border border-gray-200 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">5-Year Revenue Trend (Billions)</h3>
            <div className="flex items-center gap-2 text-sm text-green-600">
              <TrendingUp className="w-4 h-4" />
              <span>+35.7% since 2020/21</span>
            </div>
          </div>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historical}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="year" />
                <YAxis tickFormatter={(v) => `$${v}B`} />
                <Tooltip formatter={(value: number) => `$${value}B`} />
                <Legend />
                <Line type="monotone" dataKey="total" name="Total" stroke="#00CED1" strokeWidth={3} dot={{ fill: '#00CED1' }} />
                <Line type="monotone" dataKey="vat" name="VAT" stroke="#FCD116" strokeWidth={2} />
                <Line type="monotone" dataKey="customs" name="Customs" stroke="#3b82f6" strokeWidth={2} />
                <Line type="monotone" dataKey="tourism" name="Tourism" stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      )}

      {/* Source */}
      <div className="mt-6 flex items-center gap-2 text-sm text-gray-500">
        <FileText className="w-4 h-4" />
        <span>Source: {breakdown.source_document}</span>
      </div>
    </div>
  );
}
