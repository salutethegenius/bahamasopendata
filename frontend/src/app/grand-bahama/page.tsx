'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, CheckCircle2, Clock3, ExternalLink } from 'lucide-react';
import { grandBahamaDataset } from '@/data/grandBahama';
import {
  grandBahamaPlatform,
  platformModules,
} from '@/data/grandBahamaPlatform';

export default function GrandBahamaPlatformPage() {
  const liveModule = platformModules.find((m) => m.status === 'live');
  const plannedModules = platformModules.filter((m) => m.status === 'planned');

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <p className="text-xs font-semibold uppercase tracking-wide text-turquoise mb-2">
          Digital government infrastructure
        </p>
        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">
          Grand Bahama{' '}
          <span className="text-turquoise">Digital Government Platform</span>
        </h1>
        <p className="text-gray-600 max-w-3xl text-base sm:text-lg leading-relaxed">
          {grandBahamaPlatform.tagline}
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 rounded-xl border border-turquoise/20 bg-turquoise/5 p-5 sm:p-6"
      >
        <p className="text-sm text-gray-700 leading-relaxed mb-3">
          {grandBahamaPlatform.positioning}
        </p>
        <p className="text-sm text-gray-600 leading-relaxed">
          {grandBahamaPlatform.complementaryNote}
        </p>
      </motion.div>

      {liveModule && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <div className="flex items-center justify-between gap-3 mb-4">
            <h2 className="text-xl font-bold text-gray-900">Live now</h2>
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Module {liveModule.number}
            </span>
          </div>

          <Link
            href={liveModule.href!}
            className="block group rounded-xl border border-turquoise/30 bg-white p-6 sm:p-8 shadow-sm hover:shadow-md hover:border-turquoise/50 transition-all"
          >
            <div className="flex flex-col sm:flex-row sm:items-start gap-5">
              <div className="w-12 h-12 rounded-full bg-turquoise/10 flex items-center justify-center flex-shrink-0">
                <liveModule.icon className="w-6 h-6 text-turquoise" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <h3 className="text-xl font-semibold text-gray-900 group-hover:text-turquoise transition-colors">
                    {liveModule.title}
                  </h3>
                  <span className="text-xs uppercase tracking-wide text-turquoise bg-turquoise/10 px-2 py-0.5 rounded">
                    {liveModule.subtitle}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-4 max-w-3xl">
                  {liveModule.description}
                </p>
                <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-500 mb-4">
                  <span>
                    {grandBahamaDataset.ministry.portfolio.length} portfolio lines
                  </span>
                  <span>{grandBahamaDataset.mps.length} GB constituencies</span>
                  <span>{grandBahamaDataset.districts.length} local-gov districts</span>
                </div>
                <span className="inline-flex items-center gap-1.5 text-sm font-medium text-turquoise">
                  Open Module 01
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </span>
              </div>
            </div>
          </Link>
        </motion.div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10"
      >
        <div className="flex items-center justify-between gap-3 mb-2">
          <h2 className="text-xl font-bold text-gray-900">Platform modules</h2>
          <span className="inline-flex items-center gap-1.5 text-xs text-gray-500">
            <Clock3 className="w-3.5 h-3.5" />
            {plannedModules.length} planned
          </span>
        </div>
        <p className="text-sm text-gray-600 mb-5 max-w-3xl">
          Each module solves the same underlying problem — fragmented government
          information and services — from a different angle. Module 01 proves the
          open-data pattern; later modules add workflow, citizen services, and secure AI.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {platformModules.map((mod, index) => {
            const Icon = mod.icon;
            const isLive = mod.status === 'live';
            const card = (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.04 }}
                className={`h-full rounded-xl border p-5 flex flex-col ${
                  isLive
                    ? 'border-turquoise/40 bg-white hover:shadow-md transition-shadow'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div
                    className={`w-9 h-9 rounded-full flex items-center justify-center ${
                      isLive ? 'bg-turquoise/10' : 'bg-gray-200/70'
                    }`}
                  >
                    <Icon
                      className={`w-4 h-4 ${isLive ? 'text-turquoise' : 'text-gray-500'}`}
                    />
                  </div>
                  <span
                    className={`text-[10px] uppercase tracking-wide px-2 py-0.5 rounded font-semibold ${
                      isLive
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'bg-white text-gray-500 border border-gray-200'
                    }`}
                  >
                    {isLive ? 'Live' : 'Planned'}
                  </span>
                </div>
                <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wide mb-1">
                  Module {mod.number}
                </p>
                <h3 className="font-semibold text-gray-900 mb-1">{mod.title}</h3>
                <p className="text-xs text-turquoise mb-2">{mod.subtitle}</p>
                <p className="text-sm text-gray-600 flex-1 mb-4">{mod.description}</p>
                <div className="pt-3 border-t border-gray-200/80 space-y-1">
                  <p className="text-xs text-gray-500">
                    <span className="font-medium text-gray-700">Buyer:</span> {mod.buyer}
                  </p>
                  <p className="text-xs text-gray-500">
                    <span className="font-medium text-gray-700">Capability:</span>{' '}
                    {mod.capability}
                  </p>
                  {isLive && (
                    <p className="text-xs font-medium text-turquoise pt-1 inline-flex items-center gap-1">
                      Open module <ArrowRight className="w-3 h-3" />
                    </p>
                  )}
                </div>
              </motion.div>
            );

            return isLive && mod.href ? (
              <Link key={mod.id} href={mod.href} className="block h-full">
                {card}
              </Link>
            ) : (
              <div key={mod.id} className="h-full" aria-disabled>
                {card}
              </div>
            );
          })}
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10 bg-white rounded-xl border border-gray-200 p-6"
      >
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Who this serves</h2>
        <p className="text-sm text-gray-600 mb-5">
          One platform, three natural buyers — each owning a different slice of the
          same Grand Bahama digital stack.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {grandBahamaPlatform.buyers.map((buyer) => (
            <div
              key={buyer.ministry}
              className="rounded-lg border border-gray-100 bg-gray-50 p-4"
            >
              <h3 className="text-sm font-semibold text-gray-900 mb-1">
                {buyer.ministry}
              </h3>
              <p className="text-sm text-gray-600">{buyer.focus}</p>
            </div>
          ))}
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-xl border border-gray-200 bg-gray-50 p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h3 className="text-sm font-semibold text-gray-900 mb-1">
            Related open-data reports
          </h3>
          <p className="text-sm text-gray-600">
            GBPA arbitration Hot Topics already on this platform — proof of the same
            public-records → citable report pattern.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          {grandBahamaDataset.meta.related_hot_topics.map((topic) => (
            <Link
              key={topic.slug}
              href={`/hot/${topic.slug}`}
              className="inline-flex items-center gap-1.5 text-sm font-medium text-turquoise hover:underline"
            >
              View report
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          ))}
          <Link
            href="/export"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-gray-700 hover:underline"
          >
            Export Module 01 data
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
