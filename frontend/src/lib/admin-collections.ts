import type { DocumentRecord } from '@/types/admin';

export const documentTypeLabels: Record<string, string> = {
  budget_book: 'Budget book',
  budget_communication: 'Budget communication',
  revenue_estimates: 'Revenue estimates',
  capital_estimates: 'Capital estimates',
  mid_year_statement: 'Mid-year statement',
  debt_report: 'Debt report',
  health_strategy: 'Health strategy',
  economic_indicators: 'Economic indicators',
  island_projects: 'Island projects',
  news_update: 'News updates',
  procurement_report: 'Procurement report',
  legal_ruling: 'Legal ruling',
  other: 'Other',
};

export const documentTypes = [
  ['budget_book', 'Budget book'],
  ['budget_communication', 'Budget communication'],
  ['revenue_estimates', 'Revenue estimates'],
  ['capital_estimates', 'Capital estimates'],
  ['mid_year_statement', 'Mid-year statement'],
  ['debt_report', 'Debt report'],
  ['health_strategy', 'Health strategy'],
  ['economic_indicators', 'Economic indicators'],
  ['island_projects', 'Island projects'],
  ['news_update', 'News updates'],
  ['procurement_report', 'Procurement report'],
  ['legal_ruling', 'Legal ruling'],
  ['other', 'Other'],
] as const;

export type DocumentType = (typeof documentTypes)[number][0];

export type AdminSection = {
  id:
    | 'budget_finance'
    | 'health_services'
    | 'household_economy'
    | 'regional_projects'
    | 'public_updates'
    | 'legal_oversight'
    | 'general_other';
  label: string;
  shortLabel: string;
  description: string;
  publicAreas: string[];
  documentTypes: DocumentType[];
  uploadTitle: string;
  uploadDescription: string;
  reviewDescription: string;
  extractionMode: string;
  aiMode: string;
};

export type DocumentTypeDetails = {
  description: string;
  expectedExample: Record<string, unknown>;
};

