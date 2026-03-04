'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import StatCard from '@/components/StatCard';
import SectorPieChart from '@/components/SectorPieChart';
import MinistryCard from '@/components/MinistryCard';
import AskBar from '@/components/AskBar';
import DashboardSectionCard from '@/components/DashboardSectionCard';
import { formatCurrency, formatPercent } from '@/lib/format';
import {
  Ministry,
  AskResponse,
  RevenueBreakdown,
  DebtSummary,
  IncomeComparison,
  Poll,
} from '@/types';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend
} from 'recharts';
import { TrendingUp, Calendar, FileText, AlertCircle, HeartPulse, DollarSign, BarChart3, Newspaper, Flame, Building2 } from 'lucide-react';
import { newsItems } from '@/data/news';

type HotTopicSummary = {
  slug: string;
  title: string;
  source: string;
  year: string;
  summary: string;
  stat_count?: number;
  chart_count?: number;
  highlight_count?: number;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

// Real data from Bahamas Budget 2025/26
const initialBudgetSummary = {
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
const initialMinistries: Ministry[] = [
  { id: "health", name: "Ministry of Health & Wellness", allocation: 355_119_623, previous_year_allocation: 332_747_117, change_percent: 6.7, sparkline: [288.4, 263.2, 332.7, 355.1], sector: "Health" },
  { id: "finance", name: "Ministry of Finance", allocation: 362_694_099, previous_year_allocation: 346_639_187, change_percent: 4.6, sparkline: [177.5, 178.8, 346.6, 362.7], sector: "Finance" },
  { id: "education", name: "Ministry of Education", allocation: 137_052_342, previous_year_allocation: 123_252_555, change_percent: 11.2, sparkline: [114.7, 91.4, 123.3, 137.1], sector: "Education" },
  { id: "police", name: "Royal Bahamas Police Force", allocation: 134_036_300, previous_year_allocation: 126_644_406, change_percent: 5.8, sparkline: [126.5, 100.9, 126.6, 134.0], sector: "Security" },
];

// Real sector breakdown from Budget 2025/26
const initialSectorData = [
  { name: "Public Debt Service", value: 689_545_978, color: "#ef4444" },
  { name: "Health", value: 477_596_494, color: "#FCD116" },
  { name: "Education", value: 353_413_898, color: "#00CED1" },
  { name: "Security", value: 231_980_608, color: "#3b82f6" },
  { name: "Tourism", value: 123_395_161, color: "#8b5cf6" },
  { name: "Social Services", value: 72_243_034, color: "#10b981" },
  { name: "Other", value: 1_496_343_624, color: "#6b7280" },
];

// Real historical data from Fiscal Summary (Page 34)
const initialHistoricalData = [
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

  const [budgetSummary, setBudgetSummary] = useState(initialBudgetSummary);
  const [ministries, setMinistries] = useState<Ministry[]>(initialMinistries);
  const [sectorData, setSectorData] = useState(initialSectorData);
  const [historicalData, setHistoricalData] =
    useState(initialHistoricalData);
  const [revenue, setRevenue] = useState<RevenueBreakdown | null>(null);
  const [debt, setDebt] = useState<DebtSummary | null>(null);
  const [incomeComparisons, setIncomeComparisons] = useState<
    IncomeComparison[] | null
  >(null);
  const [activePoll, setActivePoll] = useState<Poll | null>(null);
  const [hotTopics, setHotTopics] = useState<HotTopicSummary[] | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [
          budgetRes,
          historicalRes,
          sectorRes,
          ministriesRes,
          revenueRes,
          debtRes,
          economicRes,
          pollsRes,
          hotTopicsRes,
        ] = await Promise.allSettled([
          fetch(`${API_BASE}/budget/summary`),
          fetch(`${API_BASE}/budget/historical`),
          fetch(`${API_BASE}/budget/sector-breakdown`),
          fetch(`${API_BASE}/ministries`),
          fetch(`${API_BASE}/revenue`),
          fetch(`${API_BASE}/debt`),
          fetch(`${API_BASE}/economic/comparison`),
          fetch(`${API_BASE}/polls/active`),
          fetch(`${API_BASE}/hot-topics/reports`),
        ]);

        if (
          budgetRes.status === 'fulfilled' &&
          budgetRes.value.ok
        ) {
          const json = await budgetRes.value.json();
          setBudgetSummary((prev) => ({
            ...prev,
            ...json,
          }));
        }

        if (
          historicalRes.status === 'fulfilled' &&
          historicalRes.value.ok
        ) {
          const json = await historicalRes.value.json();
          if (Array.isArray(json.years)) {
            setHistoricalData(
              json.years.map((y: any) => ({
                year: y.year,
                revenue: y.revenue / 1_000_000_000,
                expenditure: y.expenditure / 1_000_000_000,
                debt: y.debt / 1_000_000_000,
                debt_gdp: y.debt_gdp,
              })),
            );
          }
        }

        if (
          sectorRes.status === 'fulfilled' &&
          sectorRes.value.ok
        ) {
          const json = await sectorRes.value.json();
          if (Array.isArray(json.sectors)) {
            setSectorData(
              json.sectors.map((s: any) => ({
                name: s.name,
                value: s.amount,
                color: s.color,
              })),
            );
          }
        }

        if (
          ministriesRes.status === 'fulfilled' &&
          ministriesRes.value.ok
        ) {
          const json = await ministriesRes.value.json();
          if (Array.isArray(json)) {
            setMinistries(json);
          }
        }

        if (
          revenueRes.status === 'fulfilled' &&
          revenueRes.value.ok
        ) {
          const json = await revenueRes.value.json();
          setRevenue(json);
        }

        if (debtRes.status === 'fulfilled' && debtRes.value.ok) {
          const json = await debtRes.value.json();
          setDebt(json);
        }

        if (
          economicRes.status === 'fulfilled' &&
          economicRes.value.ok
        ) {
          const json = await economicRes.value.json();
          if (Array.isArray(json)) {
            setIncomeComparisons(json);
          }
        }

        if (
          pollsRes.status === 'fulfilled' &&
          pollsRes.value.ok
        ) {
          const json = await pollsRes.value.json();
          setActivePoll(json);
        }

        if (
          hotTopicsRes.status === 'fulfilled' &&
          hotTopicsRes.value.ok
        ) {
          const json = await hotTopicsRes.value.json();
          if (Array.isArray(json)) {
            setHotTopics(json);
          }
        }
      } catch (err) {
        console.error('Failed to load dashboard data', err);
      }
    };

    fetchData();
  }, []);

  const totalDebt = debt?.total_debt ?? budgetSummary.national_debt;
  const debtToGdp =
    debt?.debt_to_gdp_ratio ?? budgetSummary.debt_to_gdp_ratio;
  const interestCost = debt?.annual_interest_cost ?? 0;
  const revenueTotal = revenue?.total_revenue ?? null;
  const interestShare =
    interestCost && revenueTotal
      ? (interestCost / revenueTotal) * 100
      : null;

  const healthMinistry = useMemo(
    () =>
      ministries.find(
        (m) => m.id === 'health' || m.sector.toLowerCase() === 'health',
      ),
    [ministries],
  );

  const healthShare = useMemo(() => {
    if (!sectorData || sectorData.length === 0) return null;
    const total = sectorData.reduce((sum, s) => sum + s.value, 0);
    if (!total) return null;
    const healthSector = sectorData.find(
      (s) => s.name.toLowerCase() === 'health',
    );
    if (!healthSector) return null;
    return healthSector.value / total;
  }, [sectorData]);

  const incomeSnapshot = useMemo(
    () => (incomeComparisons && incomeComparisons.length > 0 ? incomeComparisons[0] : null),
    [incomeComparisons],
  );

  const latestNews = useMemo(
    () => newsItems.slice(0, 3),
    [],
  );

  const firstHotTopic = hotTopics && hotTopics.length > 0 ? hotTopics[0] : null;

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
          onClick={() => router.push('/ministries')}
        />
        <StatCard
          title="Revenue"
          value={budgetSummary.total_revenue}
          subtitle="Projected for FY2025/26"
          sourceDocument={budgetSummary.source_document}
          onClick={() => router.push('/revenue')}
        />
        <StatCard
          title="National Debt"
          value={budgetSummary.national_debt}
          subtitle={`${budgetSummary.debt_to_gdp_ratio}% of GDP (down from 88.7%)`}
          sourceDocument={budgetSummary.source_document}
          onClick={() => router.push('/debt')}
        />
        <StatCard
          title="Budget Surplus"
          value={budgetSummary.deficit_surplus}
          subtitle="First surplus since Independence! 🎉"
          sourceDocument={budgetSummary.source_document}
          onClick={() => router.push('/revenue')}
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
          <div className="h-[260px] min-h-[200px] w-full min-w-0">
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

      {/* Explore the Data */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Explore the data</h2>
          <p className="text-xs text-gray-500">
            Jump into health, income, polls, news, hot topics, and ministries.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Health */}
          <DashboardSectionCard
            href="/health"
            title="Health & wellness"
            subtitle="Hospitals, clinics, and public health."
            icon={HeartPulse}
            primaryStatLabel="Allocation 2025/26"
            primaryStatValue={
              healthMinistry
                ? formatCurrency(healthMinistry.allocation)
                : '—'
            }
            secondaryStatLabel={healthShare ? 'Share of national budget' : undefined}
            secondaryStatValue={
              healthShare ? formatPercent(healthShare) : undefined
            }
          />

          {/* Income */}
          <DashboardSectionCard
            href="/income"
            title="Income & cost of living"
            subtitle="What households need to get by."
            icon={DollarSign}
            primaryStatLabel="Middle class monthly income"
            primaryStatValue={
              incomeSnapshot
                ? formatCurrency(incomeSnapshot.middle_class.month_amount)
                : '—'
            }
            secondaryStatLabel={
              incomeSnapshot ? 'Gap vs working class' : undefined
            }
            secondaryStatValue={
              incomeSnapshot
                ? `${formatCurrency(incomeSnapshot.difference_amount)} · ${incomeSnapshot.difference_percent.toFixed(1)}% higher`
                : undefined
            }
          />

          {/* Polls */}
          <DashboardSectionCard
            href="/polls"
            title="Public polls"
            subtitle="What Bahamians are saying right now."
            icon={BarChart3}
            primaryStatLabel="Current question"
            primaryStatValue={
              activePoll?.question
                ? activePoll.question
                : 'No active poll at the moment.'
            }
            secondaryStatLabel={
              activePoll && typeof activePoll.total_votes === 'number'
                ? 'Responses so far'
                : undefined
            }
            secondaryStatValue={
              activePoll && typeof activePoll.total_votes === 'number'
                ? `${activePoll.total_votes.toLocaleString()} responses`
                : undefined
            }
          />

          {/* News */}
          <DashboardSectionCard
            href="/news"
            title="News & updates"
            subtitle="Official budget and economic announcements."
            icon={Newspaper}
            primaryStatLabel="Latest headline"
            primaryStatValue={
              latestNews.length > 0 ? latestNews[0].title : 'No news yet.'
            }
            secondaryStatLabel={
              latestNews.length > 1 ? 'More updates available' : undefined
            }
            secondaryStatValue={
              latestNews.length > 1
                ? `${latestNews.length} featured updates`
                : undefined
            }
          />

          {/* Hot topics */}
          <DashboardSectionCard
            href="/hot"
            title="Hot topics"
            subtitle="High-impact reports on accountability and governance."
            icon={Flame}
            primaryStatLabel="Reports available"
            primaryStatValue={
              hotTopics
                ? `${hotTopics.length} report${hotTopics.length === 1 ? '' : 's'}`
                : 'Loading…'
            }
            secondaryStatLabel={firstHotTopic ? 'Featured report' : undefined}
            secondaryStatValue={firstHotTopic?.title}
          />

          {/* Ministries */}
          <DashboardSectionCard
            href="/ministries"
            title="Ministries overview"
            subtitle="See which ministries receive the most funding."
            icon={Building2}
            primaryStatLabel="Number of ministries"
            primaryStatValue={ministries.length}
            secondaryStatLabel="Top ministry"
            secondaryStatValue={
              ministries.length > 0
                ? ministries
                    .slice()
                    .sort((a, b) => b.allocation - a.allocation)[0].name
                : undefined
            }
          />
        </div>
      </div>

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
