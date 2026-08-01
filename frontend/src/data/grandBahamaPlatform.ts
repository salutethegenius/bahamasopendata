import type { LucideIcon } from 'lucide-react';
import {
  Brain,
  ClipboardList,
  Landmark,
  LayoutDashboard,
  Map,
  MonitorSmartphone,
} from 'lucide-react';

export type PlatformModuleStatus = 'live' | 'planned';

export type PlatformModule = {
  id: string;
  number: string;
  title: string;
  subtitle: string;
  description: string;
  status: PlatformModuleStatus;
  href?: string;
  buyer: string;
  capability: string;
  icon: LucideIcon;
};

export const grandBahamaPlatform = {
  name: 'Grand Bahama Digital Government Platform',
  tagline:
    'Digital infrastructure for the Ministry for Grand Bahama — open data, services, case workflow, and secure AI — starting with a live institutional module.',
  positioning:
    'This is not a one-off dashboard. It is Module 1 of a Digital Government Platform: the same capability pattern used for Banking Sector–style open-data intelligence, scoped to Grand Bahama and designed to grow into case management, citizen services, and ministry knowledge assistants.',
  complementaryNote:
    'Invest Grand Bahama (GBPA) covers investment activity inside the Port Area. This platform is the government-side layer — complementary, not competing — for institutional structure, program visibility, and eventually service delivery.',
  buyers: [
    {
      ministry: 'Ministry for Grand Bahama',
      focus: 'Growth, employment, community engagement, and a public GB data layer',
    },
    {
      ministry: 'Ministry of Works & Family Island Affairs',
      focus: 'Local government districts, town committees, and case/service workflows',
    },
    {
      ministry: 'Ministry of Innovation & National Development',
      focus: 'National digital infrastructure, e-government, and secure AI',
    },
  ],
};

export const platformModules: PlatformModule[] = [
  {
    id: 'institutional',
    number: '01',
    title: 'Institutional Reference',
    subtitle: 'Open data intelligence',
    description:
      'Ministry portfolio, parliamentary delegation, and local-government districts — structured, citable, and exportable. The public gap filled first.',
    status: 'live',
    href: '/grand-bahama/institutional',
    buyer: 'Ministry for Grand Bahama',
    capability: 'Dashboards / Open Data',
    icon: Landmark,
  },
  {
    id: 'ministry-dashboard',
    number: '02',
    title: 'Ministry Performance Dashboard',
    subtitle: 'Employment, investment, programs',
    description:
      'Interactive tracking for employment, entrepreneurial programs, housing, road projects, tourism, and grants — scoped to mandate lines the Ministry already owns.',
    status: 'planned',
    buyer: 'Ministry for Grand Bahama',
    capability: 'Dashboards / Analytics',
    icon: LayoutDashboard,
  },
  {
    id: 'local-government',
    number: '03',
    title: 'Local Government Roster',
    subtitle: 'Districts & town committees',
    description:
      'Per-district representatives, committees, elections, budgets, notices, and contacts — the digital roster DLG does not publish today.',
    status: 'planned',
    buyer: 'Works & Family Island Affairs / DLG',
    capability: 'Dashboards / Open Data',
    icon: Map,
  },
  {
    id: 'case-management',
    number: '04',
    title: 'Case & Complaint Workflow',
    subtitle: 'Citizen → assigned → closed',
    description:
      'Government case management for complaints, inspections, and follow-ups — the same workflow pattern as CRM, framed for public agencies.',
    status: 'planned',
    buyer: 'Local Government & Ministries',
    capability: 'KRM Desk',
    icon: ClipboardList,
  },
  {
    id: 'citizen-services',
    number: '05',
    title: 'Citizen & Permit Services',
    subtitle: 'Applications & service delivery',
    description:
      'Digital intake for permits, licenses, vendor registration, grants, and FOIA-style requests — portal engine, government skin.',
    status: 'planned',
    buyer: 'Ministries & Local Authorities',
    capability: 'BACO Portal',
    icon: MonitorSmartphone,
  },
  {
    id: 'knowledge-ai',
    number: '06',
    title: 'Ministry Knowledge Assistants',
    subtitle: 'Domain AI & secure local AI',
    description:
      'Domain-specific AI for policy, procedures, and archives — with a path to sovereign, on-prem assistants where cloud is not appropriate.',
    status: 'planned',
    buyer: 'Innovation & National Development',
    capability: 'LawBey / VerityOS',
    icon: Brain,
  },
];
