'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from 'recharts';
import { ClipboardCheck, MapPin } from 'lucide-react';
import ResponsiveContainer from '@/components/SafeResponsiveContainer';
import {
  currentScorecard,
  type GeographicIssueRow,
  type ScorecardRegion,
} from '@/data/scorecards';

function gradeBand(grade: string): 'A' | 'B' | 'C' | 'D' | 'other' {
  const match = grade.trim().match(/^[A-D]/i);
  if (!match) return 'other';
  return match[0].toUpperCase() as 'A' | 'B' | 'C' | 'D';
}

function gradePillClass(grade: string): string {
  switch (gradeBand(grade)) {
    case 'A':
      return 'bg-turquoise/10 text-turquoise-dark';
    case 'B':
      return 'bg-blue-50 text-blue-800';
    case 'C':
      return 'bg-yellow/20 text-yellow-dark';
    case 'D':
      return 'bg-red-50 text-red-700';
    default:
      return 'bg-gray-100 text-gray-700';
  }
}

function GradePill({ grade, size = 'sm' }: { grade: string; size?: 'sm' | 'lg' }) {
  return (
    <span
      className={`inline-flex items-center justify-center font-semibold whitespace-nowrap rounded-full ${gradePillClass(grade)} ${
        size === 'lg' ? 'text-4xl px-5 py-2 min-w-[4.5rem]' : 'text-xs px-2.5 py-1'
      }`}
    >
      {grade}
    </span>
  );
}

function regionGrade(row: GeographicIssueRow, regionId: ScorecardRegion['id']): string {
  if (regionId === 'grand-bahama') return row.grandBahama;
  if (regionId === 'abaco') return row.abaco;
  return row.newProvidence;
}

