import type { Ministry } from '@/types';

// Real data from Bahamas Budget 2025/26
export const initialBudgetSummary = {
  fiscal_year: '2025/26',
  total_revenue: 3_896_324_553,
  total_expenditure: 3_820_844_050,
  recurrent_expenditure: 3_444_518_797,
  capital_expenditure: 376_325_253,
  // SURPLUS - First balanced budget in independent Bahamas!
  deficit_surplus: 75_480_503,
  national_debt: 11_386_500_000,
  debt_to_gdp_ratio: 68.9,
  gdp: 16_525_700_000,
  source_document: 'Bahamas BudgetFINAL_2025-2026_.pdf',
  source_page: 34,
};

// Real ministry allocations from Budget Book 2025/26 (Pages 71-72)
export const initialMinistries: Ministry[] = [
  {
    id: 'health',
    name: 'Ministry of Health & Wellness',
    allocation: 355_119_623,
    previous_year_allocation: 332_747_117,
    change_percent: 6.7,
    sparkline: [288.4, 263.2, 332.7, 355.1],
    sector: 'Health',
  },
  {
    id: 'finance',
    name: 'Ministry of Finance',
    allocation: 362_694_099,
    previous_year_allocation: 346_639_187,
    change_percent: 4.6,
    sparkline: [177.5, 178.8, 346.6, 362.7],
    sector: 'Finance',
  },
  {
    id: 'education',
    name: 'Ministry of Education',
    allocation: 137_052_342,
    previous_year_allocation: 123_252_555,
    change_percent: 11.2,
    sparkline: [114.7, 91.4, 123.3, 137.1],
    sector: 'Education',
  },
  {
    id: 'police',
    name: 'Royal Bahamas Police Force',
    allocation: 134_036_300,
    previous_year_allocation: 126_644_406,
    change_percent: 5.8,
    sparkline: [126.5, 100.9, 126.6, 134.0],
    sector: 'Security',
  },
];

