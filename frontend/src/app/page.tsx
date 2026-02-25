'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import StatCard from '@/components/StatCard';
import SectorPieChart from '@/components/SectorPieChart';
import MinistryCard from '@/components/MinistryCard';
import AskBar from '@/components/AskBar';
import { formatCurrency } from '@/lib/format';
import { Ministry, AskResponse } from '@/types';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend
} from 'recharts';
import { TrendingUp, Calendar, FileText, AlertCircle } from 'lucide-react';

// Real data from Bahamas Budget 2025/26
const budgetSummary = {
  fiscal_year: "2025/26",
  total_revenue: 3_896_324_553,
  total_expenditure: 3_820_844_050,
  recurrent_expenditure: 3_444_518_797,
  capital_expenditure: 376_325_253,
  deficit_surplus: 75_480_503,  // SURPLUS - First balanced budget in independent Bahamas!
  national_debt: 11_386_500_000,
  debt_to_gdp_ratio: 68.9,
  gdp: 16_525_700_000,
  source_document: "Bahamas BudgetFINAL_2025-2026_.pdf",
  source_page: 34,
};

// Real ministry allocations from Budget Book 2025/26 (Pages 71-72)
const ministries: Ministry[] = [
  { id: "health", name: "Ministry of Health & Wellness", allocation: 355_119_623, previous_year_allocation: 332_747_117, change_percent: 6.7, sparkline: [288.4, 263.2, 332.7, 355.1], sector: "Health" },
  { id: "finance", name: "Ministry of Finance", allocation: 362_694_099, previous_year_allocation: 346_639_187, change_percent: 4.6, sparkline: [177.5, 178.8, 346.6, 362.7], sector: "Finance" },
  { id: "education", name: "Ministry of Education", allocation: 137_052_342, previous_year_allocation: 123_252_555, change_percent: 11.2, sparkline: [114.7, 91.4, 123.3, 137.1], sector: "Education" },
  { id: "police", name: "Royal Bahamas Police Force", allocation: 134_036_300, previous_year_allocation: 126_644_406, change_percent: 5.8, sparkline: [126.5, 100.9, 126.6, 134.0], sector: "Security" },
];

// Real sector breakdown from Budget 2025/26
const sectorData = [
  { name: "Public Debt Service", value: 689_545_978, color: "#ef4444" },
  { name: "Health", value: 477_596_494, color: "#FCD116" },
  { name: "Education", value: 353_413_898, color: "#00CED1" },
  { name: "Security", value: 231_980_608, color: "#3b82f6" },
  { name: "Tourism", value: 123_395_161, color: "#8b5cf6" },
  { name: "Social Services", value: 72_243_034, color: "#10b981" },
  { name: "Other", value: 1_496_343_624, color: "#6b7280" },
];

// Real historical data from Fiscal Summary (Page 34)
const historicalData = [
  { year: "2020/21", revenue: 1.91, expenditure: 3.24, debt: 9.93, debt_gdp: 88.7 },
  { year: "2021/22", revenue: 2.61, expenditure: 3.33, debt: 10.79, debt_gdp: 83.2 },
  { year: "2022/23", revenue: 2.85, expenditure: 3.39, debt: 11.26, debt_gdp: 77.2 },
  { year: "2023/24", revenue: 3.07, expenditure: 3.26, debt: 11.31, debt_gdp: 72.7 },
  { year: "2024/25", revenue: 3.54, expenditure: 3.61, debt: 11.46, debt_gdp: 71.4 },
  { year: "2025/26", revenue: 3.89, expenditure: 3.82, debt: 11.39, debt_gdp: 68.9 },
];

// Budget priorities from Budget Communication
const budgetPriorities = [
  { name: "Security", description: "National security and personal safety", icon: "🛡️" },
  { name: "Opportunity", description: "Growing the economy and investing in people", icon: "📈" },
  { name: "Affordability", description: "Combating inflation and lowering prices", icon: "💰" },
  { name: "Reform", description: "Fiscal discipline and modernizing government", icon: "⚙️" },
];

