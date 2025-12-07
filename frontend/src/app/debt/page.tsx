'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import StatCard from '@/components/StatCard';
import { formatCurrency, formatPercent } from '@/lib/format';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, CartesianGrid, Legend,
  AreaChart, Area
} from 'recharts';
import { TrendingUp, TrendingDown, FileText, AlertTriangle, Building2, Globe } from 'lucide-react';

const creditors = [
  { name: "Domestic Government Bonds", category: "domestic", amount: 4_500_000_000, percent: 39.1, color: "#00CED1" },
  { name: "Domestic Treasury Bills", category: "domestic", amount: 1_700_000_000, percent: 14.8, color: "#4FE0E3" },
  { name: "Inter-American Development Bank", category: "multilateral", amount: 1_800_000_000, percent: 15.7, color: "#FCD116" },
  { name: "International Monetary Fund", category: "multilateral", amount: 400_000_000, percent: 3.5, color: "#FFE04A" },
  { name: "Caribbean Development Bank", category: "multilateral", amount: 350_000_000, percent: 3.0, color: "#3b82f6" },
  { name: "People's Republic of China", category: "bilateral", amount: 580_000_000, percent: 5.0, color: "#10b981" },
  { name: "Commercial Banks", category: "commercial", amount: 1_200_000_000, percent: 10.4, color: "#f59e0b" },
  { name: "Other External", category: "commercial", amount: 970_000_000, percent: 8.5, color: "#8b5cf6" },
];

const repaymentSchedule = [
  { year: "2024/25", principal: 450, interest: 580, total: 1030 },
  { year: "2025/26", principal: 520, interest: 560, total: 1080 },
  { year: "2026/27", principal: 580, interest: 540, total: 1120 },
  { year: "2027/28", principal: 650, interest: 510, total: 1160 },
  { year: "2028/29", principal: 720, interest: 480, total: 1200 },
];

const historicalDebt = [
  { year: "2015/16", total: 6.8, domestic: 3.8, external: 3.0, gdpRatio: 62.5 },
  { year: "2016/17", total: 7.2, domestic: 4.0, external: 3.2, gdpRatio: 65.0 },
  { year: "2017/18", total: 7.6, domestic: 4.2, external: 3.4, gdpRatio: 67.5 },
  { year: "2018/19", total: 8.1, domestic: 4.5, external: 3.6, gdpRatio: 70.0 },
  { year: "2019/20", total: 8.5, domestic: 4.7, external: 3.8, gdpRatio: 72.0 },
  { year: "2020/21", total: 10.2, domestic: 5.5, external: 4.7, gdpRatio: 85.0 },
  { year: "2021/22", total: 10.8, domestic: 5.8, external: 5.0, gdpRatio: 84.0 },
  { year: "2022/23", total: 11.1, domestic: 6.0, external: 5.1, gdpRatio: 83.0 },
  { year: "2023/24", total: 11.3, domestic: 6.1, external: 5.2, gdpRatio: 82.8 },
  { year: "2024/25", total: 11.5, domestic: 6.2, external: 5.3, gdpRatio: 82.5 },
];

