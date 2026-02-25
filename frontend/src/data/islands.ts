export type IslandProjectCategory =
  | 'education'
  | 'health'
  | 'security'
  | 'infrastructure'
  | string;

export interface IslandProject {
  name: string;
  amount: number;
  category: IslandProjectCategory;
}

export interface Island {
  id: string;
  name: string;
  capital: string;
  population: number;
  allocation: number;
  projects: IslandProject[];
}

export const islands: Island[] = [
  {
    id: 'new-providence',
    name: 'New Providence',
    capital: 'Nassau',
    population: 274400,
    allocation: 1_500_000_000,
    projects: [
      { name: 'Princess Margaret Hospital Expansion', amount: 45_000_000, category: 'health' },
      { name: 'New Government Complex', amount: 80_000_000, category: 'infrastructure' },
      { name: 'School Renovation Program', amount: 25_000_000, category: 'education' },
      { name: 'Police Station Upgrades', amount: 12_000_000, category: 'security' },
    ],
  },
  {
    id: 'grand-bahama',
    name: 'Grand Bahama',
    capital: 'Freeport',
    population: 51368,
    allocation: 280_000_000,
    projects: [
      { name: 'Rand Memorial Hospital Repairs', amount: 18_000_000, category: 'health' },
      { name: 'Hurricane Recovery Infrastructure', amount: 35_000_000, category: 'infrastructure' },
      { name: 'Eight Mile Rock Schools', amount: 8_000_000, category: 'education' },
    ],
  },
  {
    id: 'abaco',
    name: 'Abaco',
    capital: 'Marsh Harbour',
    population: 17224,
    allocation: 150_000_000,
    projects: [
      { name: 'Dorian Recovery Reconstruction', amount: 65_000_000, category: 'infrastructure' },
      { name: 'Marsh Harbour Clinic', amount: 8_000_000, category: 'health' },
      { name: 'School Rebuilding', amount: 12_000_000, category: 'education' },
    ],
  },
  {
    id: 'eleuthera',
    name: 'Eleuthera',
    capital: "Governor's Harbour",
    population: 11165,
    allocation: 85_000_000,
    projects: [
      { name: 'Road Rehabilitation', amount: 15_000_000, category: 'infrastructure' },
      { name: 'Glass Window Bridge Repair', amount: 8_000_000, category: 'infrastructure' },
      { name: 'Community Clinics', amount: 5_000_000, category: 'health' },
    ],
  },
  {
    id: 'exuma',
    name: 'Exuma',
    capital: 'George Town',
    population: 7314,
    allocation: 65_000_000,
    projects: [
      { name: 'Airport Expansion', amount: 25_000_000, category: 'infrastructure' },
      { name: 'New School Construction', amount: 12_000_000, category: 'education' },
    ],
  },
  {
    id: 'andros',
    name: 'Andros',
    capital: 'Fresh Creek',
    population: 7386,
    allocation: 55_000_000,
    projects: [
      { name: 'Road Network Improvements', amount: 18_000_000, category: 'infrastructure' },
      { name: 'AUTEC Support Facilities', amount: 10_000_000, category: 'security' },
    ],
  },
  {
    id: 'long-island',
    name: 'Long Island',
    capital: 'Clarence Town',
    population: 3094,
    allocation: 28_000_000,
    projects: [
      { name: 'Seawall Construction', amount: 8_000_000, category: 'infrastructure' },
      { name: 'School Improvements', amount: 3_000_000, category: 'education' },
    ],
  },
  {
    id: 'cat-island',
    name: 'Cat Island',
    capital: "Arthur's Town",
    population: 1522,
    allocation: 22_000_000,
    projects: [
      { name: 'Airport Upgrades', amount: 6_000_000, category: 'infrastructure' },
      { name: 'Healthcare Clinic', amount: 4_000_000, category: 'health' },
    ],
  },
];

