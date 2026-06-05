#!/usr/bin/env python3
"""Print headline totals from a normalized budget artifact for reconciliation.

Usage (from backend/):
    python scripts/verify_normalized_budget.py \
        "../data/processed/FY2026-27_Draft_Estimates_of_Revenue_and_Expenditure_normalized.json"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: verify_normalized_budget.py <path-to-normalized.json>", file=sys.stderr)
        return 1

    path = Path(sys.argv[1])
    data = json.loads(path.read_text())
    items = data.get("extracted_items") or []

    def find(label: str) -> float | None:
        for item in items:
            if str(item.get("label", "")).strip().lower() == label.lower():
                amount = item.get("amount")
                return float(amount) if amount is not None else None
        return None

    total_revenue = find("Total Revenue")
    recurrent = find("Recurrent Expenditure")
    capital = find("Capital Expenditure")
    debt = find("National Debt")
    debt_gdp = find("Debt to GDP Ratio")

    print(f"Fiscal year: {data.get('fiscal_year')}")
    print(f"Source: {data.get('source_document')}")
    print(f"Total revenue: {total_revenue:,.0f}" if total_revenue else "Total revenue: —")
    if recurrent is not None and capital is not None:
        print(f"Total expenditure: {recurrent + capital:,.0f} (recurrent {recurrent:,.0f} + capital {capital:,.0f})")
    print(f"National debt: {debt:,.0f}" if debt else "National debt: —")
    print(f"Debt/GDP: {debt_gdp}%" if debt_gdp else "Debt/GDP: —")
    print(f"Line items: {len(items)} | ministries listed: {len(data.get('ministries') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
