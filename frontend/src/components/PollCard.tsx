'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Poll } from '@/types';
import { voteInPoll } from '@/lib/api';
import { BarChart3, Loader2 } from 'lucide-react';

interface PollCardProps {
  poll: Poll;
  onUpdated?: (poll: Poll) => void;
}

function getClientFingerprint(): string | undefined {
  if (typeof window === 'undefined') return undefined;
  const key = 'bahamas-open-data-poll-fingerprint';
  let existing = window.localStorage.getItem(key);
  if (!existing) {
    existing = crypto.randomUUID();
    window.localStorage.setItem(key, existing);
  }
  return existing;
}

export default function PollCard({ poll, onUpdated }: PollCardProps) {
  const [selectedOptionId, setSelectedOptionId] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [localPoll, setLocalPoll] = useState<Poll>(poll);

  useEffect(() => {
    setLocalPoll(poll);
  }, [poll]);

  const handleVote = async () => {
    if (!selectedOptionId || isSubmitting) return;
    setIsSubmitting(true);
    setError(null);

    try {
      const fingerprint = getClientFingerprint();
      const updated = await voteInPoll(localPoll.id, selectedOptionId, fingerprint);
      setLocalPoll(updated);
      onUpdated?.(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit vote.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const totalVotes = localPoll.total_votes || 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-turquoise font-semibold mb-1">
            Poll
          </p>
          <h2 className="text-lg font-semibold text-gray-900">{localPoll.question}</h2>
          {localPoll.description && (
            <p className="text-sm text-gray-600 mt-1">{localPoll.description}</p>
          )}
        </div>
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <BarChart3 className="w-4 h-4 text-turquoise" />
          <span>{totalVotes} vote{totalVotes === 1 ? '' : 's'}</span>
        </div>
      </div>

      <div className="space-y-2 mb-4">
        {localPoll.options.map((option) => {
          const votes = option.votes || 0;
          const pct = totalVotes > 0 ? (votes / totalVotes) * 100 : 0;
          const isSelected = selectedOptionId === option.id;

          return (
            <button
              key={option.id}
              type="button"
              onClick={() => setSelectedOptionId(option.id)}
              className={`w-full text-left px-3 py-2 rounded-lg border transition-colors ${
                isSelected
                  ? 'border-turquoise bg-turquoise/10 text-gray-900'
                  : 'border-gray-200 hover:border-turquoise/50 bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm">{option.option_text}</span>
                {totalVotes > 0 && (
                  <span className="text-xs text-gray-500 tabular-nums">
                    {pct.toFixed(0)}%
                  </span>
                )}
              </div>
              {totalVotes > 0 && (
                <div className="mt-1 h-1.5 bg-white rounded-full overflow-hidden">
                  <div
                    className="h-full bg-turquoise rounded-full transition-all"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              )}
            </button>
          );
        })}
      </div>

      {error && (
        <p className="text-xs text-red-600 mb-2">
          {error}
        </p>
      )}

      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={handleVote}
          disabled={!selectedOptionId || isSubmitting}
          className="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-turquoise text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-turquoise-dark transition-colors"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
              Submitting...
            </>
          ) : (
            'Submit vote'
          )}
        </button>
        <p className="text-[11px] text-gray-400">
          One vote per device. Results update in real time.
        </p>
      </div>
    </motion.div>
  );
}

