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
} from 'recharts';
import { formatCurrency } from '@/lib/format';
import { Flame, FileText, ExternalLink, ArrowLeft, TrendingUp } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

type KeyStat = { label: string; value: number; unit: string };
type ChartPoint = { name: string; value?: number; amount?: number };

type Report = {
  slug: string;
  title: string;
  source: string;
  year: string;
  pdf_filename: string;
  highlights: string[];
  key_stats: KeyStat[];
  chart_data: ChartPoint[];
};

export default function HotTopicReportPage() {
  const params = useParams();
  const slug = typeof params.slug === 'string' ? params.slug : '';
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
    ? `${API_BASE}/documents/${encodeURIComponent(report.pdf_filename)}`
    : '';

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-2 border-turquoise border-t-current rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="text-red-600">{error ?? 'Report not found.'}</p>
        <Link href="/hot" className="text-turquoise hover:underline mt-2 inline-block">
          Back to Hot Topics
        </Link>
      </div>
    );
  }

  const chartData = (report.chart_data || []).map((d) => ({
    name: d.name,
    value: d.value ?? d.amount ?? 0,
    amount: d.amount ?? d.value ?? 0,
  }));

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link
        href="/hot"
        className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-turquoise mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Hot Topics
      </Link>

      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
          {report.year && <span>{report.year}</span>}
          <span>{report.source}</span>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{report.title}</h1>
        {pdfUrl && (
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-turquoise hover:underline"
          >
            <FileText className="w-4 h-4" />
            View full PDF
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </motion.div>

      {report.highlights && report.highlights.length > 0 && (
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <Flame className="w-5 h-5 text-turquoise" />
            Key highlights
          </h2>
          <ul className="bg-white rounded-xl border border-gray-200 p-5 space-y-2">
            {report.highlights.map((item, i) => (
              <li key={i} className="flex gap-2 text-gray-700">
                <span className="text-turquoise mt-1">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </motion.section>
      )}

      {report.key_stats && report.key_stats.length > 0 && (
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-turquoise" />
            Key figures
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {report.key_stats.map((stat, i) => (
              <div
                key={i}
                className="bg-white rounded-xl border border-gray-200 p-4"
              >
                <p className="text-sm text-gray-500 mb-1">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900 tabular-nums">
                  {stat.unit === '%'
                    ? `${stat.value}%`
                    : stat.unit === 'BSD' || stat.unit?.toLowerCase().includes('dollar')
                    ? formatCurrency(stat.value, true)
                    : `${stat.value}${stat.unit ? ` ${stat.unit}` : ''}`}
                </p>
              </div>
            ))}
          </div>
        </motion.section>
      )}

      {chartData.length > 0 && (
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-8"
        >
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Charts</h2>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => (v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v))} />
                  <Tooltip
                    formatter={(value: number) =>
                      value >= 1_000_000 ? formatCurrency(value, true) : value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value
                    }
                  />
                  <Bar dataKey="value" fill="#00CED1" radius={[4, 4, 0, 0]} name="Value" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </motion.section>
      )}

      {!report.highlights?.length && !report.key_stats?.length && !chartData.length && (
        <p className="text-gray-500">
          No highlights or charts extracted yet. Run the extraction script after ingesting the PDF, or view the full report via the PDF link above.
        </p>
      )}
    </div>
  );
}
