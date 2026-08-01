'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Building2,
  ExternalLink,
  FileText,
  Landmark,
  MapPin,
  Users,
} from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import StatCard from '@/components/StatCard';
import ResponsiveContainer from '@/components/SafeResponsiveContainer';
import { grandBahamaDataset } from '@/data/grandBahama';
import type { GrandBahamaDataset } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';
const PARTY_COLORS: Record<string, string> = {
  PLP: '#00CED1',
  FNM: '#FCD116',
};

function isValidDataset(data: unknown): data is GrandBahamaDataset {
  if (!data || typeof data !== 'object') return false;
  const d = data as GrandBahamaDataset;
  return Boolean(d.meta && d.ministry && Array.isArray(d.mps) && Array.isArray(d.districts));
}

export default function GrandBahamaPage() {
  const [data, setData] = useState<GrandBahamaDataset | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch(`${API_BASE}/grand-bahama`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const payload = await res.json();
        if (!isValidDataset(payload)) throw new Error('Invalid payload');
        setData(payload);
      } catch (error) {
        console.warn('Grand Bahama API unavailable, using fallback data', error);
        setData(grandBahamaDataset);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading || !data) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <p className="text-gray-500">Loading Grand Bahama institutional data...</p>
        </div>
      </div>
    );
  }

  const { meta, ministry, mps, districts, local_government_context: lg } = data;
  const plpCount = mps.filter((m) => m.party === 'PLP').length;
  const fnmCount = mps.filter((m) => m.party === 'FNM').length;
  const partyChartData = [
    { name: 'PLP', value: plpCount },
    { name: 'FNM', value: fnmCount },
  ];
  const confirmedOfficers = districts.filter(
    (d) => d.chief_councillor || d.secretary,
  ).length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Grand <span className="text-turquoise">Bahama</span>
        </h1>
        <p className="text-gray-600 max-w-3xl">
          Institutional reference for the Ministry for Grand Bahama, the island&apos;s
          parliamentary delegation, and local-government districts — structured and
          citable public records that are not available as a digital roster elsewhere.
        </p>
        <p className="text-xs text-gray-400 mt-2">As of {meta.as_of}</p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 rounded-xl border border-turquoise/20 bg-turquoise/5 p-5"
      >
        <p className="text-sm text-gray-700 leading-relaxed">{meta.framing}</p>
      </motion.div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard title="House seats (GB)" value={mps.length} format="number" subtitle="Constituencies" />
        <StatCard
          title="Party split"
          value={plpCount}
          format="number"
          subtitle={`${plpCount} PLP · ${fnmCount} FNM`}
        />
        <StatCard
          title="Local gov districts"
          value={districts.length}
          format="number"
          subtitle={`of ${lg.national_district_count} nationally`}
        />
        <StatCard
          title="Named officers (public)"
          value={confirmedOfficers}
          format="number"
          subtitle="Confirmed in public reporting only"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-6"
        >
          <div className="flex items-start gap-3 mb-4">
            <div className="w-9 h-9 rounded-full bg-turquoise/10 flex items-center justify-center flex-shrink-0">
              <Landmark className="w-4 h-4 text-turquoise" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">{ministry.name}</h2>
              <p className="text-sm text-gray-600">
                {ministry.minister} · {ministry.constituency} ({ministry.party})
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-600 mb-5">
            <span className="inline-flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-turquoise" />
              {ministry.office.building}, {ministry.office.city}
            </span>
            <span>{ministry.office.phone}</span>
            <span>
              In office since {ministry.in_office_since}; reappointed {ministry.reappointed}
            </span>
          </div>

          <h3 className="text-sm font-semibold text-gray-900 mb-3 uppercase tracking-wide">
            Portfolio ({ministry.portfolio.length})
          </h3>
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4">
            {ministry.portfolio.map((item) => (
              <li
                key={item}
                className="text-sm text-gray-700 pl-3 border-l-2 border-turquoise/40"
              >
                {item}
              </li>
            ))}
          </ul>

          <div className="space-y-1 mb-4">
            {ministry.notes.map((note) => (
              <p key={note} className="text-xs text-gray-500">
                {note}
              </p>
            ))}
          </div>

          <a
            href={ministry.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs text-turquoise hover:underline"
          >
            <FileText className="w-3.5 h-3.5" />
            {ministry.source}
            <ExternalLink className="w-3 h-3" />
          </a>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.05 }}
          className="bg-white rounded-xl border border-gray-200 p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">GB delegation by party</h3>
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={partyChartData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                >
                  {partyChartData.map((entry) => (
                    <Cell key={entry.name} fill={PARTY_COLORS[entry.name] || '#94a3b8'} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Split 2 PLP / 3 FNM after the May 12, 2026 general election.
          </p>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl border border-gray-200 p-6 mb-8"
      >
        <div className="flex items-center gap-2 mb-4">
          <Users className="w-5 h-5 text-turquoise" />
          <h2 className="text-lg font-semibold text-gray-900">
            Parliamentary delegation
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs uppercase tracking-wide text-gray-500">
                <th className="py-2 pr-4 font-semibold">Constituency</th>
                <th className="py-2 pr-4 font-semibold">MP</th>
                <th className="py-2 pr-4 font-semibold">Party</th>
                <th className="py-2 font-semibold">Role</th>
              </tr>
            </thead>
            <tbody>
              {mps.map((mp) => (
                <tr key={mp.constituency} className="border-b border-gray-100 last:border-0">
                  <td className="py-3 pr-4 text-gray-900 font-medium">{mp.constituency}</td>
                  <td className="py-3 pr-4 text-gray-700">{mp.name}</td>
                  <td className="py-3 pr-4">
                    <span
                      className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                        mp.party === 'PLP'
                          ? 'bg-turquoise/10 text-turquoise'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {mp.party}
                    </span>
                  </td>
                  <td className="py-3 text-gray-600">{mp.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <a
          href={mps[0]?.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-xs text-turquoise hover:underline mt-4"
        >
          <FileText className="w-3.5 h-3.5" />
          {mps[0]?.source}
          <ExternalLink className="w-3 h-3" />
        </a>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-2 mb-2">
          <Building2 className="w-5 h-5 text-turquoise" />
          <h2 className="text-lg font-semibold text-gray-900">
            Local-government districts
          </h2>
        </div>
        <p className="text-sm text-gray-600 mb-4 max-w-3xl">
          Under the {lg.governing_act} ({lg.act_in_force}), administered by the{' '}
          {lg.overseeing_department} ({lg.overseeing_ministry}). Last election{' '}
          {lg.last_election}; next expected {lg.next_election_expected}. Officer names
          appear only where publicly confirmed — most district rosters are not published
          as structured open data.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {districts.map((district, index) => (
            <motion.div
              key={district.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.04 }}
              className="bg-white rounded-xl border border-gray-200 p-5"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <h3 className="font-semibold text-gray-900">{district.name}</h3>
                <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded bg-gray-100 text-gray-600 whitespace-nowrap">
                  {district.schedule === 'third' ? '3rd schedule' : '2nd schedule'}
                </span>
              </div>
              <p className="text-xs text-gray-500 mb-3">{district.schedule_note}</p>
              <dl className="space-y-1.5 text-sm">
                <div className="flex justify-between gap-2">
                  <dt className="text-gray-500">Chief Councillor</dt>
                  <dd className="text-gray-900 text-right">
                    {district.chief_councillor ?? (
                      <span className="text-gray-400 italic">Not publicly confirmed</span>
                    )}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-gray-500">Secretary</dt>
                  <dd className="text-gray-900 text-right">
                    {district.secretary ?? (
                      <span className="text-gray-400 italic">Not publicly confirmed</span>
                    )}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-gray-500">Roster status</dt>
                  <dd className="text-gray-700 capitalize text-right">{district.officers_status}</dd>
                </div>
              </dl>
            </motion.div>
          ))}
        </div>
        <a
          href={lg.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-xs text-turquoise hover:underline mt-4"
        >
          <FileText className="w-3.5 h-3.5" />
          {lg.source}
          <ExternalLink className="w-3 h-3" />
        </a>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl border border-gray-200 p-6"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Related reports</h2>
          <p className="text-sm text-gray-600 mb-4">
            Existing Hot Topics on the February 2026 Hawksbill Creek arbitration — grounding
            for a government-owned GB data layer alongside GBPA&apos;s Port Area map.
          </p>
          <ul className="space-y-3">
            {meta.related_hot_topics.map((topic) => (
              <li key={topic.slug}>
                <Link
                  href={`/hot/${topic.slug}`}
                  className="text-sm font-medium text-turquoise hover:underline inline-flex items-center gap-1.5"
                >
                  {topic.title}
                  <ExternalLink className="w-3.5 h-3.5" />
                </Link>
              </li>
            ))}
          </ul>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl border border-gray-200 p-6"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Related authority</h2>
          <ul className="space-y-4">
            {meta.related_authorities.map((auth) => (
              <li key={auth.name}>
                <p className="text-sm font-medium text-gray-900">{auth.name}</p>
                <p className="text-xs text-turquoise mb-1">{auth.role}</p>
                <p className="text-sm text-gray-600">{auth.note}</p>
              </li>
            ))}
          </ul>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rounded-xl border border-gray-200 bg-gray-50 p-5"
      >
        <h3 className="text-sm font-semibold text-gray-900 mb-2">Methodology & export</h3>
        <p className="text-sm text-gray-600 mb-3">{meta.methodology}</p>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/export"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-turquoise hover:underline"
          >
            Export Grand Bahama dataset (CSV / JSON)
            <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
