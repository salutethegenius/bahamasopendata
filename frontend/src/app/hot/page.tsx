'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Flame, FileText, ChevronRight, AlertCircle, BarChart3, TrendingUp } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

type ReportSummary = {
  slug: string;
  title: string;
  source: string;
  year: string;
  summary: string;
  stat_count?: number;
  chart_count?: number;
  highlight_count?: number;
};

export default function HotTopicsPage() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchReports() {
      try {
        setLoading(true);
        setError(null);
        const url = `${API_BASE}/hot-topics/reports`;
        const res = await fetch(url);
        if (!res.ok) {
          const body = await res.text();
          const msg = body ? `${res.status}: ${body.slice(0, 100)}` : `HTTP ${res.status}`;
          throw new Error(msg);
        }
        const data = await res.json();
        if (!Array.isArray(data)) {
          throw new Error('Invalid response format');
        }
        setReports(data);
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : 'Failed to load hot topics. Is the API running?';
        setError(message);
      } finally {
        setLoading(false);
      }
    }
    fetchReports();
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Hot <span className="text-turquoise">Topics</span>
        </h1>
        <p className="text-gray-600">
          High-impact reports and studies on public procurement, accountability, and governance.
        </p>
      </motion.div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-2 border-turquoise border-t-current rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-red-800">Could not load reports</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && reports.length === 0 && (
        <p className="text-gray-500">No reports available yet. Check back after ingestion and extraction.</p>
      )}

      {!loading && !error && reports.length > 0 && (
        <div className="space-y-4">
          {reports.map((report, i) => (
            <motion.div
              key={report.slug}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Link
                href={`/hot/${report.slug}`}
                className="block bg-white rounded-xl border border-gray-200 p-5 hover:border-turquoise/50 hover:shadow-sm transition-all"
              >
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-lg bg-turquoise/10 flex items-center justify-center flex-shrink-0">
                    <FileText className="w-5 h-5 text-turquoise" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {report.year && (
                        <span className="text-xs text-gray-400">{report.year}</span>
                      )}
                      <span className="text-xs text-gray-400">{report.source}</span>
                    </div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-1">
                      {report.title}
                    </h2>
                    {report.summary && (
                      <p className="text-sm text-gray-600 line-clamp-2 mb-2">{report.summary}</p>
                    )}
                    <div className="flex flex-wrap gap-3 text-xs text-gray-400">
                      {!!report.highlight_count && (
                        <span className="flex items-center gap-1">
                          <Flame className="w-3 h-3" />
                          {report.highlight_count} highlights
                        </span>
                      )}
                      {!!report.stat_count && (
                        <span className="flex items-center gap-1">
                          <TrendingUp className="w-3 h-3" />
                          {report.stat_count} key figures
                        </span>
                      )}
                      {!!report.chart_count && (
                        <span className="flex items-center gap-1">
                          <BarChart3 className="w-3 h-3" />
                          {report.chart_count} charts
                        </span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0 mt-2" />
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
