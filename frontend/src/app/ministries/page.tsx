'use client';

import { useState, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MinistryCard from '@/components/MinistryCard';
import { Ministry, MinistryDetail } from '@/types';
import { formatCurrency, formatPercent } from '@/lib/format';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { X, FileText, TrendingUp, Users, Building, Wallet } from 'lucide-react';

// Real data from Bahamas Budget 2025/26 - Recurrent Expenditure Summary (Pages 71-72)
const ministries: Ministry[] = [
  { id: "finance", name: "Ministry of Finance", allocation: 362_694_099, previous_year_allocation: 346_639_187, change_percent: 4.6, sparkline: [177.5, 178.8, 346.6, 362.7], sector: "Finance" },
  { id: "health", name: "Ministry of Health & Wellness", allocation: 355_119_623, previous_year_allocation: 332_747_117, change_percent: 6.7, sparkline: [288.4, 263.2, 332.7, 355.1], sector: "Health" },
  { id: "education", name: "Ministry of Education & Technical Training", allocation: 137_052_342, previous_year_allocation: 123_252_555, change_percent: 11.2, sparkline: [114.7, 91.4, 123.3, 137.1], sector: "Education" },
  { id: "police", name: "Royal Bahamas Police Force", allocation: 134_036_300, previous_year_allocation: 126_644_406, change_percent: 5.8, sparkline: [126.5, 100.9, 126.6, 134.0], sector: "Security" },
  { id: "tourism", name: "Ministry of Tourism, Investments & Aviation", allocation: 123_395_161, previous_year_allocation: 131_376_411, change_percent: -6.1, sparkline: [140.5, 97.8, 131.4, 123.4], sector: "Tourism" },
  { id: "defence", name: "Royal Bahamas Defence Force", allocation: 77_530_944, previous_year_allocation: 71_382_034, change_percent: 8.6, sparkline: [69.0, 53.9, 71.4, 77.5], sector: "Security" },
  { id: "disaster", name: "Ministry of Disaster Risk Management", allocation: 60_518_380, previous_year_allocation: 10_538_081, change_percent: 474.3, sparkline: [11.9, 7.8, 10.5, 60.5], sector: "Emergency" },
  { id: "foreign-affairs", name: "Ministry of Foreign Affairs", allocation: 54_967_437, previous_year_allocation: 50_682_286, change_percent: 8.5, sparkline: [49.8, 39.7, 50.7, 55.0], sector: "Government" },
  { id: "social-services", name: "Department of Social Services", allocation: 53_074_475, previous_year_allocation: 48_009_263, change_percent: 10.5, sparkline: [47.7, 30.7, 48.0, 53.1], sector: "Social Services" },
  { id: "works", name: "Ministry of Works & Family Island Affairs", allocation: 48_213_665, previous_year_allocation: 36_183_087, change_percent: 33.2, sparkline: [49.9, 41.2, 36.2, 48.2], sector: "Infrastructure" },
  { id: "agriculture", name: "Ministry of Agriculture & Marine Resources", allocation: 35_414_725, previous_year_allocation: 33_036_741, change_percent: 7.2, sparkline: [25.1, 22.4, 33.0, 35.4], sector: "Agriculture" },
  { id: "pmo", name: "Office of the Prime Minister", allocation: 22_236_232, previous_year_allocation: 57_808_386, change_percent: -61.5, sparkline: [56.9, 47.9, 57.8, 22.2], sector: "Executive" },
];

// Real detail data from Budget Book 2025/26
const mockDetails: Record<string, MinistryDetail> = {
  education: {
    id: "education",
    name: "Ministry of Education & Technical Training",
    allocation: 137_052_342,
    salaries: 95_000_000,
    programs: 25_000_000,
    capital_projects: 10_000_000,
    grants: 7_052_342,
    line_items: [
      { name: "Teacher Salaries", amount: 75_000_000 },
      { name: "School Operations", amount: 25_000_000 },
      { name: "Technical & Vocational Training", amount: 15_000_000 },
      { name: "Student Support", amount: 12_000_000 },
      { name: "Administration", amount: 10_052_342 },
    ],
    historical: [
      { year: "2022/23", allocation: 114_718_725 },
      { year: "2023/24", allocation: 91_421_318 },
      { year: "2024/25", allocation: 123_252_555 },
      { year: "2025/26", allocation: 137_052_342 },
    ],
    source_document: "Bahamas BudgetFINAL_2025-2026_.pdf",
    source_page: 71,
  },
  health: {
    id: "health",
    name: "Ministry of Health & Wellness",
    allocation: 355_119_623,
    salaries: 180_000_000,
    programs: 100_000_000,
    capital_projects: 45_000_000,
    grants: 30_119_623,
    line_items: [
      { name: "Public Health Services", amount: 60_631_875 },
      { name: "Environmental Health", amount: 61_844_996 },
      { name: "Hospital Services", amount: 120_000_000 },
      { name: "Medical Supplies", amount: 35_000_000 },
      { name: "General Administration", amount: 50_000_000 },
      { name: "Capital Projects", amount: 27_642_752 },
    ],
    historical: [
      { year: "2022/23", allocation: 288_424_867 },
      { year: "2023/24", allocation: 263_248_575 },
      { year: "2024/25", allocation: 332_747_117 },
      { year: "2025/26", allocation: 355_119_623 },
    ],
    source_document: "Bahamas BudgetFINAL_2025-2026_.pdf",
    source_page: 72,
  },
  police: {
    id: "police",
    name: "Royal Bahamas Police Force",
    allocation: 134_036_300,
    salaries: 95_000_000,
    programs: 25_000_000,
    capital_projects: 10_036_300,
    grants: 4_000_000,
    line_items: [
      { name: "Officer Salaries & Benefits", amount: 95_000_000 },
      { name: "Operations & Patrol", amount: 20_000_000 },
      { name: "Equipment & Vehicles", amount: 10_036_300 },
      { name: "Training & Development", amount: 5_000_000 },
      { name: "Administrative Costs", amount: 4_000_000 },
    ],
    historical: [
      { year: "2022/23", allocation: 126_542_088 },
      { year: "2023/24", allocation: 100_934_535 },
      { year: "2024/25", allocation: 126_644_406 },
      { year: "2025/26", allocation: 134_036_300 },
    ],
    source_document: "Bahamas BudgetFINAL_2025-2026_.pdf",
    source_page: 71,
  },
  disaster: {
    id: "disaster",
    name: "Ministry of Disaster Risk Management",
    allocation: 60_518_380,
    salaries: 15_000_000,
    programs: 30_000_000,
    capital_projects: 10_518_380,
    grants: 5_000_000,
    line_items: [
      { name: "Emergency Response Operations", amount: 25_000_000 },
      { name: "Staff Salaries", amount: 15_000_000 },
      { name: "Equipment & Infrastructure", amount: 10_518_380 },
      { name: "Training & Preparedness", amount: 5_000_000 },
      { name: "Grants & Relief", amount: 5_000_000 },
    ],
    historical: [
      { year: "2022/23", allocation: 11_943_637 },
      { year: "2023/24", allocation: 7_789_084 },
      { year: "2024/25", allocation: 10_538_081 },
      { year: "2025/26", allocation: 60_518_380 },
    ],
    source_document: "Bahamas BudgetFINAL_2025-2026_.pdf",
    source_page: 72,
  },
  tourism: {
    id: "tourism",
    name: "Ministry of Tourism, Investments & Aviation",
    allocation: 123_395_161,
    salaries: 25_000_000,
    programs: 70_000_000,
    capital_projects: 15_000_000,
    grants: 13_395_161,
    line_items: [
      { name: "Marketing & Promotion", amount: 50_000_000 },
      { name: "Staff Salaries", amount: 25_000_000 },
      { name: "Tourism Development", amount: 20_000_000 },
      { name: "Aviation Support", amount: 15_000_000 },
      { name: "Grants & Incentives", amount: 13_395_161 },
    ],
    historical: [
      { year: "2022/23", allocation: 140_512_680 },
      { year: "2023/24", allocation: 97_789_768 },
      { year: "2024/25", allocation: 131_376_411 },
      { year: "2025/26", allocation: 123_395_161 },
    ],
    source_document: "Bahamas BudgetFINAL_2025-2026_.pdf",
    source_page: 72,
  },
  finance: {
    id: "finance",
    name: "Ministry of Finance",
    allocation: 362_694_099,
    salaries: 50_000_000,
    programs: 200_000_000,
    capital_projects: 62_694_099,
    grants: 50_000_000,
    line_items: [
      { name: "Debt Management & Servicing", amount: 150_000_000 },
      { name: "Revenue Administration", amount: 80_000_000 },
      { name: "Staff Salaries", amount: 50_000_000 },
      { name: "Capital Investments", amount: 62_694_099 },
      { name: "Financial Sector Support", amount: 20_000_000 },
    ],
    historical: [
      { year: "2022/23", allocation: 177_516_207 },
      { year: "2023/24", allocation: 178_764_503 },
      { year: "2024/25", allocation: 346_639_187 },
      { year: "2025/26", allocation: 362_694_099 },
    ],
    source_document: "Bahamas BudgetFINAL_2025-2026_.pdf",
    source_page: 71,
  },
};

const COLORS = ['#00CED1', '#FCD116', '#3b82f6', '#10b981'];

function MinistriesPageContent() {
  const [selectedMinistry, setSelectedMinistry] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'allocation' | 'change'>('allocation');

  // Note: Query parameter is ignored - clicking from front page just redirects here
  // Users can manually click ministry cards to open detail panel

  const filteredMinistries = ministries
    .filter(m => m.name.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort((a, b) => sortBy === 'allocation' 
      ? b.allocation - a.allocation 
      : b.change_percent - a.change_percent
    );

  const totalAllocation = ministries.reduce((sum, m) => sum + m.allocation, 0);

  // Get the selected ministry detail, or default to education
  const selectedDetail = selectedMinistry 
    ? (mockDetails[selectedMinistry] || mockDetails.education)
    : mockDetails.education;
  
  // Get the selected ministry for change percent calculation
  const selectedMinistryData = selectedMinistry
    ? ministries.find(m => m.id === selectedMinistry)
    : null;

  const breakdownData = [
    { name: 'Salaries', value: selectedDetail.salaries },
    { name: 'Programs', value: selectedDetail.programs },
    { name: 'Capital', value: selectedDetail.capital_projects },
    { name: 'Grants', value: selectedDetail.grants },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Ministry <span className="text-turquoise">Allocations</span>
        </h1>
        <p className="text-gray-600">
          Explore budget allocations for all government ministries and departments.
        </p>
      </motion.div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total Ministries</p>
          <p className="text-2xl font-bold text-gray-900">{ministries.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Total Allocation</p>
          <p className="text-2xl font-bold text-turquoise">{formatCurrency(totalAllocation, true)}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <p className="text-sm text-gray-500">Average YoY Change</p>
          <p className="text-2xl font-bold text-green-600">
            {formatPercent(ministries.reduce((sum, m) => sum + m.change_percent, 0) / ministries.length)}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <input
          type="text"
          placeholder="Search ministries..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
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

      {/* Ministry Grid */}
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

      {/* Ministry Detail Panel */}
      <AnimatePresence>
        {selectedMinistry && (
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
                {/* Header */}
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <p className="text-sm font-medium text-turquoise uppercase tracking-wide mb-1">
                      {selectedMinistryData?.sector || 'Ministry'}
                    </p>
                    <h2 className="text-2xl font-bold text-gray-900">{selectedDetail.name}</h2>
                  </div>
                  <button
                    onClick={() => setSelectedMinistry(null)}
                    className="p-2 hover:bg-gray-100 rounded-full"
                  >
                    <X className="w-5 h-5 text-gray-500" />
                  </button>
                </div>

                {/* Allocation */}
                <div className="bg-turquoise/10 rounded-xl p-4 mb-6">
                  <p className="text-sm text-turquoise font-medium">Total Allocation 2025/26</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {formatCurrency(selectedDetail.allocation, true)}
                  </p>
                  {selectedMinistryData && (
                    <p className={`text-sm mt-1 ${selectedMinistryData.change_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {selectedMinistryData.change_percent >= 0 ? '+' : ''}{formatPercent(selectedMinistryData.change_percent)} from last year
                    </p>
                  )}
                </div>

                {/* Breakdown */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Budget Breakdown</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <Users className="w-5 h-5 text-turquoise mb-2" />
                      <p className="text-xs text-gray-500">Salaries</p>
                      <p className="font-bold text-gray-900">{formatCurrency(selectedDetail.salaries, true)}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <Wallet className="w-5 h-5 text-yellow-500 mb-2" />
                      <p className="text-xs text-gray-500">Programs</p>
                      <p className="font-bold text-gray-900">{formatCurrency(selectedDetail.programs, true)}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <Building className="w-5 h-5 text-blue-500 mb-2" />
                      <p className="text-xs text-gray-500">Capital Projects</p>
                      <p className="font-bold text-gray-900">{formatCurrency(selectedDetail.capital_projects, true)}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <TrendingUp className="w-5 h-5 text-green-500 mb-2" />
                      <p className="text-xs text-gray-500">Grants</p>
                      <p className="font-bold text-gray-900">{formatCurrency(selectedDetail.grants, true)}</p>
                    </div>
                  </div>
                </div>

                {/* Pie Chart */}
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
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value: number) => formatCurrency(value, true)} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Line Items */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Line Items</h3>
                  <div className="space-y-2">
                    {selectedDetail.line_items.map((item, i) => (
                      <div key={i} className="flex justify-between items-center py-2 border-b border-gray-100">
                        <span className="text-gray-700">{item.name}</span>
                        <span className="font-medium text-gray-900 tabular-nums">
                          {formatCurrency(item.amount, true)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Historical */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Historical Allocation</h3>
                  <div className="h-40">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={selectedDetail.historical}>
                        <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                        <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${(v/1000000).toFixed(0)}M`} />
                        <Tooltip formatter={(value: number) => formatCurrency(value, true)} />
                        <Bar dataKey="allocation" fill="#00CED1" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Source */}
                <div className="border-t border-gray-200 pt-4">
                  <a href="#" className="flex items-center gap-2 text-sm text-gray-500 hover:text-turquoise">
                    <FileText className="w-4 h-4" />
                    <span>{selectedDetail.source_document}, page {selectedDetail.source_page}</span>
                  </a>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function MinistriesPage() {
  return (
    <Suspense fallback={
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    }>
      <MinistriesPageContent />
    </Suspense>
  );
}

