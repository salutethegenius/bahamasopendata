'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  CartesianGrid,
  Cell,
} from 'recharts';
import {
  Flame,
  FileText,
  ExternalLink,
  ArrowLeft,
  TrendingUp,
  BookOpen,
  BarChart3,
  Users,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

type KeyStat = { label: string; value: number; unit: string };
type ChartPoint = { name: string; [key: string]: string | number };
type ChartDef = {
  id: string;
  title: string;
  type: string;
  data: ChartPoint[];
};

type Report = {
  slug: string;
  title: string;
  source: string;
  year: string;
  journal?: string;
  pdf_filename: string;
  overview?: string;
  methodology?: string;
  highlights: string[];
  key_stats: KeyStat[];
  charts?: ChartDef[];
  chart_data?: ChartPoint[];
};

const CHART_COLORS = ['#00CED1', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8'];
const BAR_PAIR = ['#00CED1', '#FF6B6B'];

function StatCard({ stat, index }: { stat: KeyStat; index: number }) {
  const formatted =
    stat.unit === '%'
      ? `${stat.value}%`
      : stat.unit === 'women' || stat.unit === 'respondents'
      ? stat.value.toLocaleString()
      : `${stat.value}${stat.unit ? ` ${stat.unit}` : ''}`;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.05 }}
      className="bg-white rounded-xl border border-gray-200 p-5 hover:border-turquoise/40 transition-colors"
    >
      <p className="text-sm text-gray-500 mb-2 leading-snug">{stat.label}</p>
      <p className="text-3xl font-bold text-gray-900 tabular-nums">{formatted}</p>
    </motion.div>
  );
}