export const adminSections: AdminSection[] = [
  {
    id: 'budget_finance',
    label: 'Budget and finance',
    shortLabel: 'Budget',
    description:
      'Core finance files used across the home page, ministries, revenue, and debt experiences.',
    publicAreas: ['Home', 'Ministries', 'Revenue', 'Debt'],
    documentTypes: [
      'budget_book',
      'budget_communication',
      'revenue_estimates',
      'capital_estimates',
      'mid_year_statement',
      'debt_report',
    ],
    uploadTitle: 'Upload finance source files',
    uploadDescription:
      'Use this section for budget books, debt reports, revenue estimates, and other core finance PDFs.',
    reviewDescription:
      'Review extracted numbers and AI-cleaned outputs before approving them for downstream use.',
    extractionMode: 'Deterministic first. Structured budget tables should read quickly with minimal AI help.',
    aiMode: 'Use AI when a finance file is messy, text-heavy, or inconsistent across pages.',
  },
  {
    id: 'health_services',
    label: 'Health and services',
    shortLabel: 'Health',
    description:
      'Strategy and service documents that support the health side of the product.',
    publicAreas: ['Health'],
    documentTypes: ['health_strategy'],
    uploadTitle: 'Upload health source files',
    uploadDescription:
      'Use this section for health strategies, planning documents, and service-delivery PDFs.',
    reviewDescription:
      'Check extracted summaries and AI organization before approving them for use in the platform.',
    extractionMode: 'Structured tables and section headings should be read directly where possible.',
    aiMode: 'Use AI for long narrative documents that need clearer summaries and standardized topics.',
  },
  {
    id: 'household_economy',
    label: 'Household economy',
    shortLabel: 'Economy',
    description:
      'Cost-of-living and household income datasets used across income and affordability views.',
    publicAreas: ['Income'],
    documentTypes: ['economic_indicators'],
    uploadTitle: 'Upload economic indicator data',
    uploadDescription:
      'Use this collection for cost-of-living, living wage, and household budget datasets.',
    reviewDescription:
      'Review the uploaded indicator rows before approving and publishing them to the public comparison views.',
    extractionMode: 'Structured JSON is preferred for indicator rows and yearly comparisons.',
    aiMode: 'AI can help normalize labels and categories, but the target output should stay highly structured.',
  },
  {
    id: 'regional_projects',
    label: 'Regional projects',
    shortLabel: 'Projects',
    description:
      'Island-level allocations and project lists used across the map and project-driven health sections.',
    publicAreas: ['Map', 'Health'],
    documentTypes: ['island_projects'],
    uploadTitle: 'Upload island project data',
    uploadDescription:
      'Use this collection for island allocations, project lists, and regional project snapshots.',
    reviewDescription:
      'Confirm island names, allocations, and project categories before approval and publication.',
    extractionMode: 'Structured datasets work best here because island and project rows are naturally tabular.',
    aiMode: 'AI is helpful only when you are translating a messy PDF into the expected project schema.',
  },
  {
    id: 'public_updates',
    label: 'Public updates',
    shortLabel: 'Updates',
    description:
      'News and announcement data that powers the public updates feed.',
    publicAreas: ['News', 'Home'],
    documentTypes: ['news_update'],
    uploadTitle: 'Upload public update data',
    uploadDescription:
      'Use this collection for official announcements, updates, and release summaries.',
    reviewDescription:
      'Review titles, links, dates, and summaries before sending them live.',
    extractionMode: 'Structured JSON is ideal. PDFs can be used when you need extraction first.',
    aiMode: 'AI is best used to summarize or tidy official announcement documents.',
  },
  {
    id: 'legal_oversight',
    label: 'Legal and oversight',
    shortLabel: 'Legal',
    description:
      'Rulings, oversight reports, and explainers used for hot topics and public accountability content.',
    publicAreas: ['Hot topics', 'Oversight'],
    documentTypes: ['legal_ruling', 'procurement_report'],
    uploadTitle: 'Upload legal and oversight files',
    uploadDescription:
      'Use this section for legal rulings, awards, investigations, and watchdog reports.',
    reviewDescription:
      'Review extracted facts, summaries, and AI-cleaned outputs before marking them ready.',
    extractionMode: 'Direct extraction handles straightforward rulings and clearly structured reports.',
    aiMode: 'AI helps most when legal language is dense or reports mix narrative, exhibits, and tables.',
  },
  {
    id: 'general_other',
    label: 'General and other',
    shortLabel: 'Other',
    description:
      'Files that do not fit an existing product section yet but still need intake and review.',
    publicAreas: ['Other uploads'],
    documentTypes: ['other'],
    uploadTitle: 'Upload general files',
    uploadDescription:
      'Use this holding section for files that need intake before they are mapped to a permanent section.',
    reviewDescription:
      'Review what was extracted, confirm whether AI was needed, and then approve the file for follow-up.',
    extractionMode: 'Start with simple extraction and only escalate if the file is hard to structure.',
    aiMode: 'AI is a helper here, not a requirement.',
  },
];

