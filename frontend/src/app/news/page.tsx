'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { formatDate } from '@/lib/format';
import { 
  Newspaper, 
  FileText, 
  AlertCircle, 
  TrendingUp, 
  Building2,
  Calendar,
  ExternalLink,
  Filter
} from 'lucide-react';

// Mock news data
const newsItems = [
  {
    id: 1,
    title: "2024/25 Budget Communication Delivered to Parliament",
    source: "Ministry of Finance",
    category: "Budget",
    date: "2024-06-12",
    summary: "Prime Minister and Minister of Finance delivered the annual budget communication outlining $3.2 billion in planned expenditure for the coming fiscal year.",
    url: "https://www.bahamasbudget.gov.bs/",
    icon: FileText,
  },
  {
    id: 2,
    title: "Mid-Year Budget Review Shows Revenue Above Projections",
    source: "Ministry of Finance",
    category: "Revenue",
    date: "2024-12-01",
    summary: "Government revenue collection for the first six months of FY2024/25 exceeded projections by 3.2%, driven primarily by strong VAT and tourism tax receipts.",
    url: "#",
    icon: TrendingUp,
  },
  {
    id: 3,
    title: "Auditor General Report on Public Accounts 2022/23",
    source: "Auditor General",
    category: "Audit",
    date: "2024-10-15",
    summary: "The Auditor General's annual report highlights areas for improvement in public financial management across several ministries.",
    url: "#",
    icon: AlertCircle,
  },
  {
    id: 4,
    title: "Central Bank Quarterly Economic Review Q3 2024",
    source: "Central Bank of The Bahamas",
    category: "Economic",
    date: "2024-11-20",
    summary: "The quarterly review indicates continued economic recovery with tourism arrivals reaching pre-pandemic levels and positive growth in key sectors.",
    url: "https://www.centralbankbahamas.com/",
    icon: TrendingUp,
  },
  {
    id: 5,
    title: "Government Debt Falls Below 83% of GDP",
    source: "Ministry of Finance",
    category: "Debt",
    date: "2024-09-28",
    summary: "National debt-to-GDP ratio continues its downward trend, falling to 82.5% as economic growth outpaces new borrowing.",
    url: "#",
    icon: TrendingUp,
  },
  {
    id: 6,
    title: "New Public Financial Management Act Takes Effect",
    source: "Ministry of Finance",
    category: "Policy",
    date: "2024-07-01",
    summary: "The new legislation introduces stronger fiscal responsibility requirements and improved transparency in government financial reporting.",
    url: "#",
    icon: Building2,
  },
  {
    id: 7,
    title: "Hurricane Preparedness Allocation Increased",
    source: "Cabinet Office",
    category: "Budget",
    date: "2024-08-15",
    summary: "Government increases the National Disaster Fund allocation by $25 million ahead of the 2024 hurricane season.",
    url: "#",
    icon: AlertCircle,
  },
  {
    id: 8,
    title: "VAT Collection Reaches Record Monthly High",
    source: "Department of Inland Revenue",
    category: "Revenue",
    date: "2024-11-05",
    summary: "October 2024 VAT collections reached $105 million, the highest single-month collection since the tax was introduced.",
    url: "#",
    icon: TrendingUp,
  },
];

const categories = ["All", "Budget", "Revenue", "Debt", "Audit", "Economic", "Policy"];

const categoryColors: Record<string, string> = {
  Budget: "bg-turquoise/10 text-turquoise",
  Revenue: "bg-green-100 text-green-700",
  Debt: "bg-yellow-100 text-yellow-700",
  Audit: "bg-red-100 text-red-700",
  Economic: "bg-blue-100 text-blue-700",
  Policy: "bg-purple-100 text-purple-700",
};

export default function NewsPage() {
  const [selectedCategory, setSelectedCategory] = useState("All");

  const filteredNews = selectedCategory === "All" 
    ? newsItems 
    : newsItems.filter(n => n.category === selectedCategory);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          News & <span className="text-turquoise">Updates</span>
        </h1>
        <p className="text-gray-600">
          Official announcements, reports, and fiscal updates from government sources.
        </p>
      </motion.div>

      {/* Note */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6 flex items-start gap-3">
        <Newspaper className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-gray-600">
          This feed aggregates official government announcements related to public finance. 
          No political commentary or opinion is included.
        </p>
      </div>

      {/* Category Filter */}
      <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-2">
        <Filter className="w-4 h-4 text-gray-400 flex-shrink-0" />
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
              selectedCategory === cat
                ? 'bg-turquoise text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* News List */}
      <div className="space-y-4">
        {filteredNews.map((item, i) => {
          const Icon = item.icon;
          return (
            <motion.article
              key={item.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:border-turquoise/50 transition-colors"
            >
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-turquoise/10 flex items-center justify-center flex-shrink-0">
                  <Icon className="w-5 h-5 text-turquoise" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${categoryColors[item.category] || 'bg-gray-100 text-gray-600'}`}>
                      {item.category}
                    </span>
                    <span className="text-xs text-gray-400 flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {formatDate(item.date)}
                    </span>
                  </div>
                  <h2 className="text-lg font-semibold text-gray-900 mb-1">
                    {item.title}
                  </h2>
                  <p className="text-sm text-gray-600 mb-2">
                    {item.summary}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">
                      Source: {item.source}
                    </span>
                    {item.url !== "#" && (
                      <a 
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-sm text-turquoise hover:underline"
                      >
                        View source
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </motion.article>
          );
        })}
      </div>

      {/* Load More */}
      <div className="mt-8 text-center">
        <button className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors">
          Load more updates
        </button>
      </div>

      {/* Sources */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Official Sources</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <a href="https://www.bahamasbudget.gov.bs/" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-gray-600 hover:text-turquoise">
            <ExternalLink className="w-4 h-4" />
            Ministry of Finance Budget Site
          </a>
          <a href="https://www.centralbankbahamas.com/" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-gray-600 hover:text-turquoise">
            <ExternalLink className="w-4 h-4" />
            Central Bank of The Bahamas
          </a>
          <a href="#" className="flex items-center gap-2 text-gray-600 hover:text-turquoise">
            <ExternalLink className="w-4 h-4" />
            Auditor General's Office
          </a>
          <a href="#" className="flex items-center gap-2 text-gray-600 hover:text-turquoise">
            <ExternalLink className="w-4 h-4" />
            Department of Statistics
          </a>
        </div>
      </div>
    </div>
  );
}