function MultiBarChart({ chart }: { chart: ChartDef }) {
  const sampleRow = chart.data[0] || {};
  const seriesKeys = Object.keys(sampleRow).filter((k) => k !== 'name');

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl border border-gray-200 p-5"
    >
      <h3 className="text-base font-semibold text-gray-800 mb-4">{chart.title}</h3>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chart.data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11 }}
              interval={0}
              angle={-20}
              textAnchor="end"
              height={60}
            />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ borderRadius: 8, border: '1px solid #e5e7eb', fontSize: 13 }}
              formatter={(value: number, name: string) => [`${value}%`, name]}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {seriesKeys.map((key, i) => (
              <Bar
                key={key}
                dataKey={key}
                fill={BAR_PAIR[i] ?? CHART_COLORS[i % CHART_COLORS.length]}
                radius={[4, 4, 0, 0]}
                name={key}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}

export default function HotTopicReportPage() {
  const params = useParams();
  const slug = typeof params.slug === 'string' ? params.slug : '';
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAllHighlights, setShowAllHighlights] = useState(false);

  useEffect(() => {
    if (!slug) return;
    async function fetchReport() {
      try {
        setLoading(true);
        setError(null);
        const res = await fetch(`${API_BASE}/hot-topics/reports/${encodeURIComponent(slug)}`);
        if (!res.ok) throw new Error('Report not found');
        const data = await res.json();
        setReport(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load report.');
      } finally {
        setLoading(false);
      }
    }
    fetchReport();
  }, [slug]);

  const pdfUrl = report?.pdf_filename
    ? `/documents/${encodeURIComponent(report.pdf_filename)}`
    : '';

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-16">
          <div className="w-8 h-8 border-2 border-turquoise border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-xl p-5 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />
          <div>
            <p className="font-semibold text-red-800">Report could not be loaded</p>
            <p className="text-sm text-red-700 mt-1">{error ?? 'Report not found.'}</p>
          </div>
        </div>
        <Link href="/hot" className="text-turquoise hover:underline mt-4 inline-block">
          Back to Hot Topics
        </Link>
      </div>
    );
  }

  const INITIAL_HIGHLIGHTS = 5;
  const visibleHighlights = showAllHighlights
    ? report.highlights
    : report.highlights.slice(0, INITIAL_HIGHLIGHTS);
  const hasMore = report.highlights.length > INITIAL_HIGHLIGHTS;

  const charts = report.charts ?? [];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      {/* Back link */}
      <Link
        href="/hot"
        className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-turquoise transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Hot Topics
      </Link>

      {/* Header */}
      <motion.header initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex flex-wrap items-center gap-2 text-sm text-gray-500 mb-2">
          {report.year && (
            <span className="bg-turquoise/10 text-turquoise px-2 py-0.5 rounded-full text-xs font-medium">
              {report.year}
            </span>
          )}
          <span>{report.source}</span>
          {report.journal && <span className="text-gray-400">· {report.journal}</span>}
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">{report.title}</h1>
        {pdfUrl && (
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-turquoise hover:underline text-sm font-medium"
          >
            <FileText className="w-4 h-4" />
            View full PDF report
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </motion.header>

      {/* Overview */}
      {report.overview && (
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
        >
          <div className="flex items-center gap-2 mb-3">
            <BookOpen className="w-5 h-5 text-turquoise" />
            <h2 className="text-lg font-semibold text-gray-900">Overview</h2>
          </div>
          <div className="bg-gradient-to-br from-turquoise/5 to-transparent rounded-xl border border-turquoise/20 p-6">
            <p className="text-gray-700 leading-relaxed">{report.overview}</p>
            {report.methodology && (
              <p className="text-sm text-gray-500 mt-4 pt-3 border-t border-turquoise/10">
                <strong className="text-gray-600">Methodology:</strong> {report.methodology}
              </p>
            )}
          </div>
        </motion.section>
      )}

      {/* Key Figures */}
      {report.key_stats && report.key_stats.length > 0 && (
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-turquoise" />
            <h2 className="text-lg font-semibold text-gray-900">Key Figures</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {report.key_stats.map((stat, i) => (
              <StatCard key={i} stat={stat} index={i} />
            ))}
          </div>
        </motion.section>
      )}

      {/* Key Highlights */}
      {report.highlights && report.highlights.length > 0 && (
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <div className="flex items-center gap-2 mb-4">
            <Flame className="w-5 h-5 text-turquoise" />
            <h2 className="text-lg font-semibold text-gray-900">Key Highlights</h2>
            <span className="text-xs text-gray-400 ml-auto">{report.highlights.length} findings</span>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
            {visibleHighlights.map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                className="flex gap-4 p-4 hover:bg-gray-50/50 transition-colors"
              >
                <span className="flex-shrink-0 w-7 h-7 rounded-full bg-turquoise/10 text-turquoise text-xs font-bold flex items-center justify-center mt-0.5">
                  {i + 1}
                </span>
                <p className="text-gray-700 leading-relaxed text-sm">{item}</p>
              </motion.div>
            ))}
          </div>
          {hasMore && (
            <button
              onClick={() => setShowAllHighlights((prev) => !prev)}
              className="mt-3 inline-flex items-center gap-1.5 text-sm text-turquoise hover:text-turquoise/80 font-medium transition-colors"
            >
              {showAllHighlights ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  Show fewer highlights
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  Show all {report.highlights.length} highlights
                </>
              )}
            </button>
          )}
        </motion.section>
      )}

      {/* Charts */}
      {charts.length > 0 && (
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-5 h-5 text-turquoise" />
            <h2 className="text-lg font-semibold text-gray-900">Data Visualizations</h2>
            <span className="text-xs text-gray-400 ml-auto">{charts.length} charts</span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {charts.map((chart) => (
              <MultiBarChart key={chart.id} chart={chart} />
            ))}
          </div>
        </motion.section>
      )}

      {/* Fallback: legacy single chart_data */}
      {charts.length === 0 && report.chart_data && report.chart_data.length > 0 && (
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-xl border border-gray-200 p-5"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Chart</h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={report.chart_data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#00CED1" radius={[4, 4, 0, 0]} name="Value">
                  {(report.chart_data || []).map((_: ChartPoint, idx: number) => (
                    <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.section>
      )}

      {/* Sample info */}
      {report.methodology && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="flex items-start gap-3 bg-gray-50 rounded-xl p-4 text-sm text-gray-500"
        >
          <Users className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <p>
            Based on a study of <strong className="text-gray-700">1,728 women</strong> in The
            Bahamas. Data collected September–October 2022. Published in the{' '}
            {report.journal || 'International Journal of Bahamian Studies'}.
          </p>
        </motion.div>
      )}

      {/* Empty state */}
      {!report.highlights?.length && !report.key_stats?.length && charts.length === 0 && (
        <p className="text-gray-500">
          No highlights or charts extracted yet. View the full report via the PDF link above.
        </p>
      )}
    </div>
  );
}
