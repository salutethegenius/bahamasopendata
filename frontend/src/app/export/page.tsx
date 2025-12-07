'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Download, 
  FileJson, 
  FileSpreadsheet, 
  Database, 
  Code,
  Copy,
  Check,
  ExternalLink,
  FileText
} from 'lucide-react';

const datasets = [
  {
    id: 'budget_summary',
    name: 'Budget Summary',
    description: 'Overall budget summary with revenue, expenditure, deficit/surplus, and debt levels',
    size: '2 KB',
    records: 1,
  },
  {
    id: 'ministries',
    name: 'Ministry Allocations',
    description: 'All ministry budget allocations with year-over-year change data',
    size: '8 KB',
    records: 15,
  },
  {
    id: 'revenue',
    name: 'Revenue Breakdown',
    description: 'Revenue collection by source (VAT, Customs, Tourism, etc.)',
    size: '5 KB',
    records: 7,
  },
  {
    id: 'debt',
    name: 'National Debt',
    description: 'Debt breakdown by creditor type (domestic, external, multilateral)',
    size: '6 KB',
    records: 8,
  },
  {
    id: 'historical',
    name: 'Historical Data',
    description: '10-year historical budget data for trend analysis',
    size: '15 KB',
    records: 10,
  },
  {
    id: 'line_items',
    name: 'Budget Line Items',
    description: 'Detailed line item data for all ministries (where available)',
    size: '45 KB',
    records: 250,
  },
];

const apiEndpoints = [
  { method: 'GET', path: '/api/v1/budget/summary', description: 'Get budget summary' },
  { method: 'GET', path: '/api/v1/ministries', description: 'List all ministries' },
  { method: 'GET', path: '/api/v1/ministries/{id}', description: 'Get ministry details' },
  { method: 'GET', path: '/api/v1/revenue', description: 'Get revenue breakdown' },
  { method: 'GET', path: '/api/v1/debt', description: 'Get debt summary' },
  { method: 'POST', path: '/api/v1/ask', description: 'Ask a question (RAG)' },
  { method: 'GET', path: '/api/v1/export/{dataset}', description: 'Export dataset' },
];

const API_DOMAIN = 'api.bahamasopendata.com';

export default function ExportPage() {
  const [selectedFormat, setSelectedFormat] = useState<'json' | 'csv'>('json');
  const [copiedEndpoint, setCopiedEndpoint] = useState<string | null>(null);

  const handleDownload = (datasetId: string) => {
    // In production, this would trigger an actual download
    const url = `/api/v1/export/${datasetId}?format=${selectedFormat}`;
    console.log('Downloading:', url);
    // window.location.href = url;
    alert(`Download started: ${datasetId}.${selectedFormat}`);
  };

  const copyEndpoint = (path: string) => {
    navigator.clipboard.writeText(`https://api.bahamasopendata.com${path}`);
    setCopiedEndpoint(path);
    setTimeout(() => setCopiedEndpoint(null), 2000);
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Export <span className="text-turquoise">Data</span>
        </h1>
        <p className="text-gray-600">
          Download datasets in JSON or CSV format, or use our API for programmatic access.
        </p>
      </motion.div>

      {/* Format Toggle */}
      <div className="flex items-center gap-4 mb-6">
        <span className="text-sm font-medium text-gray-700">Format:</span>
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setSelectedFormat('json')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedFormat === 'json'
                ? 'bg-white text-turquoise shadow'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <FileJson className="w-4 h-4" />
            JSON
          </button>
          <button
            onClick={() => setSelectedFormat('csv')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedFormat === 'csv'
                ? 'bg-white text-turquoise shadow'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <FileSpreadsheet className="w-4 h-4" />
            CSV
          </button>
        </div>
      </div>

      {/* Datasets */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-12">
        {datasets.map((dataset, i) => (
          <motion.div
            key={dataset.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="bg-white rounded-xl border border-gray-200 p-5"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-turquoise/10 flex items-center justify-center">
                  <Database className="w-5 h-5 text-turquoise" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{dataset.name}</h3>
                  <p className="text-xs text-gray-400">
                    {dataset.records} records • {dataset.size}
                  </p>
                </div>
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              {dataset.description}
            </p>
            <button
              onClick={() => handleDownload(dataset.id)}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-turquoise text-white rounded-lg text-sm font-medium hover:bg-turquoise-dark transition-colors"
            >
              <Download className="w-4 h-4" />
              Download {selectedFormat.toUpperCase()}
            </button>
          </motion.div>
        ))}
      </div>

      {/* API Section */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-gray-900 rounded-xl p-6 text-white"
      >
        <div className="flex items-center gap-3 mb-4">
          <Code className="w-6 h-6 text-turquoise" />
          <h2 className="text-xl font-bold">Developer API</h2>
        </div>
        <p className="text-gray-400 mb-6">
          Access data programmatically via our REST API. Free for non-commercial use.
        </p>

        {/* Base URL */}
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <p className="text-xs text-gray-400 mb-1">Base URL</p>
          <code className="text-turquoise">https://api.bahamasopendata.com/api/v1</code>
        </div>

        {/* Endpoints */}
        <h3 className="text-sm font-medium text-gray-400 mb-3">Endpoints</h3>
        <div className="space-y-2">
          {apiEndpoints.map((endpoint) => (
            <div
              key={endpoint.path}
              className="flex items-center justify-between bg-gray-800 rounded-lg p-3"
            >
              <div className="flex items-center gap-3">
                <span className={`px-2 py-0.5 rounded text-xs font-mono ${
                  endpoint.method === 'GET' ? 'bg-green-900 text-green-300' : 'bg-blue-900 text-blue-300'
                }`}>
                  {endpoint.method}
                </span>
                <code className="text-sm text-gray-300">{endpoint.path}</code>
                <span className="text-xs text-gray-500">{endpoint.description}</span>
              </div>
              <button
                onClick={() => copyEndpoint(endpoint.path)}
                className="p-2 text-gray-400 hover:text-white transition-colors"
              >
                {copiedEndpoint === endpoint.path ? (
                  <Check className="w-4 h-4 text-green-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
          ))}
        </div>

        {/* Example */}
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Example Request</h3>
          <div className="bg-gray-800 rounded-lg p-4 overflow-x-auto">
            <pre className="text-sm text-gray-300">
{`curl -X GET "https://api.bahamasopendata.com/api/v1/budget/summary" \\
  -H "Accept: application/json"`}
            </pre>
          </div>
        </div>

        {/* Docs Link */}
        <div className="mt-6 flex items-center gap-2">
          <a
            href="#"
            className="flex items-center gap-2 text-turquoise hover:underline text-sm"
          >
            <ExternalLink className="w-4 h-4" />
            View full API documentation
          </a>
        </div>
      </motion.div>

      {/* License & Attribution */}
      <div className="mt-8 bg-gray-50 rounded-xl border border-gray-200 p-6">
        <div className="flex items-start gap-3">
          <FileText className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Data License & Attribution</h3>
            <p className="text-sm text-gray-600 mb-3">
              This data is derived from official Bahamas Government documents and is provided 
              for informational purposes. When using this data, please attribute:
            </p>
            <div className="bg-white border border-gray-200 rounded-lg p-3 text-sm text-gray-700">
              Data from <strong>Bahamas Open Data</strong> (bahamasopendata.com), 
              sourced from Bahamas Ministry of Finance and Central Bank publications.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

