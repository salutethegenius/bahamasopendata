export type ScorecardStat = {
  label: string;
  display: string;
  source: string;
  chartValue?: number;
};

export type ScorecardChart = {
  title: string;
  unit: string;
  points: { year: string; value: number }[];
};

export type ScorecardArea = {
  id: string;
  name: string;
  firstTerm: string;
  secondTerm: string;
  direction: string;
  verdict: string;
  relatedHref?: string;
  stats: ScorecardStat[];
  chart?: ScorecardChart;
};

export type GeographicIssueRow = {
  id: string;
  label: string;
  grandBahama: string;
  abaco: string;
  newProvidence: string;
};

export type ScorecardRegion = {
  id: 'grand-bahama' | 'abaco' | 'new-providence';
  name: string;
  overall: string;
  firstTerm?: string;
  secondTerm?: string;
  verdict: string;
  href: string;
};

export type Scorecard = {
  id: string;
  title: string;
  subtitle: string;
  assessedOn: string;
  assessedOnLabel: string;
  overall: {
    firstTerm: string;
    secondTerm: string;
    secondTermNote: string;
    direction: string;
  };
  thesis: string;
  verdict: string;
  areas: ScorecardArea[];
  geographicIssues: GeographicIssueRow[];
  regions: ScorecardRegion[];
};

