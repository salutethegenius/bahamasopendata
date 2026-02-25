'use client';

import { useEffect, useState } from 'react';
import { fetchActivePoll } from '@/lib/api';
import type { Poll } from '@/types';
import { useRouter } from 'next/navigation';
import { Loader2, MessageCircle } from 'lucide-react';

export default function CurrentPollWidget() {
  const [poll, setPoll] = useState<Poll | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const active = await fetchActivePoll();
        setPoll(active);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'Failed to load current poll.',
        );
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-4 flex items-center justify-center">
        <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
      </div>
    );
  }

  if (error || !poll) {
    return null;
  }

  const totalVotes = poll.total_votes || 0;
  const topOption =
    poll.options.length > 0
      ? [...poll.options].sort((a, b) => b.votes - a.votes)[0]
      : null;

  return (
    <button
      type="button"
      onClick={() => router.push('/polls')}
      className="w-full text-left bg-white rounded-xl border border-gray-200 p-4 hover:border-turquoise hover:shadow-sm transition-all"
    >
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-full bg-turquoise/10 flex items-center justify-center flex-shrink-0">
          <MessageCircle className="w-4 h-4 text-turquoise" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs uppercase tracking-wide text-turquoise font-semibold mb-1">
            Current poll
          </p>
          <p className="text-sm font-medium text-gray-900 line-clamp-2">
            {poll.question}
          </p>
          {topOption && (
            <p className="mt-1 text-xs text-gray-500 line-clamp-1">
              Leading option: <span className="font-medium">{topOption.option_text}</span>
            </p>
          )}
          <p className="mt-2 text-[11px] text-gray-400">
            {totalVotes} response{totalVotes === 1 ? '' : 's'} · Tap to vote or see
            detailed results
          </p>
        </div>
      </div>
    </button>
  );
}

