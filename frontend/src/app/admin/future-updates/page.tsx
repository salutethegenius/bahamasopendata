'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  CalendarClock,
  Flame,
  Layers3,
  Plus,
  Radar,
  Save,
  ScrollText,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { useAdminAuth } from '@/contexts/AdminAuthContext';
import { fetchFutureUpdates, updateFutureUpdates } from '@/lib/admin-api';
import type { FutureUpdateCard } from '@/types/admin';

const iconMap = [Flame, ScrollText, Layers3, CalendarClock, Radar];

function createNewCard(): FutureUpdateCard {
  return {
    id: `future-update-${Date.now()}`,
    title: 'New update',
    phase: 'Planned',
    description: 'Describe the next addition you want to track here.',
    items: ['Add the first task for this update'],
  };
}

export default function AdminFutureUpdatesPage() {
  const router = useRouter();
  const { user, isLoading } = useAdminAuth();
  const [cards, setCards] = useState<FutureUpdateCard[]>([]);
  const [loadingCards, setLoadingCards] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isLoading) {
      return;
    }

    if (user?.role !== 'superuser') {
      router.replace('/admin/collections');
    }
  }, [isLoading, router, user?.role]);

  useEffect(() => {
    if (isLoading || user?.role !== 'superuser') {
      return;
    }

    const load = async () => {
      setLoadingCards(true);
      setError(null);
      try {
        const response = await fetchFutureUpdates();
        setCards(response);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Failed to load future updates');
      } finally {
        setLoadingCards(false);
      }
    };

    void load();
  }, [isLoading, user?.role]);

  if (isLoading) {
    return null;
  }

  if (user?.role !== 'superuser') {
    return (
      <div className="rounded-[28px] border border-[#0A2342]/8 bg-white p-6 shadow-[0_18px_55px_rgba(10,35,66,0.05)]">
        <p className="text-xs uppercase tracking-[0.28em] text-[#0A2342]/45">Redirecting</p>
        <h1 className="mt-3 text-2xl font-semibold text-[#0A2342]">This page is for the superuser only</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-[#0A2342]/65">
          Only the superuser can manage future updates. You are being returned to Collections now.
        </p>
        <Link
          href="/admin/collections"
          className="mt-5 inline-flex items-center rounded-2xl bg-[#00CED1] px-4 py-3 text-sm font-medium text-white shadow-[0_12px_30px_rgba(0,206,209,0.22)] hover:bg-[#00b8bb]"
        >
          Go to Collections
        </Link>
      </div>
    );
  }

  const updateCard = (index: number, updates: Partial<FutureUpdateCard>) => {
    setCards((current) =>
      current.map((card, cardIndex) => (cardIndex === index ? { ...card, ...updates } : card)),
    );
  };

  const updateCardItems = (index: number, rawValue: string) => {
    updateCard(index, {
      items: rawValue
        .split('\n')
        .map((item) => item.trim())
        .filter(Boolean),
    });
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const response = await updateFutureUpdates(cards);
      setCards(response);
      setMessage('Future updates saved.');
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Failed to save future updates');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <section className="rounded-[28px] border border-[#0A2342]/8 bg-[linear-gradient(135deg,#ecfbfc_0%,#fffaf3_100%)] p-5 sm:rounded-[30px] sm:p-6">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl bg-[#00CED1]/14 p-3 text-[#0A2342]">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-[#0A2342]/45">Future updates</p>
            <h1 className="mt-3 text-2xl font-semibold text-[#0A2342] sm:text-3xl">
              What the superuser panel is planning next
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-[#0A2342]/68 sm:text-[15px]">
              Edit the roadmap below to track upcoming content types, publishing work, and operational improvements.
            </p>
          </div>
        </div>
      </section>

      {error ? (
        <div className="rounded-[24px] border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
          {error}
        </div>
      ) : null}

      {message ? (
        <div className="rounded-[24px] border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm text-emerald-700">
          {message}
        </div>
      ) : null}

      <section className="flex flex-wrap items-center justify-between gap-3 rounded-[28px] border border-[#0A2342]/8 bg-white p-5 shadow-[0_18px_55px_rgba(10,35,66,0.05)]">
        <p className="text-sm text-[#0A2342]/65">
          Add, edit, or remove roadmap cards here. Only superusers can change this page.
        </p>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => setCards((current) => [...current, createNewCard()])}
            className="inline-flex items-center gap-2 rounded-2xl border border-[#0A2342]/10 px-4 py-3 text-sm font-medium text-[#0A2342] hover:bg-[#f8fcfc]"
          >
            <Plus className="h-4 w-4" />
            Add update
          </button>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-2xl bg-[#00CED1] px-4 py-3 text-sm font-medium text-white shadow-[0_12px_30px_rgba(0,206,209,0.22)] hover:bg-[#00b8bb] disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Save className="h-4 w-4" />
            {saving ? 'Saving…' : 'Save updates'}
          </button>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        {loadingCards ? (
          <div className="rounded-[28px] border border-[#0A2342]/8 bg-white p-5 text-sm text-[#0A2342]/60">
            Loading future updates…
          </div>
        ) : null}

        {cards.map((card, index) => {
          const Icon = iconMap[index % iconMap.length];

          return (
            <article
              key={card.id}
              className="rounded-[28px] border border-[#0A2342]/8 bg-white p-5 shadow-[0_18px_55px_rgba(10,35,66,0.05)]"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex min-w-0 flex-1 items-start gap-3">
                  <div className="rounded-2xl bg-[#00CED1]/12 p-3 text-[#0A2342]">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="min-w-0 flex-1 space-y-3">
                    <input
                      value={card.title}
                      onChange={(event) => updateCard(index, { title: event.target.value })}
                      className="w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm font-semibold text-[#0A2342] outline-none focus:border-[#00CED1]/35"
                    />
                    <input
                      value={card.phase}
                      onChange={(event) => updateCard(index, { phase: event.target.value })}
                      className="w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-xs uppercase tracking-[0.18em] text-[#0A2342]/60 outline-none focus:border-[#00CED1]/35"
                    />
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setCards((current) => current.filter((_, cardIndex) => cardIndex !== index))}
                  className="inline-flex items-center gap-2 rounded-2xl border border-rose-200 px-3 py-2 text-sm text-rose-600 hover:bg-rose-50"
                >
                  <Trash2 className="h-4 w-4" />
                  Remove
                </button>
              </div>

              <textarea
                value={card.description}
                onChange={(event) => updateCard(index, { description: event.target.value })}
                rows={4}
                className="mt-4 w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm leading-6 text-[#0A2342]/70 outline-none focus:border-[#00CED1]/35"
              />

              <label className="mt-4 block">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-[#0A2342]/45">
                  Tasks, one per line
                </span>
                <textarea
                  value={card.items.join('\n')}
                  onChange={(event) => updateCardItems(index, event.target.value)}
                  rows={6}
                  className="w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-sm leading-6 text-[#0A2342]/70 outline-none focus:border-[#00CED1]/35"
                />
              </label>
            </article>
          );
        })}
      </section>
    </div>
  );
}