export const documentTypeDetails: Record<DocumentType, DocumentTypeDetails> = {
  budget_book: {
    description: 'Full budget book records with ministry allocations, fiscal year context, and extracted finance items.',
    expectedExample: {
      source_document: 'Bahamas BudgetFINAL(2025-2026).pdf',
      title: 'Bahamas Budget 2025/26',
      document_type: 'budget_book',
      fiscal_year: '2025/26',
      executive_summary: 'Full annual budget book for the fiscal year.',
      ministries: ['Ministry of Education', 'Ministry of Health'],
      extracted_items: [
        {
          label: 'Ministry of Education',
          amount: 450000000,
          currency: 'BSD',
          category: 'recurrent_expenditure',
          ministry_code: null,
          source_page: 71,
        },
      ],
      notable_topics: ['Annual appropriations', 'Ministry allocations'],
      warnings: [],
      confidence: 0.92,
      needs_review: false,
    },
  },
  budget_communication: {
    description: 'Budget communication summaries with headline priorities, signals, and selected allocation references.',
    expectedExample: {
      source_document: 'Budget_Communication_25_26_final_1.pdf',
      title: 'Budget Communication 2025/26',
      document_type: 'budget_communication',
      fiscal_year: '2025/26',
      executive_summary: 'Headline budget communication with major priorities and policy framing.',
      ministries: ['Ministry of Education'],
      extracted_items: [
        {
          label: 'Ministry of Education',
          amount: 450000000,
          currency: 'BSD',
          category: 'recurrent_expenditure',
          ministry_code: null,
          source_page: 71,
        },
      ],
      notable_topics: ['Education funding', 'Budget priorities'],
      warnings: [],
      confidence: 0.91,
      needs_review: false,
    },
  },
  revenue_estimates: {
    description: 'Revenue estimate files organized into sources, categories, totals, and fiscal-year context.',
    expectedExample: {
      source_document: 'Revenue_Estimates_2025_26.pdf',
      title: 'Revenue Estimates 2025/26',
      document_type: 'revenue_estimates',
      fiscal_year: '2025/26',
      executive_summary: 'Estimated government revenue by source for the fiscal year.',
      ministries: [],
      extracted_items: [
        {
          label: 'VAT',
          amount: 820000000,
          currency: 'BSD',
          category: 'tax_revenue',
          ministry_code: null,
          source_page: 12,
        },
      ],
      notable_topics: ['Tax revenue', 'Revenue projections'],
      warnings: [],
      confidence: 0.9,
      needs_review: false,
    },
  },
  capital_estimates: {
    description: 'Capital estimate files with projects, capital allocations, and related categories.',
    expectedExample: {
      source_document: 'Capital_Estimates_2025_26.pdf',
      title: 'Capital Estimates 2025/26',
      document_type: 'capital_estimates',
      fiscal_year: '2025/26',
      executive_summary: 'Capital projects and planned spending for the fiscal year.',
      ministries: ['Ministry of Works'],
      extracted_items: [
        {
          label: 'Road rehabilitation programme',
          amount: 125000000,
          currency: 'BSD',
          category: 'capital_project',
          ministry_code: null,
          source_page: 33,
        },
      ],
      notable_topics: ['Infrastructure', 'Capital projects'],
      warnings: [],
      confidence: 0.89,
      needs_review: false,
    },
  },
  mid_year_statement: {
    description: 'Mid-year fiscal updates with status changes, progress notes, and revised figures.',
    expectedExample: {
      source_document: 'Mid_Year_Statement_2025_26.pdf',
      title: 'Mid-Year Statement 2025/26',
      document_type: 'mid_year_statement',
      fiscal_year: '2025/26',
      executive_summary: 'Mid-year update on fiscal performance and outlook.',
      ministries: [],
      extracted_items: [
        {
          label: 'Mid-year deficit estimate',
          amount: 95000000,
          currency: 'BSD',
          category: 'fiscal_balance',
          ministry_code: null,
          source_page: 8,
        },
      ],
      notable_topics: ['Fiscal update', 'Year-to-date performance'],
      warnings: [],
      confidence: 0.88,
      needs_review: false,
    },
  },
  debt_report: {
    description: 'Debt reports with totals, debt mix, creditors, and debt-to-GDP context.',
    expectedExample: {
      source_document: 'Debt_Report_2025_26.pdf',
      title: 'Debt Report 2025/26',
      document_type: 'debt_report',
      fiscal_year: '2025/26',
      executive_summary: 'Government debt position and composition.',
      ministries: [],
      extracted_items: [
        {
          label: 'Total public debt',
          amount: 12000000000,
          currency: 'BSD',
          category: 'total_debt',
          ministry_code: null,
          source_page: 4,
        },
      ],
      notable_topics: ['Domestic debt', 'External debt'],
      warnings: [],
      confidence: 0.9,
      needs_review: false,
    },
  },
  health_strategy: {
    description: 'Health strategy and planning documents with goals, programs, and service themes.',
    expectedExample: {
      source_document: 'Bahamas National Health Strategy FINAL (08Dec2025).pdf',
      title: 'Bahamas National Health Strategy',
      document_type: 'health_strategy',
      fiscal_year: null,
      executive_summary: 'National health strategy outlining priority goals and service directions.',
      ministries: ['Ministry of Health'],
      extracted_items: [
        {
          label: 'Primary care access',
          amount: null,
          currency: 'BSD',
          category: 'policy_priority',
          ministry_code: null,
          source_page: 14,
        },
      ],
      notable_topics: ['Primary care', 'Health system reform'],
      warnings: [],
      confidence: 0.87,
      needs_review: false,
    },
  },
  economic_indicators: {
    description: 'Household affordability and income indicators by island, class, and year.',
    expectedExample: {
      source_document: 'Household_Indicators_2025_26.json',
      title: 'Household Economy Indicators 2025/26',
      document_type: 'economic_indicators',
      fiscal_year: '2025/26',
      economic_indicators: [
        {
          indicator_type: 'middle_class',
          island: 'new_providence',
          year: 2025,
          month_amount: 10450,
          annual_amount: 125400,
          breakdown: {
            food: 2600,
            housing_utilities: 2200,
            nfnh: 3550,
            savings: 2100,
          },
          source_document: 'Household_Indicators_2025_26.json',
          source_url: 'https://source.example.gov.bs/economy/household-indicators',
          author: 'Department of Statistics',
          published_date: '2025-07-01',
        },
      ],
      warnings: [],
      confidence: 0.95,
      needs_review: false,
    },
  },
  island_projects: {
    description: 'Island-level allocations with project lists for map and regional project views.',
    expectedExample: {
      source_document: 'Island_Projects_2025_26.json',
      title: 'Island Projects 2025/26',
      document_type: 'island_projects',
      fiscal_year: '2025/26',
      islands: [
        {
          id: 'new-providence',
          name: 'New Providence',
          capital: 'Nassau',
          population: 274400,
          allocation: 1500000000,
          projects: [
            { name: 'Princess Margaret Hospital Expansion', amount: 45000000, category: 'health' },
            { name: 'New Government Complex', amount: 80000000, category: 'infrastructure' },
          ],
        },
      ],
      warnings: [],
      confidence: 0.94,
      needs_review: false,
    },
  },
  news_update: {
    description: 'Official update and announcement entries used in the public news feed.',
    expectedExample: {
      source_document: 'Public_Updates_2025_07.json',
      title: 'Public Updates July 2025',
      document_type: 'news_update',
      fiscal_year: '2025/26',
      news_items: [
        {
          title: 'Budget debate opens in Parliament',
          source: 'Ministry of Finance',
          url: 'https://source.example.gov.bs/news/budget-debate-opens',
          published_date: '2025-07-12',
          summary: 'Parliament opened debate on the 2025/26 budget with a focus on growth and health spending.',
          category: 'Budget',
        },
      ],
      warnings: [],
      confidence: 0.96,
      needs_review: false,
    },
  },
  procurement_report: {
    description: 'Oversight and procurement reports with findings, case references, and notable issues.',
    expectedExample: {
      source_document: 'FieldingandBallanceSweethearting2023FINAL.pdf',
      title: 'Sweethearting in Public Procurement',
      document_type: 'procurement_report',
      fiscal_year: null,
      executive_summary: 'Oversight report summarizing procurement concerns and findings.',
      ministries: [],
      extracted_items: [
        {
          label: 'Restricted bidding concern',
          amount: null,
          currency: 'BSD',
          category: 'finding',
          ministry_code: null,
          source_page: 5,
        },
      ],
      notable_topics: ['Procurement governance', 'Oversight findings'],
      warnings: [],
      confidence: 0.86,
      needs_review: true,
    },
  },
  legal_ruling: {
    description: 'Court awards, rulings, and legal guidance documents summarized into structured references.',
    expectedExample: {
      source_document: '20260227_Government-of-The-Bahamas-v-GBPA-Partial-Final-Award_vF-Signed.pdf',
      title: 'GBPA Partial Final Award',
      document_type: 'legal_ruling',
      fiscal_year: '2026/02',
      executive_summary: 'Legal ruling with summarized issues, findings, and award details.',
      ministries: [],
      extracted_items: [
        {
          label: 'Partial final award',
          amount: null,
          currency: 'BSD',
          category: 'legal_finding',
          ministry_code: null,
          source_page: 1,
        },
      ],
      notable_topics: ['GBPA', 'Arbitration award'],
      warnings: [],
      confidence: 0.84,
      needs_review: true,
    },
  },
  other: {
    description: 'Catch-all record type for documents that do not fit a named type yet.',
    expectedExample: {
      source_document: 'other-document.pdf',
      title: 'Other document',
      document_type: 'other',
      fiscal_year: null,
      executive_summary: 'Short summary of the document.',
      ministries: [],
      extracted_items: [],
      notable_topics: [],
      warnings: [],
      confidence: 0.8,
      needs_review: true,
    },
  },
};

