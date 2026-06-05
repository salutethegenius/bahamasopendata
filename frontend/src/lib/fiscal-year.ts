'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

export const FY_QUERY_PARAM = 'fy';
export const DEFAULT_FISCAL_YEARS = ['2025/26', '2026/27'];
// Years shown in the selector but not yet selectable (data not trusted/verified).
export const DISABLED_FISCAL_YEARS = ['2026/27'];
export const CURRENT_FISCAL_YEAR = '2025/26';

export function isFiscalYearDisabled(year: string): boolean {
  return DISABLED_FISCAL_YEARS.includes(year);
}

function fyOrder(year: string): number {
  const start = Number.parseInt(year.split('/')[0] ?? '0', 10);
  return Number.isNaN(start) ? 0 : start;
}

function mergeFiscalYears(apiYears: string[]): string[] {
  const merged = new Set<string>([...DEFAULT_FISCAL_YEARS, ...apiYears]);
  return [...merged].sort((a, b) => fyOrder(a) - fyOrder(b));
}

function firstEnabledYear(years: string[]): string {
  const enabled = years.filter((year) => !isFiscalYearDisabled(year));
  return enabled.at(-1) ?? CURRENT_FISCAL_YEAR;
}

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
    return { years: DEFAULT_FISCAL_YEARS, current_year: CURRENT_FISCAL_YEAR };
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
        const mergedYears = mergeFiscalYears(payload.years ?? []);
        setYears(mergedYears);
        // Never default to a disabled year, even if the API reports it as current.
        const apiCurrent = payload.current_year;
        if (apiCurrent && !isFiscalYearDisabled(apiCurrent)) {
          setDefaultYear(apiCurrent);
        } else {
          setDefaultYear(firstEnabledYear(mergedYears));
        }
      })
      .catch(() => undefined);
  }, []);

  const fiscalYear = useMemo(() => {
    const fromUrl = searchParams.get(FY_QUERY_PARAM);
    if (fromUrl && years.includes(fromUrl) && !isFiscalYearDisabled(fromUrl)) {
      return fromUrl;
    }
    return isFiscalYearDisabled(defaultYear) ? firstEnabledYear(years) : defaultYear;
  }, [searchParams, years, defaultYear]);

  const setFiscalYear = useCallback(
    (nextYear: string) => {
      if (isFiscalYearDisabled(nextYear)) {
        return;
      }
      const params = new URLSearchParams(searchParams.toString());
      params.set(FY_QUERY_PARAM, nextYear);
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  return { fiscalYear, setFiscalYear, years, currentYear: defaultYear };
}
