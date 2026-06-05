'use client';

import { Calendar } from 'lucide-react';
import { isFiscalYearDisabled, useFiscalYear } from '@/lib/fiscal-year';

type FiscalYearSelectorProps = {
  className?: string;
  label?: string;
};

export default function FiscalYearSelector({
  className = '',
  label = 'Fiscal year',
}: FiscalYearSelectorProps) {
  const { fiscalYear, setFiscalYear, years } = useFiscalYear();

  return (
    <label className={`inline-flex items-center gap-2 ${className}`}>
      <Calendar className="h-4 w-4 text-turquoise" aria-hidden="true" />
      <span className="text-sm font-medium text-gray-600">{label}</span>
      <select
        value={fiscalYear}
        onChange={(event) => setFiscalYear(event.target.value)}
        className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm outline-none transition focus:border-turquoise focus:ring-2 focus:ring-turquoise/20"
        aria-label="Select fiscal year"
      >
        {[...years].reverse().map((year) => {
          const disabled = isFiscalYearDisabled(year);
          return (
            <option key={year} value={year} disabled={disabled}>
              FY {year}
              {disabled ? ' (coming soon)' : ''}
            </option>
          );
        })}
      </select>
    </label>
  );
}
