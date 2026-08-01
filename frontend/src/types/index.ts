// Budget Types
export interface BudgetSummary {
  fiscal_year: string;
  total_revenue: number;
  total_expenditure: number;
  recurrent_expenditure?: number;
  capital_expenditure?: number;
  deficit_surplus: number;
  national_debt: number;
  debt_to_gdp_ratio: number | null;
  revenue_change_yoy?: number | null;
  expenditure_change_yoy?: number | null;
  gdp?: number | null;
  last_updated: string;
  source_document: string;
  source_page: number | null;
}

export interface MonthlyData {
  month: string;
  revenue: number;
  expenditure: number;
}

// Ministry Types
export interface Ministry {
  id: string;
  name: string;
  allocation: number;
  previous_year_allocation: number;
  change_percent: number;
  sparkline: number[];
  sector: string;
}

export interface MinistryDetail {
  id: string;
  name: string;
  allocation: number;
  salaries: number;
  programs: number;
  capital_projects: number;
  grants: number;
  line_items: LineItem[];
  historical: HistoricalData[];
  source_document: string;
  source_page: number;
}

export interface LineItem {
  name: string;
  amount: number;
}

export interface HistoricalData {
  year: string;
  allocation?: number;
  amount?: number;
}

// Revenue Types
export interface RevenueSource {
  name: string;
  amount: number;
  percent_of_total: number;
  change_yoy: number;
}

export interface RevenueBreakdown {
  fiscal_year: string;
  total_revenue: number;
  sources: RevenueSource[];
  last_updated: string;
  source_document: string;
}

// Debt Types
export interface DebtSummary {
  total_debt: number;
  domestic_debt: number;
  external_debt: number;
  debt_to_gdp_ratio: number;
  annual_interest_cost: number;
  change_yoy: number;
  last_updated: string;
  source_document: string;
}

export interface Creditor {
  name: string;
  category: string;
  amount: number;
  percent_of_total: number;
}

export interface RepaymentSchedule {
  year: string;
  principal: number;
  interest: number;
  total: number;
}

// Ask Types
export interface Citation {
  document: string;
  page: number;
  snippet: string;
  url: string | null;
}

export interface AskResponse {
  answer: string;
  numbers: Record<string, number> | null;
  chart_data: Array<{ year: string; amount: number }> | null;
  citations: Citation[];
  confidence: number;
}

// News Types
export interface NewsItem {
  id: number;
  title: string;
  source: string;
  url: string;
  published_date: string;
  summary: string;
  category: string;
}

// Chart data types
export interface ChartDataPoint {
  name: string;
  value: number;
  [key: string]: string | number;
}

// Economic Indicator Types
export interface IncomeBreakdown {
  food?: number | null;
  housing_utilities?: number | null;
  nfnh?: number | null; // Non-food, non-housing
  savings?: number | null;
}

export interface EconomicIndicator {
  id?: number | null;
  indicator_type: string; // "middle_class" | "working_class"
  island: string; // "new_providence" | "grand_bahama"
  year: number;
  month_amount: number;
  annual_amount: number;
  breakdown?: IncomeBreakdown | null;
  source_document?: string | null;
  source_url?: string | null;
  author?: string | null;
  published_date?: string | null;
}

export interface IncomeComparison {
  island: string;
  year: number;
  middle_class: EconomicIndicator;
  working_class: EconomicIndicator;
  difference_percent: number;
  difference_amount: number;
}

// Poll Types
export interface PollOption {
  id: number;
  option_text: string;
  display_order: number;
  votes: number;
}

export interface Poll {
  id: number;
  question: string;
  description?: string | null;
  status: string;
  domain?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  total_votes: number;
  options: PollOption[];
}

// Grand Bahama institutional reference
export interface GrandBahamaRelatedHotTopic {
  slug: string;
  title: string;
}

export interface GrandBahamaRelatedAuthority {
  name: string;
  role: string;
  note: string;
  source: string;
  source_url: string;
}

export interface GrandBahamaMeta {
  title: string;
  as_of: string;
  methodology: string;
  framing: string;
  related_hot_topics: GrandBahamaRelatedHotTopic[];
  related_authorities: GrandBahamaRelatedAuthority[];
}

export interface GrandBahamaMinistryOffice {
  building: string;
  street: string;
  po_box: string;
  city: string;
  phone: string;
}

export interface GrandBahamaMinistry {
  name: string;
  minister: string;
  constituency: string;
  party: string;
  in_office_since: string;
  reappointed: string;
  office: GrandBahamaMinistryOffice;
  portfolio: string[];
  notes: string[];
  source: string;
  source_url: string;
  as_of: string;
}

export interface GrandBahamaMP {
  constituency: string;
  name: string;
  party: string;
  role: string;
  side: 'government' | 'opposition' | string;
  source: string;
  source_url: string;
  as_of: string;
}

export type GrandBahamaDistrictSchedule = 'second' | 'third' | string;
export type GrandBahamaOfficersStatus = 'confirmed' | 'partial' | 'unconfirmed' | string;

export interface GrandBahamaDistrict {
  id: string;
  name: string;
  schedule: GrandBahamaDistrictSchedule;
  schedule_note: string;
  chief_councillor: string | null;
  secretary: string | null;
  officers_status: GrandBahamaOfficersStatus;
  source: string;
  source_url: string;
  as_of: string;
}

export interface GrandBahamaLocalGovernmentContext {
  governing_act: string;
  act_in_force: string;
  overseeing_department: string;
  overseeing_ministry: string;
  national_district_count: number;
  last_election: string;
  next_election_expected: string;
  election_cycle_years: number;
  source: string;
  source_url: string;
}

export interface GrandBahamaDataset {
  meta: GrandBahamaMeta;
  ministry: GrandBahamaMinistry;
  mps: GrandBahamaMP[];
  districts: GrandBahamaDistrict[];
  local_government_context: GrandBahamaLocalGovernmentContext;
}


