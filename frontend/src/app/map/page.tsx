'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { formatCurrency } from '@/lib/format';
import { islands } from '@/data/islands';
import { MapPin, Building, School, Heart, Shield, Construction, FileText } from 'lucide-react';

const categoryIcons: Record<string, typeof School> = {
  education: School,
  health: Heart,
  security: Shield,
  infrastructure: Construction,
};

const categoryColors: Record<string, string> = {
  education: '#00CED1',
  health: '#ef4444',
  security: '#3b82f6',
  infrastructure: '#FCD116',
};

export default function MapPage() {
  const [selectedIsland, setSelectedIsland] = useState<string | null>(null);
  const selected = islands.find(i => i.id === selectedIsland);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Spending by <span className="text-turquoise">Island</span>
        </h1>
        <p className="text-gray-600">
          Explore capital projects and allocations across the Bahamas archipelago.
        </p>
      </motion.div>

      {/* Note */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-8">
        <p className="text-sm text-amber-800">
          <strong>Note:</strong> Island-level data is compiled from available capital budget documents. 
          Some allocations are estimated based on ministry-level data distribution.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Island List */}
        <div className="lg:col-span-1 space-y-3">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Select an Island</h2>
          {islands.map((island, i) => (
            <motion.button
              key={island.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => setSelectedIsland(island.id)}
              className={`w-full text-left p-4 rounded-xl border transition-all ${
                selectedIsland === island.id
                  ? 'bg-turquoise/10 border-turquoise'
                  : 'bg-white border-gray-200 hover:border-turquoise/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <MapPin className={`w-5 h-5 ${selectedIsland === island.id ? 'text-turquoise' : 'text-gray-400'}`} />
                  <div>
                    <p className="font-medium text-gray-900">{island.name}</p>
                    <p className="text-sm text-gray-500">{island.capital}</p>
                  </div>
                </div>
                <p className="font-bold text-turquoise tabular-nums">
                  {formatCurrency(island.allocation, true)}
                </p>
              </div>
            </motion.button>
          ))}
        </div>

        {/* Island Detail */}
        <div className="lg:col-span-2">
          {selected ? (
            <motion.div
              key={selected.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-xl border border-gray-200 p-6"
            >
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{selected.name}</h2>
                  <p className="text-gray-500">Capital: {selected.capital}</p>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-turquoise">
                    {formatCurrency(selected.allocation, true)}
                  </p>
                  <p className="text-sm text-gray-500">Total Allocation</p>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-500">Population</p>
                  <p className="text-xl font-bold text-gray-900">
                    {selected.population.toLocaleString()}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-500">Per Capita</p>
                  <p className="text-xl font-bold text-gray-900">
                    {formatCurrency(selected.allocation / selected.population)}
                  </p>
                </div>
              </div>

              {/* Projects */}
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Capital Projects</h3>
              <div className="space-y-3">
                {selected.projects.map((project, i) => {
                  const Icon = categoryIcons[project.category] || Building;
                  const color = categoryColors[project.category] || '#6b7280';
                  return (
                    <div 
                      key={i}
                      className="flex items-center gap-4 p-3 rounded-lg bg-gray-50"
                    >
                      <div 
                        className="w-10 h-10 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: `${color}20` }}
                      >
                        <Icon className="w-5 h-5" style={{ color }} />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{project.name}</p>
                        <p className="text-xs text-gray-500 capitalize">{project.category}</p>
                      </div>
                      <p className="font-bold text-gray-900 tabular-nums">
                        {formatCurrency(project.amount, true)}
                      </p>
                    </div>
                  );
                })}
              </div>

              {/* Source */}
              <div className="mt-6 pt-4 border-t border-gray-200">
                <a href="#" className="flex items-center gap-2 text-sm text-gray-500 hover:text-turquoise">
                  <FileText className="w-4 h-4" />
                  <span>Source: Capital Budget Estimates 2024-25.pdf</span>
                </a>
              </div>
            </motion.div>
          ) : (
            <div className="bg-gray-50 rounded-xl border border-dashed border-gray-300 p-12 text-center">
              <MapPin className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Select an island to view projects and allocations</p>
            </div>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="mt-8 bg-white rounded-xl border border-gray-200 p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Project Categories</h3>
        <div className="flex flex-wrap gap-4">
          {Object.entries(categoryColors).map(([cat, color]) => {
            const Icon = categoryIcons[cat];
            return (
              <div key={cat} className="flex items-center gap-2">
                <div 
                  className="w-6 h-6 rounded flex items-center justify-center"
                  style={{ backgroundColor: `${color}20` }}
                >
                  <Icon className="w-4 h-4" style={{ color }} />
                </div>
                <span className="text-sm text-gray-600 capitalize">{cat}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

