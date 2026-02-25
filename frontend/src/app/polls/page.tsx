'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { fetchPolls } from '@/lib/api';
import type { Poll } from '@/types';
import PollCard from '@/components/PollCard';
import { AlertCircle } from 'lucide-react';

export default function PollsPage() {
  const [polls, setPolls] = useState<Poll[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await fetchPolls();
        setPolls(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load polls.');
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  const handleUpdated = (updated: Poll) => {
    setPolls((current) =>
      current.map((p) => (p.id === updated.id ? updated : p)),
    );
  };

  const activePolls = polls.filter((p) => p.status === 'active');
  const closedPolls = polls.filter((p) => p.status !== 'active');

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Public <span className="text-turquoise">Polls</span>
        </h1>
        <p className="text-gray-600 max-w-2xl">
          Share your perspective on key topics in the national budget, health, income,
          and public finance. Results are aggregated and anonymised.
        </p>
      </motion.div>

      {isLoading && (
        <div className="space-y-4">
          <div className="h-24 bg-gray-100 rounded-xl animate-pulse" />
          <div className="h-24 bg-gray-100 rounded-xl animate-pulse" />
        </div>
      )}

      {!isLoading && error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-8 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
          <div>
            <p className="font-semibold text-red-800">Could not load polls</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {!isLoading && !error && polls.length === 0 && (
        <p className="text-sm text-gray-500">
          No polls are available yet. Check back soon.
        </p>
      )}

      {activePolls.length > 0 && (
        <section className="mb-10 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Active polls
          </h2>
          {activePolls.map((poll) => (
            <PollCard key={poll.id} poll={poll} onUpdated={handleUpdated} />
          ))}
        </section>
      )}

      {closedPolls.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Recent polls
          </h2>
          <div className="space-y-4">
            {closedPolls.map((poll) => (
              <PollCard key={poll.id} poll={poll} onUpdated={handleUpdated} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

