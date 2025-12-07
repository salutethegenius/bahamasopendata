'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MinistryCard from '@/components/MinistryCard';
import { Ministry, MinistryDetail } from '@/types';
import { formatCurrency, formatPercent } from '@/lib/format';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { X, FileText, TrendingUp, Users, Building, Wallet } from 'lucide-react';

// Mock data
const ministries: Ministry[] = [
  { id: "education", name: "Ministry of Education", allocation: 450_000_000, previous_year_allocation: 420_000_000, change_percent: 7.1, sparkline: [380, 395, 410, 420, 450], sector: "Education" },
  { id: "health", name: "Ministry of Health", allocation: 380_000_000, previous_year_allocation: 350_000_000, change_percent: 8.6, sparkline: [310, 325, 340, 350, 380], sector: "Health" },
  { id: "national-security", name: "Ministry of National Security", allocation: 320_000_000, previous_year_allocation: 310_000_000, change_percent: 3.2, sparkline: [280, 290, 300, 310, 320], sector: "Security" },
  { id: "works", name: "Ministry of Works & Infrastructure", allocation: 280_000_000, previous_year_allocation: 250_000_000, change_percent: 12.0, sparkline: [200, 220, 235, 250, 280], sector: "Infrastructure" },
  { id: "finance", name: "Ministry of Finance", allocation: 250_000_000, previous_year_allocation: 245_000_000, change_percent: 2.0, sparkline: [220, 230, 238, 245, 250], sector: "Finance" },
  { id: "tourism", name: "Ministry of Tourism", allocation: 180_000_000, previous_year_allocation: 165_000_000, change_percent: 9.1, sparkline: [140, 150, 158, 165, 180], sector: "Tourism" },
  { id: "social-services", name: "Ministry of Social Services", allocation: 150_000_000, previous_year_allocation: 140_000_000, change_percent: 7.1, sparkline: [120, 128, 135, 140, 150], sector: "Social Services" },
  { id: "agriculture", name: "Ministry of Agriculture", allocation: 85_000_000, previous_year_allocation: 80_000_000, change_percent: 6.3, sparkline: [65, 70, 75, 80, 85], sector: "Agriculture" },
  { id: "environment", name: "Ministry of Environment", allocation: 65_000_000, previous_year_allocation: 58_000_000, change_percent: 12.1, sparkline: [45, 50, 54, 58, 65], sector: "Environment" },
  { id: "pmo", name: "Office of the Prime Minister", allocation: 120_000_000, previous_year_allocation: 115_000_000, change_percent: 4.3, sparkline: [100, 105, 110, 115, 120], sector: "Executive" },
];

const mockDetail: MinistryDetail = {
  id: "education",
  name: "Ministry of Education",
  allocation: 450_000_000,
  salaries: 280_000_000,
  programs: 95_000_000,
  capital_projects: 55_000_000,
  grants: 20_000_000,
  line_items: [
    { name: "Teacher Salaries", amount: 180_000_000 },
    { name: "Administrative Staff", amount: 45_000_000 },
    { name: "School Maintenance", amount: 35_000_000 },
    { name: "Curriculum Development", amount: 25_000_000 },
    { name: "Student Support Programs", amount: 20_000_000 },
    { name: "Technology & Equipment", amount: 18_000_000 },
    { name: "School Construction", amount: 45_000_000 },
    { name: "Training Programs", amount: 15_000_000 },
  ],
  historical: [
    { year: "2020/21", allocation: 380_000_000 },
    { year: "2021/22", allocation: 395_000_000 },
    { year: "2022/23", allocation: 410_000_000 },
    { year: "2023/24", allocation: 420_000_000 },
    { year: "2024/25", allocation: 450_000_000 },
  ],
  source_document: "Budget Book 2024-25.pdf",
  source_page: 87,
};

const COLORS = ['#00CED1', '#FCD116', '#3b82f6', '#10b981'];

export default function MinistriesPage() {
  const [selectedMinistry, setSelectedMinistry] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'allocation' | 'change'>('allocation');

  const filteredMinistries = ministries
    .filter(m => m.name.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort((a, b) => sortBy === 'allocation' 
      ? b.allocation - a.allocation 
      : b.change_percent - a.change_percent
    );

  const totalAllocation = ministries.reduce((sum, m) => sum + m.allocation, 0);

  const breakdownData = [
    { name: 'Salaries', value: mockDetail.salaries },
    { name: 'Programs', value: mockDetail.programs },
    { name: 'Capital', value: mockDetail.capital_projects },
    { name: 'Grants', value: mockDetail.grants },
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
                      {mockDetail.id === selectedMinistry ? 'Education' : 'Ministry'}
                    </p>
                    <h2 className="text-2xl font-bold text-gray-900">{mockDetail.name}</h2>
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
                  <p className="text-sm text-turquoise font-medium">Total Allocation 2024/25</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {formatCurrency(mockDetail.allocation, true)}
                  </p>
                  <p className="text-sm text-green-600 mt-1">
                    +7.1% from last year
                  </p>
                </div>

                {/* Breakdown */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Budget Breakdown</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <Users className="w-5 h-5 text-turquoise mb-2" />
                      <p className="text-xs text-gray-500">Salaries</p>
                      <p className="font-bold text-gray-900">{formatCurrency(mockDetail.salaries, true)}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <Wallet className="w-5 h-5 text-yellow-500 mb-2" />
                      <p className="text-xs text-gray-500">Programs</p>
                      <p className="font-bold text-gray-900">{formatCurrency(mockDetail.programs, true)}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <Building className="w-5 h-5 text-blue-500 mb-2" />
                      <p className="text-xs text-gray-500">Capital Projects</p>
                      <p className="font-bold text-gray-900">{formatCurrency(mockDetail.capital_projects, true)}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <TrendingUp className="w-5 h-5 text-green-500 mb-2" />
                      <p className="text-xs text-gray-500">Grants</p>
                      <p className="font-bold text-gray-900">{formatCurrency(mockDetail.grants, true)}</p>
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
                    {mockDetail.line_items.map((item, i) => (
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
                      <BarChart data={mockDetail.historical}>
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
                    <span>{mockDetail.source_document}, page {mockDetail.source_page}</span>
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