const COLORS = ['#00CED1', '#4FE0E3', '#FCD116', '#FFE04A', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'];

export default function DebtPage() {
  const [view, setView] = useState<'overview' | 'creditors' | 'schedule' | 'historical'>('overview');

  const domesticTotal = creditors.filter(c => c.category === 'domestic').reduce((sum, c) => sum + c.amount, 0);
  const externalTotal = creditors.filter(c => c.category !== 'domestic').reduce((sum, c) => sum + c.amount, 0);
  const totalDebt = domesticTotal + externalTotal;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          National <span className="text-turquoise">Debt</span>
        </h1>
        <p className="text-gray-600">
          A clear, honest view of the nation's debt — domestic and external obligations.
        </p>
      </motion.div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total National Debt"
          value={11_500_000_000}
          change={1.8}
          sourceDocument="Debt Report 2024-25.pdf"
        />
        <StatCard
          title="Debt to GDP"
          value={82.5}
          format="percent"
          change={-0.3}
          subtitle="Improving trend"
        />
        <StatCard
          title="Annual Interest"
          value={580_000_000}
          subtitle="Cost of servicing debt"
        />
        <StatCard
          title="5-Year Repayment"
          value={5_590_000_000}
          subtitle="Principal + Interest"
        />
      </div>

      {/* View Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        {['overview', 'creditors', 'schedule', 'historical'].map((v) => (
          <button
            key={v}
            onClick={() => setView(v as typeof view)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize whitespace-nowrap transition-colors ${
              view === v 
                ? 'bg-turquoise text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {v}
          </button>
        ))}
      </div>

      {/* Overview */}
      {view === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Debt Split */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Domestic vs External</h3>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-turquoise/10 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Building2 className="w-5 h-5 text-turquoise" />
                  <span className="text-sm font-medium text-gray-600">Domestic</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(domesticTotal, true)}</p>
                <p className="text-sm text-gray-500">53.9% of total</p>
              </div>
              <div className="bg-yellow/10 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Globe className="w-5 h-5 text-yellow-600" />
                  <span className="text-sm font-medium text-gray-600">External</span>
                </div>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(externalTotal, true)}</p>
                <p className="text-sm text-gray-500">46.1% of total</p>
              </div>
            </div>
            <div className="h-4 bg-gray-100 rounded-full overflow-hidden flex">
              <div className="bg-turquoise h-full" style={{ width: '53.9%' }}></div>
              <div className="bg-yellow h-full" style={{ width: '46.1%' }}></div>
            </div>
          </motion.div>

          {/* GDP Ratio Trend */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Debt-to-GDP Ratio</h3>
              <div className="flex items-center gap-1 text-green-600 text-sm">
                <TrendingDown className="w-4 h-4" />
                <span>Improving</span>
              </div>
            </div>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={historicalDebt.slice(-5)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                  <YAxis domain={[75, 90]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(value: number) => `${value}%`} />
                  <Area 
                    type="monotone" 
                    dataKey="gdpRatio" 
                    stroke="#00CED1" 
                    fill="#00CED1" 
                    fillOpacity={0.2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 p-3 bg-amber-50 rounded-lg flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-amber-800">
                Debt-to-GDP peaked at 85% in 2020/21 due to COVID-19. The ratio has been 
                gradually declining as the economy recovers.
              </p>
            </div>
          </motion.div>
        </div>
      )}

      {/* Creditors */}
      {view === 'creditors' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Creditor Distribution</h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={creditors}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    dataKey="amount"
                  >
                    {creditors.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => formatCurrency(value, true)} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">By Creditor</h3>
            <div className="space-y-3 max-h-[350px] overflow-y-auto">
              {creditors.map((creditor, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div 
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: creditor.color }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-baseline">
                      <span className="text-sm text-gray-700 truncate">{creditor.name}</span>
                      <span className="text-sm font-medium text-gray-900 tabular-nums ml-2">
                        {formatCurrency(creditor.amount, true)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 capitalize">
                        {creditor.category}
                      </span>
                      <span className="text-xs text-gray-400">
                        {creditor.percent}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      )}

      {/* Repayment Schedule */}
      {view === 'schedule' && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-xl border border-gray-200 p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">5-Year Repayment Schedule (Millions)</h3>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={repaymentSchedule}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="year" />
                <YAxis tickFormatter={(v) => `$${v}M`} />
                <Tooltip formatter={(value: number) => `$${value}M`} />
                <Legend />
                <Bar dataKey="principal" name="Principal" fill="#00CED1" stackId="a" />
                <Bar dataKey="interest" name="Interest" fill="#FCD116" stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-4 text-center">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-sm text-gray-500">Total Principal</p>
              <p className="text-lg font-bold text-turquoise">$2.92B</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-sm text-gray-500">Total Interest</p>
              <p className="text-lg font-bold text-yellow-600">$2.67B</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-sm text-gray-500">Total Repayment</p>
              <p className="text-lg font-bold text-gray-900">$5.59B</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Historical */}
      {view === 'historical' && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-xl border border-gray-200 p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">10-Year Debt History (Billions)</h3>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historicalDebt}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                <YAxis tickFormatter={(v) => `$${v}B`} />
                <Tooltip formatter={(value: number) => `$${value}B`} />
                <Legend />
                <Line type="monotone" dataKey="total" name="Total Debt" stroke="#00CED1" strokeWidth={3} dot={{ fill: '#00CED1' }} />
                <Line type="monotone" dataKey="domestic" name="Domestic" stroke="#3b82f6" strokeWidth={2} />
                <Line type="monotone" dataKey="external" name="External" stroke="#FCD116" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      )}

      {/* Source */}
      <div className="mt-6 flex items-center gap-2 text-sm text-gray-500">
        <FileText className="w-4 h-4" />
        <span>Source: Debt Report 2024-25.pdf, Central Bank Quarterly Bulletin</span>
      </div>
    </div>
  );
}

