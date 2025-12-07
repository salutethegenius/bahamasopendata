'use client';

import { useState } from 'react';
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

// Mock data for demonstration
const budgetSummary = {
  fiscal_year: "2024/25",
  total_revenue: 2_850_000_000,
  total_expenditure: 3_200_000_000,
  deficit_surplus: -350_000_000,
  national_debt: 11_500_000_000,
  debt_to_gdp_ratio: 82.5,
  revenue_change_yoy: 5.2,
  expenditure_change_yoy: 3.8,
  source_document: "Budget Communication 2024-25.pdf",
  source_page: 12,
};

const ministries: Ministry[] = [
  { id: "education", name: "Ministry of Education", allocation: 450_000_000, previous_year_allocation: 420_000_000, change_percent: 7.1, sparkline: [380, 395, 410, 420, 450], sector: "Education" },
  { id: "health", name: "Ministry of Health", allocation: 380_000_000, previous_year_allocation: 350_000_000, change_percent: 8.6, sparkline: [310, 325, 340, 350, 380], sector: "Health" },
  { id: "national-security", name: "Ministry of National Security", allocation: 320_000_000, previous_year_allocation: 310_000_000, change_percent: 3.2, sparkline: [280, 290, 300, 310, 320], sector: "Security" },
  { id: "works", name: "Ministry of Works", allocation: 280_000_000, previous_year_allocation: 250_000_000, change_percent: 12.0, sparkline: [200, 220, 235, 250, 280], sector: "Infrastructure" },
];

const sectorData = [
  { name: "Education", value: 450_000_000, color: "#00CED1" },
  { name: "Health", value: 380_000_000, color: "#FCD116" },
  { name: "Security", value: 320_000_000, color: "#3b82f6" },
  { name: "Infrastructure", value: 280_000_000, color: "#10b981" },
  { name: "Finance", value: 250_000_000, color: "#f59e0b" },
  { name: "Other", value: 520_000_000, color: "#8b5cf6" },
];

const historicalData = [
  { year: "2020/21", revenue: 2.1, expenditure: 3.2, debt: 10.2 },
  { year: "2021/22", revenue: 2.4, expenditure: 3.1, debt: 10.8 },
  { year: "2022/23", revenue: 2.65, expenditure: 3.05, debt: 11.1 },
  { year: "2023/24", revenue: 2.75, expenditure: 3.1, debt: 11.3 },
  { year: "2024/25", revenue: 2.85, expenditure: 3.2, debt: 11.5 },
];

// Mock ask function
const handleAsk = async (question: string): Promise<AskResponse> => {
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  if (question.toLowerCase().includes('education') || question.toLowerCase().includes('school')) {
    return {
      answer: "The Ministry of Education received a total allocation of $450 million in the 2024/25 fiscal year. This represents a 7.1% increase from the previous year.",
      numbers: { total_allocation: 450_000_000, change_yoy_percent: 7.1 },
      chart_data: [
        { year: "2020/21", amount: 380_000_000 },
        { year: "2021/22", amount: 395_000_000 },
        { year: "2022/23", amount: 410_000_000 },
        { year: "2023/24", amount: 420_000_000 },
        { year: "2024/25", amount: 450_000_000 },
      ],
      citations: [{ document: "Budget Book 2024-25.pdf", page: 87, snippet: "Ministry of Education - Total Allocation: $450,000,000", url: null }],
      confidence: 0.95,
    };
  }
  
  return {
    answer: "The national debt stands at $11.5 billion as of fiscal year 2024/25, representing 82.5% of GDP.",
    numbers: { total_debt: 11_500_000_000, debt_to_gdp: 82.5 },
    chart_data: null,
    citations: [{ document: "Debt Report 2024-25.pdf", page: 5, snippet: "Total National Debt: $11.5B", url: null }],
    confidence: 0.92,
  };
};

export default function Home() {
  const [selectedMinistry, setSelectedMinistry] = useState<string | null>(null);

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
          <span>Fiscal Year 2024/25</span>
          <span className="mx-2">•</span>
          <FileText className="w-4 h-4" />
          <span>Last updated: December 2024</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
          Bahamas <span className="text-turquoise">Open Data</span>
        </h1>
        <p className="text-gray-600 max-w-2xl">
          Real-time insights into the Bahamas national budget. See where your money goes, 
          track trends, and ask questions about government spending.
        </p>
      </motion.div>

      {/* Key Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Budget"
          value={budgetSummary.total_expenditure}
          subtitle="Fiscal Year 2024/25"
          sourceDocument={budgetSummary.source_document}
          sourcePage={budgetSummary.source_page}
        />
        <StatCard
          title="Revenue"
          value={budgetSummary.total_revenue}
          change={budgetSummary.revenue_change_yoy}
          sourceDocument={budgetSummary.source_document}
        />
        <StatCard
          title="National Debt"
          value={budgetSummary.national_debt}
          subtitle={`${budgetSummary.debt_to_gdp_ratio}% of GDP`}
          sourceDocument="Debt Report 2024-25.pdf"
        />
        <StatCard
          title="Deficit"
          value={Math.abs(budgetSummary.deficit_surplus)}
          subtitle="Expenditure exceeds revenue"
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
              onClick={() => setSelectedMinistry(ministry.id)}
            />
          ))}
        </div>
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
            <p className="text-sm text-gray-500 mb-1">Total Debt</p>
            <p className="text-3xl font-bold text-gray-900 tabular-nums">
              {formatCurrency(11_500_000_000, true)}
            </p>
            <p className="text-sm text-gray-500 mt-1">82.5% of GDP</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">Domestic</p>
            <p className="text-2xl font-bold text-turquoise tabular-nums">
              {formatCurrency(6_200_000_000, true)}
            </p>
            <p className="text-sm text-gray-500 mt-1">53.9% of total</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">External</p>
            <p className="text-2xl font-bold text-yellow-600 tabular-nums">
              {formatCurrency(5_300_000_000, true)}
            </p>
            <p className="text-sm text-gray-500 mt-1">46.1% of total</p>
          </div>
        </div>
        <div className="mt-6 h-3 bg-gray-100 rounded-full overflow-hidden flex">
          <div className="bg-turquoise h-full" style={{ width: '53.9%' }}></div>
          <div className="bg-yellow h-full" style={{ width: '46.1%' }}></div>
        </div>
        <div className="flex justify-between mt-2 text-xs text-gray-500">
          <span>Domestic Bonds & Bills</span>
          <span>External Loans</span>
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
            All figures are sourced from official Bahamas Government documents including the 
            Budget Communication, Budget Book, and Central Bank reports. Each data point links 
            to its source document. This dashboard is updated as new official documents are published.
          </p>
        </div>
      </motion.div>

      {/* Ask Bar */}
      <AskBar onAsk={handleAsk} />
    </div>
  );
}