export const adminCollections = adminSections;

export type AdminSectionId = AdminSection['id'];
export type AdminCollectionId = AdminSectionId;

export function isAdminSectionId(value: string): value is AdminSectionId {
  return adminSections.some((section) => section.id === value);
}

export function formatDocumentType(value?: string | null) {
  if (!value) {
    return 'Other';
  }
  return documentTypeLabels[value] ?? value.replaceAll('_', ' ');
}

export function formatReviewStatus(value?: string | null) {
  if (!value) {
    return 'Waiting for review';
  }

  const labels: Record<string, string> = {
    waiting_for_processing: 'Waiting for processing',
    pending_review: 'Ready for review',
    approved: 'Approved',
    changes_requested: 'Needs changes',
  };

  return labels[value] ?? value.replaceAll('_', ' ');
}

export function getSectionById(sectionId: AdminSectionId) {
  return adminSections.find((section) => section.id === sectionId) ?? adminSections[0];
}

export function isDocumentType(value: string): value is DocumentType {
  return documentTypes.some(([type]) => type === value);
}

export function getDocumentTypeDetails(type: DocumentType) {
  return documentTypeDetails[type];
}

export function getCollectionById(sectionId: AdminCollectionId) {
  return getSectionById(sectionId);
}

export function getSectionForDocumentType(documentType?: string | null) {
  const normalized = (documentType ?? 'other') as DocumentType;
  return (
    adminSections.find((section) =>
      section.documentTypes.includes(normalized),
    ) ?? adminSections[adminSections.length - 1]
  );
}