// Real API ask function - lazy load to avoid SSR issues
const handleAsk = async (question: string): Promise<AskResponse> => {
  try {
    // Dynamically import to avoid SSR issues
    const { askQuestion } = await import('@/lib/api');
    return await askQuestion(question);
  } catch (error) {
    console.error('Failed to get answer:', error);
    // Return a user-friendly error response
    return {
      answer: error instanceof Error 
        ? error.message 
        : "I'm having trouble connecting to the answer service. Please check your connection and try again.",
      numbers: null,
      chart_data: null,
      citations: [],
      confidence: 0.0,
    };
  }
};

export default function Home() {
  const router = useRouter();

  const handleMinistryClick = (ministryId: string) => {
    // #region agent log
    fetch('http://localhost:7242/ingest/9b91e0da-2b25-4d4b-8286-9d38d86a8b2c', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        location: 'page.tsx:79',
        message: 'Ministry card clicked',
        data: { ministryId },
        timestamp: Date.now(),
        sessionId: 'debug-session',
        runId: 'run1',
        hypothesisId: 'A'
      })
    }).catch(() => {});
    // #endregion agent log
    
    // Navigate to ministries page with query parameter
    router.push(`/ministries?ministry=${ministryId}`);
    
    // #region agent log
    fetch('http://localhost:7242/ingest/9b91e0da-2b25-4d4b-8286-9d38d86a8b2c', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        location: 'page.tsx:88',
        message: 'Navigation triggered',
        data: { url: `/ministries?ministry=${ministryId}` },
        timestamp: Date.now(),
        sessionId: 'debug-session',
        runId: 'run1',
        hypothesisId: 'B'
      })
    }).catch(() => {});
    // #endregion agent log
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <Calendar className="w-4 h-4" />
          <span>Fiscal Year 2025/26</span>
          <span className="mx-2">•</span>
          <FileText className="w-4 h-4" />
          <span>Last updated: May 28, 2025</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
          Bahamas <span className="text-turquoise">Open Data</span>
        </h1>
        <p className="text-gray-600 max-w-2xl">
          Real-time insights into the Bahamas national budget. See where your money goes, 
          track trends, and ask questions about government spending.
        </p>
        {/* Historic Milestone Banner */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="mt-4 bg-gradient-to-r from-turquoise/10 to-yellow/10 border border-turquoise/20 rounded-lg p-4"
        >
          <div className="flex items-center gap-3">
            <TrendingUp className="w-6 h-6 text-turquoise" />
            <div>
              <p className="font-semibold text-gray-900">🎉 Historic First: Balanced Budget with Surplus</p>
              <p className="text-sm text-gray-600">For the first time since Independence, The Bahamas has achieved a budget surplus of $75.5M</p>
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Key Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Budget"
          value={budgetSummary.total_expenditure}
          subtitle="Fiscal Year 2025/26"
          sourceDocument={budgetSummary.source_document}
          sourcePage={budgetSummary.source_page}
        />
        <StatCard
          title="Revenue"
          value={budgetSummary.total_revenue}
          subtitle="Projected for FY2025/26"
          sourceDocument={budgetSummary.source_document}
        />
        <StatCard
          title="National Debt"
          value={budgetSummary.national_debt}
          subtitle={`${budgetSummary.debt_to_gdp_ratio}% of GDP (down from 88.7%)`}
          sourceDocument={budgetSummary.source_document}
        />
        <StatCard
          title="Budget Surplus"
          value={budgetSummary.deficit_surplus}
          subtitle="First surplus since Independence! 🎉"
          sourceDocument={budgetSummary.source_document}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Sector Breakdown */}
        <SectorPieChart data={sectorData} title="Where the Money Goes" />

        {/* Trend Chart */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-xl border border-gray-200 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Budget Trends</h3>
            <div className="flex items-center gap-4 text-sm">
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-turquoise"></span>
                Revenue
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-yellow"></span>
                Expenditure
              </span>
            </div>
          </div>
          <div className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historicalData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                <YAxis 
                  tick={{ fontSize: 12 }} 
                  tickFormatter={(v) => `$${v}B`}
                />
                <Tooltip 
                  formatter={(value: number) => [`$${value}B`, '']}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="revenue" 
                  stroke="#00CED1" 
                  strokeWidth={2}
                  dot={{ fill: '#00CED1' }}
                  name="Revenue"
                />
                <Line 
                  type="monotone" 
                  dataKey="expenditure" 
                  stroke="#FCD116" 
                  strokeWidth={2}
                  dot={{ fill: '#FCD116' }}
                  name="Expenditure"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Ministry Tiles */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Top Ministries</h2>
          <a href="/ministries" className="text-turquoise text-sm font-medium hover:underline">
            View all ministries →
          </a>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {ministries.map((ministry, index) => (
            <MinistryCard
              key={ministry.id}
              ministry={ministry}
              index={index}
              onClick={() => handleMinistryClick(ministry.id)}
            />
          ))}
        </div>
      </motion.div>

      {/* Budget Priorities - SOAR Framework */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.25 }}
        className="bg-white rounded-xl border border-gray-200 p-6 mb-8"
      >
        <h2 className="text-xl font-bold text-gray-900 mb-4">Budget Priorities: SOAR Framework</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {budgetPriorities.map((priority, idx) => (
            <div key={idx} className="text-center p-4 bg-gray-50 rounded-lg">
              <span className="text-3xl mb-2 block">{priority.icon}</span>
              <h3 className="font-semibold text-gray-900">{priority.name}</h3>
              <p className="text-xs text-gray-500 mt-1">{priority.description}</p>
            </div>
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-4 text-center">Source: Budget Communication 2025/26, Page 7</p>
      </motion.div>

      {/* Debt Overview */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="bg-white rounded-xl border border-gray-200 p-6 mb-8"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">Debt Overview</h2>
          <a href="/debt" className="text-turquoise text-sm font-medium hover:underline">
            View full breakdown →
          </a>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-500 mb-1">Total Debt (End FY2025/26)</p>
            <p className="text-3xl font-bold text-gray-900 tabular-nums">
              {formatCurrency(11_386_500_000, true)}
            </p>
            <p className="text-sm text-green-600 mt-1">↓ 68.9% of GDP (down from 88.7% in 2021)</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">Interest Payments</p>
            <p className="text-2xl font-bold text-turquoise tabular-nums">
              {formatCurrency(668_045_978, true)}
            </p>
            <p className="text-sm text-gray-500 mt-1">17.2% of revenue</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">Target by 2031</p>
            <p className="text-2xl font-bold text-yellow-600 tabular-nums">
              50% of GDP
            </p>
            <p className="text-sm text-gray-500 mt-1">Investment-grade goal by FY2028/29</p>
          </div>
        </div>
        <div className="mt-6">
          <p className="text-xs text-gray-500 mb-2">Debt-to-GDP Ratio Trajectory</p>
          <div className="h-3 bg-gray-100 rounded-full overflow-hidden flex">
            <div className="bg-turquoise h-full transition-all" style={{ width: '68.9%' }}></div>
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-500">
            <span>0%</span>
            <span>68.9% (2025/26)</span>
            <span>100%</span>
          </div>
        </div>
      </motion.div>

      {/* Info Banner */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="bg-turquoise/10 rounded-xl p-6 flex items-start gap-4"
      >
        <AlertCircle className="w-6 h-6 text-turquoise flex-shrink-0 mt-0.5" />
        <div>
          <h3 className="font-semibold text-gray-900 mb-1">About this data</h3>
          <p className="text-sm text-gray-600">
            All figures are sourced from the official <strong>Bahamas Budget 2025/26</strong> documents 
            presented to Parliament on May 28, 2025 by Prime Minister and Minister of Finance 
            Hon. Philip Edward Davis KC, MP. Data includes the Budget Communication and Budget Book 
            (Draft Estimates of Revenue & Expenditure). Ask questions below to explore more.
          </p>
        </div>
      </motion.div>

      {/* Ask Bar */}
      <AskBar onAsk={handleAsk} />
    </div>
  );
}
