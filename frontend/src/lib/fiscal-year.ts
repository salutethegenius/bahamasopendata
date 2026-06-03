'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

export const FY_QUERY_PARAM = 'fy';
export const DEFAULT_FISCAL_YEARS = ['2025/26', '2026/27'];
export const CURRENT_FISCAL_YEAR = DEFAULT_FISCAL_YEARS.at(-1)!;

export function withFiscalYear(path: string, fiscalYear?: string | null): string {
  if (!fiscalYear) {
    return path;
  }
  const url = new URL(path, 'http://local');
  url.searchParams.set(FY_QUERY_PARAM, fiscalYear);
  return `${url.pathname}${url.search}`;
}

export function fiscalYearSearchParam(fiscalYear?: string | null): string {
  if (!fiscalYear) {
    return '';
  }
  return `?fiscal_year=${encodeURIComponent(fiscalYear)}`;
}

export async function fetchBudgetYears(): Promise<{
  years: string[];
  current_year: string;
}> {
  const res = await fetch(`${API_BASE}/budget/years`);
  if (!res.ok) {
    return { years: DEFAULT_FISCAL_YEARS, current_year: DEFAULT_FISCAL_YEARS.at(-1)! };
  }
  return res.json();
}

export function useFiscalYear() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [years, setYears] = useState<string[]>(DEFAULT_FISCAL_YEARS);
  const [defaultYear, setDefaultYear] = useState(CURRENT_FISCAL_YEAR);

  useEffect(() => {
    fetchBudgetYears()
      .then((payload) => {
        if (payload.years.length) {
          setYears(payload.years);
        }
        if (payload.current_year) {
          setDefaultYear(payload.current_year);
        }
      })
      .catch(() => undefined);
  }, []);

  const fiscalYear = useMemo(() => {
    const fromUrl = searchParams.get(FY_QUERY_PARAM);
    if (fromUrl && years.includes(fromUrl)) {
      return fromUrl;
    }
    return defaultYear;
  }, [searchParams, years, defaultYear]);

  const setFiscalYear = useCallback(
    (nextYear: string) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set(FY_QUERY_PARAM, nextYear);
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  return { fiscalYear, setFiscalYear, years, currentYear: defaultYear };
}