export default function ScorecardsPage() {
  const card = currentScorecard;
  const crimeArea = card.areas.find((area) => area.id === 'crime');
  const highlightIssueIds = ['tourism', 'electricity-cost', 'electricity-reliability'];
  const highlightIssues = card.geographicIssues.filter((row) =>
    highlightIssueIds.includes(row.id),
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Government <span className="text-turquoise">Scorecards</span>
        </h1>
        <p className="text-gray-600">{card.subtitle}</p>
        <p className="mt-3 max-w-3xl text-sm text-gray-500">
          Independent assessment, assessed {card.assessedOnLabel}. Letter grades are editorial.
          Figures are cited to the source named under each stat. They are not official budget-book
          numbers.
        </p>
      </motion.div>

      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl border border-gray-200 p-6 md:p-8 mb-8"
      >
        <div className="flex flex-col md:flex-row md:items-start gap-6">
          <div className="flex-shrink-0">
            <p className="text-[11px] uppercase tracking-wide text-gray-500 mb-2">
              Overall, first term
            </p>
            <GradePill grade={card.overall.firstTerm} size="lg" />
            <p className="mt-2 text-xs text-gray-500">
              Second term {card.overall.secondTerm} {card.overall.secondTermNote}
            </p>
          </div>
          <div className="min-w-0">
            <p className="text-lg md:text-xl font-semibold text-gray-900 leading-snug">
              “{card.thesis}”
            </p>
            <p className="mt-3 text-sm text-gray-600 leading-relaxed">{card.verdict}</p>
            <p className="mt-3 text-xs text-gray-500">{card.overall.direction}</p>
          </div>
        </div>
      </motion.section>

      <section className="mb-10">
        <h2 className="text-xl font-bold text-gray-900 mb-4">National grades</h2>
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-left text-[11px] uppercase tracking-wide text-gray-500">
                  <th className="px-4 py-3 font-medium">Area</th>
                  <th className="px-4 py-3 font-medium">2021–2026 first term</th>
                  <th className="px-4 py-3 font-medium">Opening of second term</th>
                  <th className="px-4 py-3 font-medium">Direction</th>
                </tr>
              </thead>
              <tbody>
                {card.areas.map((area) => (
                  <tr key={area.id} className="border-b border-gray-50 last:border-0">
                    <td className="px-4 py-3">
                      <a
                        href={`#${area.id}`}
                        className="font-medium text-gray-900 hover:text-turquoise"
                      >
                        {area.name}
                      </a>
                    </td>
                    <td className="px-4 py-3">
                      <GradePill grade={area.firstTerm} />
                    </td>
                    <td className="px-4 py-3">
                      <GradePill grade={area.secondTerm} />
                    </td>
                    <td className="px-4 py-3 text-gray-600">{area.direction}</td>
                  </tr>
                ))}
                <tr className="bg-gray-50">
                  <td className="px-4 py-3 font-semibold text-gray-900">Overall</td>
                  <td className="px-4 py-3">
                    <GradePill grade={card.overall.firstTerm} />
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1.5">
                      <GradePill grade={card.overall.secondTerm} />
                      <span className="text-xs text-gray-500">{card.overall.secondTermNote}</span>
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{card.overall.direction}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mb-10">
        <div className="flex items-end justify-between gap-4 mb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Geographic comparison</h2>
            <p className="text-sm text-gray-500 mt-1">
              The national average hides three different Bahamian experiences.
            </p>
          </div>
          <Link href="/map" className="text-sm text-turquoise hover:underline shrink-0">
            Open map
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {card.regions.map((region) => (
            <motion.div
              key={region.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col"
            >
              <div className="flex items-start justify-between gap-3 mb-3">
                <div>
                  <div className="flex items-center gap-2 text-gray-500 mb-1">
                    <MapPin className="w-3.5 h-3.5" />
                    <span className="text-[11px] uppercase tracking-wide">Island</span>
                  </div>
                  <h3 className="text-base font-semibold text-gray-900">{region.name}</h3>
                  <p className="text-xs text-gray-500 mt-1">{region.overall}</p>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  {region.firstTerm && <GradePill grade={region.firstTerm} />}
                  {region.secondTerm && region.secondTerm !== region.firstTerm && (
                    <GradePill grade={region.secondTerm} />
                  )}
                  {!region.firstTerm && !region.secondTerm && (
                    <GradePill grade={region.overall} />
                  )}
                </div>
              </div>
              <dl className="space-y-2 mb-4">
                {highlightIssues.map((row) => (
                  <div key={row.id} className="flex items-center justify-between gap-3">
                    <dt className="text-xs text-gray-500">{row.label}</dt>
                    <dd>
                      <GradePill grade={regionGrade(row, region.id)} />
                    </dd>
                  </div>
                ))}
              </dl>
              <p className="text-sm text-gray-600 leading-relaxed flex-1">{region.verdict}</p>
              <Link
                href={region.href}
                className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500 hover:text-turquoise"
              >
                See capital projects on the map →
              </Link>
            </motion.div>
          ))}
        </div>
      </section>

      {crimeArea?.chart && (
        <section className="mb-10">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-1">{crimeArea.chart.title}</h2>
            <p className="text-xs text-gray-500 mb-4">Source: Police</p>
            <div className="h-72 w-full min-w-0">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={crimeArea.chart.points}
                  margin={{ top: 8, right: 8, left: 12, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    allowDecimals={false}
                    label={{
                      value: 'Murders',
                      angle: -90,
                      position: 'insideLeft',
                      style: { fontSize: 11, fill: '#6b7280' },
                    }}
                  />
                  <Tooltip
                    formatter={(value: number) => [`${value} ${crimeArea.chart?.unit}`, 'Murders']}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                  />
                  <Bar dataKey="value" fill="#00CED1" radius={[4, 4, 0, 0]} name="Murders" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>
      )}

      <section className="space-y-4">
        <h2 className="text-xl font-bold text-gray-900">By policy area</h2>
        {card.areas.map((area) => (
          <motion.article
            key={area.id}
            id={area.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl border border-gray-200 p-5 scroll-mt-28"
          >
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-3">
              <div>
                <h3 className="text-base font-semibold text-gray-900">{area.name}</h3>
                <p className="text-xs text-gray-500 mt-0.5">{area.direction}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] uppercase tracking-wide text-gray-400">First term</span>
                <GradePill grade={area.firstTerm} />
                <span className="text-[11px] uppercase tracking-wide text-gray-400 ml-2">
                  Second term
                </span>
                <GradePill grade={area.secondTerm} />
              </div>
            </div>
            <p className="text-sm text-gray-600 leading-relaxed mb-4">{area.verdict}</p>
            {area.stats.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {area.stats.map((stat) => (
                  <div
                    key={stat.label}
                    className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-3"
                  >
                    <p className="text-[11px] uppercase tracking-wide text-gray-500 mb-1">
                      {stat.label}
                    </p>
                    <p className="text-sm font-semibold text-gray-900">{stat.display}</p>
                    <p className="text-[11px] text-gray-400 mt-1">Source: {stat.source}</p>
                  </div>
                ))}
              </div>
            )}
            {area.relatedHref && (
              <Link
                href={area.relatedHref}
                className="inline-block mt-4 text-sm text-turquoise hover:underline"
              >
                See related data →
              </Link>
            )}
          </motion.article>
        ))}
      </section>

      <p className="mt-8 text-xs text-gray-400">
        <ClipboardCheck className="w-3.5 h-3.5 inline mr-1 align-text-bottom" />
        Assessment of the Davis administration, September 2021 – August 2026. Not an official
        government publication.
      </p>
    </div>
  );
}
