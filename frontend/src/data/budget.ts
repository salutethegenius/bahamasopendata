import type { Ministry } from '@/types';
import { CURRENT_FISCAL_YEAR } from '@/lib/fiscal-year';

// Fallback dashboard data until API responses load (FY2026/27 Draft Estimates)
export const initialBudgetSummary = {
  fiscal_year: CURRENT_FISCAL_YEAR,
  total_revenue: 4_362_850_850,
  total_expenditure: 4_139_779_656,
  recurrent_expenditure: 3_723_979_656,
  capital_expenditure: 415_800_000,
  deficit_surplus: 223_071_194,
  national_debt: 11_096_700_000,
  debt_to_gdp_ratio: 59.9,
  gdp: 18_515_700_000,
  source_document: 'FY2026-27_Draft_Estimates_of_Revenue_and_Expenditure.pdf',
  source_page: 9,
};

// Ministry allocations from Draft Estimates 2026/27 (agency summary)
export const initialMinistries: Ministry[] = [
  {
    id: 'health',
    name: 'Ministry of Health & Wellness',
    allocation: 400_228_827,
    previous_year_allocation: 355_119_623,
    change_percent: 12.7,
    sparkline: [263.2, 332.7, 355.1, 400.2],
    sector: 'Health',
  },
  {
    id: 'finance',
    name: 'Ministry of Finance',
    allocation: 369_040_488,
    previous_year_allocation: 362_694_099,
    change_percent: 1.8,
    sparkline: [178.8, 346.6, 362.7, 369.0],
    sector: 'Finance',
  },
  {
    id: 'education',
    name: 'Ministry of Education, Science and Technology',
    allocation: 141_904_237,
    previous_year_allocation: 137_052_342,
    change_percent: 3.5,
    sparkline: [91.4, 123.3, 137.1, 141.9],
    sector: 'Education',
  },
  {
    id: 'police',
    name: 'Royal Bahamas Police Force',
    allocation: 141_390_647,
    previous_year_allocation: 134_036_300,
    change_percent: 5.5,
    sparkline: [100.9, 126.6, 134.0, 141.4],
    sector: 'Security',
  },
];
