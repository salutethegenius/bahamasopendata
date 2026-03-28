'use client';

type StatusBadgeProps = {
  status: string | null | undefined;
};

const toneByStatus: Record<string, string> = {
  success: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  partial_success: 'bg-amber-100 text-amber-900 border-amber-200',
  pending: 'bg-slate-100 text-slate-700 border-slate-200',
  running: 'bg-sky-100 text-sky-800 border-sky-200',
  skipped: 'bg-stone-100 text-stone-700 border-stone-200',
  error: 'bg-rose-100 text-rose-800 border-rose-200',
  validation_error: 'bg-orange-100 text-orange-900 border-orange-200',
  file_not_found: 'bg-rose-100 text-rose-800 border-rose-200',
  no_processed_input: 'bg-stone-100 text-stone-700 border-stone-200',
  pending_review: 'bg-amber-100 text-amber-900 border-amber-200',
  approved: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  waiting_for_processing: 'bg-slate-100 text-slate-700 border-slate-200',
  changes_requested: 'bg-rose-100 text-rose-800 border-rose-200',
};

const labelByStatus: Record<string, string> = {
  success: 'Ready',
  partial_success: 'Partly ready',
  pending: 'Waiting',
  running: 'Working',
  skipped: 'Skipped',
  error: 'Needs attention',
  validation_error: 'Needs review',
  file_not_found: 'File missing',
  no_processed_input: 'Nothing to read',
  pending_review: 'Ready for review',
  approved: 'Approved',
  waiting_for_processing: 'Waiting',
  changes_requested: 'Needs changes',
  unknown: 'Unknown',
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = (status ?? 'unknown').toLowerCase();
  const tone = toneByStatus[normalized] ?? 'bg-stone-100 text-stone-700 border-stone-200';
  const label = labelByStatus[normalized] ?? normalized.replaceAll('_', ' ');

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ${tone}`}
    >
      {label}
    </span>
  );
}