export function getCollectionForDocumentType(documentType?: string | null) {
  return getSectionForDocumentType(documentType);
}

export function getSectionDocuments(
  documents: DocumentRecord[],
  sectionId: AdminSectionId | 'all',
) {
  if (sectionId === 'all') {
    return documents;
  }

  const section = getSectionById(sectionId);
  return documents.filter((document) =>
    section.documentTypes.includes((document.document_type ?? 'other') as DocumentType),
  );
}

export function getCollectionDocuments(
  documents: DocumentRecord[],
  collectionId: AdminCollectionId | 'all',
) {
  return getSectionDocuments(documents, collectionId);
}

export function getSectionSummary(documents: DocumentRecord[]) {
  return adminSections.map((section) => {
    const matchingDocuments = getSectionDocuments(documents, section.id);
    const presentTypes = new Set(
      matchingDocuments.map((document) => (document.document_type ?? 'other') as DocumentType),
    );
    const missingTypes = section.documentTypes.filter((type) => !presentTypes.has(type));

    return {
      ...section,
      count: matchingDocuments.length,
      matchingDocuments,
      missingTypes,
      extractedCount: matchingDocuments.filter((document) => document.extraction_status === 'success').length,
      normalizedCount: matchingDocuments.filter((document) => document.normalization_status === 'success').length,
      approvedCount: matchingDocuments.filter((document) => document.review_status === 'approved').length,
    };
  });
}

export function getCollectionSummary(documents: DocumentRecord[]) {
  return getSectionSummary(documents);
}
