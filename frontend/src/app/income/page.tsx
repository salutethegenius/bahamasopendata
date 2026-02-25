'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import StatCard from '@/components/StatCard';
import { formatCurrency, formatPercent } from '@/lib/format';
import { EconomicIndicator, IncomeComparison } from '@/types';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, CartesianGrid, Legend
} from 'recharts';
import { FileText, MapPin, ExternalLink } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8007';
const COLORS = ['#00CED1', '#FCD116', '#3b82f6', '#10b981', '#f59e0b'];

function getYearFromDate(dateString: string | null | undefined): string {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    if (!isNaN(date.getTime())) {
      return ` (${date.getFullYear()})`;
    }
  } catch {
    // Ignore date parsing errors
  }
  return '';
}

export default function IncomePage() {
  const [indicators, setIndicators] = useState<EconomicIndicator[]>([]);
  const [comparisons, setComparisons] = useState<IncomeComparison[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [indicatorsRes, comparisonsRes] = await Promise.all([
          fetch(`${API_BASE}/api/v1/economic/indicators`),
          fetch(`${API_BASE}/api/v1/economic/comparison`)
        ]);
        
        let indicatorsData: EconomicIndicator[] = [];
        let comparisonsData: IncomeComparison[] = [];
        
        if (indicatorsRes.ok) {
          indicatorsData = await indicatorsRes.json();
        } else {
          console.warn('Failed to fetch indicators, using fallback data');
        }
        
        if (comparisonsRes.ok) {
          comparisonsData = await comparisonsRes.json();
        } else {
          console.warn('Failed to fetch comparisons, using fallback data');
        }
        
        // Use fallback if we got empty arrays or errors
        if (indicatorsData.length === 0 || comparisonsData.length === 0) {
          throw new Error('No data received');
        }
        
        setIndicators(indicatorsData);
        setComparisons(comparisonsData);
      } catch (error) {
        console.error('Error fetching data:', error);
        // Fallback to mock data if API fails
        const fallbackIndicators: EconomicIndicator[] = [
          {
            indicator_type: 'middle_class',
            island: 'new_providence',
            year: 2024,
            month_amount: 10200,
            annual_amount: 122400,
            breakdown: { food: 2500, housing_utilities: 2142, nfnh: 3508, savings: 2040 },
            source_document: 'How Much Does It Cost to Be Middle Class in The Bahamas?',
            source_url: 'https://www.ub.edu.bs/wp-content/uploads/Archer2024Final.pdf',
            author: 'Lesvie Archer',
            published_date: '2024-03-01'
          },
          {
            indicator_type: 'working_class',
            island: 'new_providence',
            year: 2024,
            month_amount: 5000,
            annual_amount: 60000,
            breakdown: null,
            source_document: 'The Bahamas Living Wages Survey (updated to 2024)',
            source_url: 'https://www.ub.edu.bs/wp-content/uploads/2016/10/GPPI_Living-Wage-Survey_revised_27-May-2021.pdf',
            author: 'Lesvie Archer et al.',
            published_date: '2020-03-01'
          },
          {
            indicator_type: 'middle_class',
            island: 'grand_bahama',
            year: 2024,
            month_amount: 10100,
            annual_amount: 121200,
            breakdown: { food: 2850, housing_utilities: 1692, nfnh: 3508, savings: 2020 },
            source_document: 'How Much Does It Cost to Be Middle Class in The Bahamas?',
            source_url: 'https://www.ub.edu.bs/wp-content/uploads/Archer2024Final.pdf',
            author: 'Lesvie Archer',
            published_date: '2024-03-01'
          },
          {
            indicator_type: 'working_class',
            island: 'grand_bahama',
            year: 2024,
            month_amount: 6600,
            annual_amount: 79200,
            breakdown: null,
            source_document: 'The Bahamas Living Wages Survey (updated to 2024)',
            source_url: 'https://www.ub.edu.bs/wp-content/uploads/2016/10/GPPI_Living-Wage-Survey_revised_27-May-2021.pdf',
            author: 'Lesvie Archer et al.',
            published_date: '2020-03-01'
          }
        ];
        
        const fallbackComparisons: IncomeComparison[] = [
          {
            island: 'new_providence',
            year: 2024,
            middle_class: fallbackIndicators[0],
            working_class: fallbackIndicators[1],
            difference_percent: 104.0,
            difference_amount: 5200
          },
          {
            island: 'grand_bahama',
            year: 2024,
            middle_class: fallbackIndicators[2],
            working_class: fallbackIndicators[3],
            difference_percent: 53.0,
            difference_amount: 3500
          }
        ];
        
        setIndicators(fallbackIndicators);
        setComparisons(fallbackComparisons);
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, []);

  const middleClassNP = indicators.find(i => i.indicator_type === 'middle_class' && i.island === 'new_providence');
  const middleClassGB = indicators.find(i => i.indicator_type === 'middle_class' && i.island === 'grand_bahama');
  const workingClassNP = indicators.find(i => i.indicator_type === 'working_class' && i.island === 'new_providence');
  const workingClassGB = indicators.find(i => i.indicator_type === 'working_class' && i.island === 'grand_bahama');

  const comparisonData = comparisons.length > 0 ? comparisons.map(c => ({
    island: c.island === 'new_providence' ? 'New Providence' : 'Grand Bahama',
    middleClass: c.middle_class?.month_amount || 0,
    workingClass: c.working_class?.month_amount || 0,
    difference: c.difference_percent || 0
  })) : [];

  const islandComparisonData = [
    {
      island: 'New Providence',
      middleClass: middleClassNP?.month_amount || 0,
      workingClass: workingClassNP?.month_amount || 0
    },
    {
      island: 'Grand Bahama',
      middleClass: middleClassGB?.month_amount || 0,
      workingClass: workingClassGB?.month_amount || 0
    }
  ];

  const breakdownDataNP = middleClassNP?.breakdown ? [
    { name: 'Food', value: middleClassNP.breakdown.food || 0 },
    { name: 'Housing & Utilities', value: middleClassNP.breakdown.housing_utilities || 0 },
    { name: 'Non-Food, Non-Housing', value: middleClassNP.breakdown.nfnh || 0 },
    { name: 'Savings', value: middleClassNP.breakdown.savings || 0 }
  ] : [];

  const breakdownDataGB = middleClassGB?.breakdown ? [
    { name: 'Food', value: middleClassGB.breakdown.food || 0 },
    { name: 'Housing & Utilities', value: middleClassGB.breakdown.housing_utilities || 0 },
    { name: 'Non-Food, Non-Housing', value: middleClassGB.breakdown.nfnh || 0 },
    { name: 'Savings', value: middleClassGB.breakdown.savings || 0 }
  ] : [];

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <p className="text-gray-500">Loading income data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Cost of <span className="text-turquoise">Living</span>
        </h1>
        <p className="text-gray-600">
          Income requirements for middle-class and working-class families in The Bahamas.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Middle Class (New Providence)"
          value={middleClassNP?.month_amount || 0}
          subtitle={`$${middleClassNP?.annual_amount.toLocaleString() || 0}/year`}
          format="currency"
        />
        <StatCard
          title="Middle Class (Grand Bahama)"
          value={middleClassGB?.month_amount || 0}
          subtitle={`$${middleClassGB?.annual_amount.toLocaleString() || 0}/year`}
          format="currency"
        />
        <StatCard
          title="Working Class (New Providence)"
          value={workingClassNP?.month_amount || 0}
          subtitle={`$${workingClassNP?.annual_amount.toLocaleString() || 0}/year`}
          format="currency"
        />
        <StatCard
          title="Working Class (Grand Bahama)"
          value={workingClassGB?.month_amount || 0}
          subtitle={`$${workingClassGB?.annual_amount.toLocaleString() || 0}/year`}
          format="currency"
        />
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-xl border border-gray-200 p-6 mb-6"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Middle Class vs Working Class Comparison</h3>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            {comparisonData.length > 0 ? (
              <BarChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="island" />
                <YAxis tickFormatter={(v) => `$${v.toLocaleString()}`} />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Legend />
                <Bar dataKey="middleClass" name="Middle Class" fill="#00CED1" />
                <Bar dataKey="workingClass" name="Working Class" fill="#FCD116" />
              </BarChart>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                No comparison data available
              </div>
            )}
          </ResponsiveContainer>
        </div>
        {comparisons.length > 0 && (
          <div className="mt-4 grid grid-cols-2 gap-4">
            {comparisons.map((comp) => (
              <div key={comp.island} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <MapPin className="w-4 h-4 text-gray-500" />
                  <span className="font-medium text-gray-900 capitalize">
                    {comp.island.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-sm text-gray-600">
                  Middle class requires <span className="font-semibold text-turquoise">
                    {formatPercent(comp.difference_percent || 0)}
                  </span> more than working class
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Difference: {formatCurrency(comp.difference_amount || 0)}/month
                </p>
              </div>
            ))}
          </div>
        )}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {middleClassNP?.breakdown && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Middle Class Breakdown - New Providence
            </h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={breakdownDataNP}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                  >
                    {breakdownDataNP.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 space-y-2">
              {breakdownDataNP.map((item, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS[i % COLORS.length] }}
                    />
                    <span className="text-sm text-gray-700">{item.name}</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {formatCurrency(item.value)}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {middleClassGB?.breakdown && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Middle Class Breakdown - Grand Bahama
            </h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={breakdownDataGB}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    dataKey="value"
                    label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                  >
                    {breakdownDataGB.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 space-y-2">
              {breakdownDataGB.map((item, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS[i % COLORS.length] }}
                    />
                    <span className="text-sm text-gray-700">{item.name}</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {formatCurrency(item.value)}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-xl border border-gray-200 p-6 mb-6"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Island Comparison</h3>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            {islandComparisonData.length > 0 ? (
              <BarChart data={islandComparisonData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="island" />
                <YAxis tickFormatter={(v) => `$${v.toLocaleString()}`} />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Legend />
                <Bar dataKey="middleClass" name="Middle Class" fill="#00CED1" />
                <Bar dataKey="workingClass" name="Working Class" fill="#FCD116" />
              </BarChart>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                No comparison data available
              </div>
            )}
          </ResponsiveContainer>
        </div>
      </motion.div>

      {middleClassNP && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-gray-50 rounded-xl border border-gray-200 p-6"
        >
          <div className="flex items-start gap-3">
            <FileText className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-medium text-gray-900 mb-2">Source</h4>
              <p className="text-sm text-gray-700 mb-2">
                <span className="font-medium">{middleClassNP.source_document || 'Source document'}</span>
                {middleClassNP.author && ` by ${middleClassNP.author}`}
                {getYearFromDate(middleClassNP.published_date)}
              </p>
              {middleClassNP.source_url && (
                <a
                  href={middleClassNP.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-turquoise hover:underline"
                >
                  View source document
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