export const currentScorecard: Scorecard = {
  id: 'davis-2021-2026',
  title: 'Government Scorecard',
  subtitle: 'Davis administration, September 2021 – August 2026',
  assessedOn: '2026-08-21',
  assessedOnLabel: '21 August 2026',
  overall: {
    firstTerm: 'B-',
    secondTerm: 'B-',
    secondTermNote: 'so far',
    direction: 'Positive fundamentals, uneven delivery',
  },
  thesis: 'The PLP stabilized the country faster than it modernized it.',
  verdict:
    'The Davis administration deserves more credit than its loudest critics give it on the national economy, fiscal stabilization, tourism, investment, and the 2025 drop in violent crime. It deserves more criticism than its own messaging acknowledges on electricity, project completion, Family Island infrastructure, housing affordability, and public healthcare delivery. The second term should be judged on execution rather than announcements.',
  areas: [
    {
      id: 'economy',
      name: 'Economy and employment',
      firstTerm: 'B+',
      secondTerm: 'B',
      direction: 'Stable',
      verdict:
        'The first term stabilized and expanded the economy, but has not produced the productivity shift needed to change living standards. Growth remains tourism-heavy, wages have lagged household costs, and underlying potential growth is still estimated around 1.5 percent without deeper reform.',
      stats: [
        { label: 'Real GDP growth, 2025', display: '2.8%', source: 'IMF' },
        { label: 'Real GDP growth, 2024', display: '3.4%', source: 'IMF' },
        { label: 'Unemployment, Q2 2025', display: '9.3%', source: 'IMF' },
        { label: 'S&P sovereign rating', display: 'BB- (from B+, Sep 2025)', source: 'S&P' },
        { label: "Moody's sovereign rating", display: 'Ba3 (Apr 2026)', source: "Moody's" },
      ],
    },
    {
      id: 'fiscal',
      name: 'Fiscal management',
      firstTerm: 'B+',
      secondTerm: 'B+',
      direction: 'Improving',
      relatedHref: '/debt',
      verdict:
        'The government inherited a dangerous fiscal position and has materially improved it, including a third consecutive primary surplus. Debt is still high, and contingent liabilities from state-owned enterprises and public-private partnerships remain a risk as government takes a larger role in energy.',
      stats: [
        { label: 'Primary surplus streak', display: 'Third consecutive in FY2024/25', source: 'IMF' },
        { label: 'Central government debt, 2025', display: 'About 74% of GDP', source: 'IMF' },
        { label: 'Projected debt, 2026', display: 'About 72.7% of GDP', source: 'IMF' },
      ],
    },
    {
      id: 'tourism',
      name: 'Tourism and investment',
      firstTerm: 'A-',
      secondTerm: 'A-',
      direction: 'Strong',
      verdict:
        'National visitor numbers are hard to argue with, and the gains were not limited to Nassau. Some Grand Bahama investment figures are announced or committed rather than completed, which still matters, but attracting capital and rebuilding tourism momentum is a genuine strength.',
      stats: [
        { label: 'Visitors, 2025', display: 'About 12.5 million', source: 'Government tourism figures' },
        { label: 'Abaco visitors, 2025', display: 'Just under 520,000, a record', source: 'Government tourism figures' },
        {
          label: 'Grand Bahama visitors, 2025',
          display: 'About 1.1 million, first million-plus year in 22+ years',
          source: 'Government tourism figures',
        },
        {
          label: 'Grand Bahama investment since 2021',
          display: 'More than $3.5 billion in investments and commitments',
          source: 'Government',
        },
      ],
    },
    {
      id: 'cost-of-living',
      name: 'Cost of living',
      firstTerm: 'C',
      secondTerm: 'C+',
      direction: 'Slight improvement',
      relatedHref: '/income',
      verdict:
        'Inflation has cooled, and government has raised the minimum wage, cut VAT on some foods, and expanded price controls. The existing price level for food, housing, insurance, transport, and energy remains unaffordable for many households. Low measured inflation and a high cost of living can both be true.',
      stats: [
        { label: 'Minimum wage, 2023', display: '$260 per week', source: 'Government' },
        {
          label: 'Livable wage, New Providence',
          display: 'About $2,625 per month',
          source: 'University of The Bahamas, reported by Our News',
        },
        {
          label: 'Livable wage, Grand Bahama',
          display: 'About $3,550 per month',
          source: 'University of The Bahamas, reported by Our News',
        },
      ],
    },
    {
      id: 'crime',
      name: 'Crime and public safety',
      firstTerm: 'B-',
      secondTerm: 'B-',
      direction: 'Improving',
      verdict:
        'Murders fell sharply in 2025, and police reported reductions in major crime across New Providence, Grand Bahama, and the Family Islands. One strong year does not yet prove a structural change. If 2026 and 2027 stay near or below 2025 levels, the grade should rise.',
      stats: [
        { label: 'Murders, 2025', display: '83', source: 'Police', chartValue: 83 },
        { label: 'Change vs 2024', display: 'Down about 31% from 120', source: 'Police' },
      ],
      chart: {
        title: 'Murders, 2021 to 2025',
        unit: 'homicides',
        points: [
          { year: '2021', value: 119 },
          { year: '2022', value: 128 },
          { year: '2023', value: 110 },
          { year: '2024', value: 120 },
          { year: '2025', value: 83 },
        ],
      },
    },
    {
      id: 'housing',
      name: 'Housing',
      firstTerm: 'C+',
      secondTerm: 'C+',
      direction: 'Slow improvement',
      verdict:
        'Public housing construction and rent-to-own programmes have restarted, which deserves recognition. The national affordability gap is still much larger than the delivery so far. This is progress from a weak starting point, not a solved problem.',
      stats: [
        {
          label: 'Government homes completed and occupied',
          display: '159',
          source: 'Government delivery report',
        },
        {
          label: 'Homes scheduled around June 2026',
          display: '126',
          source: 'Government delivery report',
        },
      ],
    },
    {
      id: 'healthcare',
      name: 'Healthcare',
      firstTerm: 'C+',
      secondTerm: 'C+',
      direction: 'Major projects, delivery lag',
      relatedHref: '/health',
      verdict:
        'There is significant capital investment, including a new Grand Bahama health campus and a major New Providence hospital plan. Service today still lags the renderings: Rand Memorial has had infrastructure failures, and Princess Margaret Hospital remains under pressure. The grade can move quickly if facilities open, are staffed, and cut waiting times.',
      stats: [
        {
          label: 'Capital investment',
          display: 'New Grand Bahama health campus; New Providence hospital in development',
          source: 'Government',
        },
      ],
    },
    {
      id: 'infrastructure',
      name: 'Roads and public infrastructure',
      firstTerm: 'C',
      secondTerm: 'C+',
      direction: 'Uneven',
      relatedHref: '/map',
      verdict:
        'Delivery is island-dependent. Private recovery on Abaco has outpaced public reconstruction, while Grand Bahama’s airport and Lucayan projects remain the tests of whether announcements become operating assets. Grade projects when the doors open, not at groundbreaking.',
      stats: [
        {
          label: 'Grand Bahama airport, Sep 2025',
          display: '$200 million redevelopment halted after financing failed',
          source: 'Public reports',
        },
        {
          label: 'Grand Bahama airport, Jan 2026',
          display: 'Contractors mobilized; Phase One expected to exceed $100 million',
          source: 'Government',
        },
      ],
    },
    {
      id: 'electricity',
      name: 'Electricity and energy',
      firstTerm: 'C-',
      secondTerm: 'C',
      direction: 'Highly island-dependent',
      verdict:
        'Grand Bahama’s GBPC takeover and Equity Rate Adjustment is the strongest energy intervention of the administration, with estimated residential bill cuts of 35 to 49 percent. New Providence’s summer 2026 outages are a serious service failure in the capital. Abaco still faces weak reliability. The national grade hides three different grids.',
      stats: [
        {
          label: 'GBPC residential bill change',
          display: 'About 35–49% reductions, depending on use',
          source: 'GBPC estimates',
        },
        {
          label: 'GBPC rate design, June 2026',
          display: 'First 200 kWh has no residential base tariff; storm recovery charge removed',
          source: 'GBPC',
        },
        {
          label: 'Nassau outages, Jul–Aug 2026',
          display: 'Island-wide blackout 30 July; repeated western NP outages into August',
          source: 'The Tribune; BPL',
        },
        {
          label: 'PM energy address, 17 Aug 2026',
          display: '45% fewer outages and 35% shorter duration vs historical averages (2025 work)',
          source: 'Prime Minister Davis',
        },
      ],
    },
    {
      id: 'governance',
      name: 'Governance and execution',
      firstTerm: 'C+',
      secondTerm: 'C+',
      direction: 'Mixed',
      verdict:
        'The gap is not a shortage of plans. It is the distance from announcement to financing, groundbreaking, completion, and reliable operation. “Delivered or in progress” is not the same as delivered. The IMF has also warned that heavier use of PPPs needs stronger procurement, reporting, and fiscal-risk controls.',
      stats: [
        {
          label: 'Blueprint commitments',
          display: '325 of 387 delivered or in progress',
          source: 'Government delivery tracker',
        },
        {
          label: '2026 election result',
          display: '33 of 41 seats; 51.11% of votes cast',
          source: 'Election results',
        },
      ],
    },
  ],
  geographicIssues: [
    { id: 'economy', label: 'Economic momentum', grandBahama: 'B+', abaco: 'B+', newProvidence: 'B+' },
    { id: 'tourism', label: 'Tourism', grandBahama: 'A-', abaco: 'A-', newProvidence: 'A' },
    { id: 'electricity-cost', label: 'Electricity cost', grandBahama: 'B+ now', abaco: 'C-/D+', newProvidence: 'C' },
    {
      id: 'electricity-reliability',
      label: 'Electricity reliability',
      grandBahama: 'B-/C+',
      abaco: 'D',
      newProvidence: 'D currently',
    },
    { id: 'roads', label: 'Roads and infrastructure', grandBahama: 'C', abaco: 'D+', newProvidence: 'C' },
    { id: 'healthcare', label: 'Healthcare', grandBahama: 'C+', abaco: 'C', newProvidence: 'C+' },
    { id: 'execution', label: 'Major project execution', grandBahama: 'C+', abaco: 'C', newProvidence: 'B-' },
    { id: 'cost-of-living', label: 'Cost of living', grandBahama: 'C', abaco: 'C', newProvidence: 'C' },
    {
      id: 'politics',
      label: 'Political satisfaction signal',
      grandBahama: 'Mixed',
      abaco: 'Very mixed',
      newProvidence: 'PLP dominant',
    },
  ],
  regions: [
    {
      id: 'grand-bahama',
      name: 'Grand Bahama',
      overall: 'B- trending B',
      firstTerm: 'B-',
      secondTerm: 'B',
      href: '/map',
      verdict:
        'This is where the second term currently has the most upside. The GBPC intervention could become transformational, tourism has returned, and large private projects are underway. The airport and Grand Lucayan are the tests: grade them when the doors open.',
    },
    {
      id: 'abaco',
      name: 'Abaco',
      overall: 'C+',
      href: '/map',
      verdict:
        'The private economy and tourism recovered faster than public infrastructure. Roads, airports, and power still trail the island’s economic recovery. Abaco shows that a strong local private sector can rebuild faster than the state.',
    },
    {
      id: 'new-providence',
      name: 'New Providence',
      overall: 'B- first term, C+ currently',
      firstTerm: 'B-',
      secondTerm: 'C+',
      href: '/map',
      verdict:
        'The capital has the strongest national recovery, tourism, and public investment pipeline. It cannot regularly lose electricity for eight, twelve, or twenty hours and keep a strong governance grade. The present BPL situation is a second-term accountability issue.',
    },
  ],
};

export const scorecards: Scorecard[] = [currentScorecard];
