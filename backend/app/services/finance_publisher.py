"""Publish approved document artifacts into live finance tables."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    BudgetItem,
    Creditor,
    Debt,
    Document,
    IslandAllocation,
    IslandProject,
    Ministry,
    MinistryAllocation,
    PublishedEconomicIndicator,
    PublishedNewsItem,
    Revenue,
)
from app.services.document_ingestion import find_document_path, get_processed_artifact_path, load_processed_artifact


FINANCE_DOCUMENT_TYPES = {
    "budget_book",
    "budget_communication",
    "revenue_estimates",
    "capital_estimates",
    "mid_year_statement",
    "debt_report",
}

NEWS_DOCUMENT_TYPES = {"news_update", "news_items"}
ECONOMIC_DOCUMENT_TYPES = {"economic_indicators"}
ISLAND_DOCUMENT_TYPES = {"island_projects"}

ALLOCATION_CATEGORIES = {
    "allocation",
    "ministry_allocation",
    "recurrent_expenditure",
    "capital_expenditure",
}

RECURRENT_CATEGORIES = {
    "recurrent_expenditure",
    "salary",
    "salaries",
    "program",
    "programs",
    "grant",
    "grants",
}

CAPITAL_CATEGORIES = {
    "capital",
    "capital_expenditure",
    "capital_project",
    "capital_projects",
}

DEBT_FIELD_ALIASES = {
    "total_debt": "total_debt",
    "domestic_debt": "domestic_debt",
    "external_debt": "external_debt",
    "gdp": "gdp",
    "debt_to_gdp_ratio": "debt_to_gdp_ratio",
    "annual_interest": "annual_interest",
    "annual_interest_cost": "annual_interest",
}


@dataclass
class PublishResult:
    """Summary of one publish run."""

    status: str
    published_records: dict[str, int]
    warnings: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "published_records": self.published_records,
            "warnings": self.warnings,
        }


def slugify_name(value: str) -> str:
    """Turn a ministry or source label into a stable slug."""
    return "-".join(
        "".join(char.lower() if char.isalnum() else " " for char in value).split()
    )


def infer_ministry_code(name: str) -> str:
    """Generate a lightweight ministry code when one is not supplied."""
    words = [word for word in name.replace("&", " ").split() if word[:1].isalnum()]
    initials = "".join(word[0].upper() for word in words[:4])
    return initials or slugify_name(name).upper()[:12]


def _coerce_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").replace("$", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _normalize_category(value: Any) -> str | None:
    if not value:
        return None
    return str(value).strip().lower().replace(" ", "_")


def _resolve_latest_timestamp(doc_meta: dict[str, Any]) -> datetime:
    for key in ("submitted_at", "reviewed_at", "normalized_at", "downloaded_at"):
        raw_value = doc_meta.get(key)
        if not raw_value:
            continue
        try:
            return datetime.fromisoformat(raw_value)
        except ValueError:
            continue
    return datetime.now()


async def _get_or_create_document_row(
    db: AsyncSession,
    doc_meta: dict[str, Any],
) -> Document:
    result = await db.execute(select(Document).where(Document.filename == doc_meta["filename"]))
    document_row = result.scalars().first()
    file_path = find_document_path(doc_meta["filename"])
    if document_row is None:
        document_row = Document(filename=doc_meta["filename"])
        db.add(document_row)

    document_row.original_url = doc_meta.get("original_url")
    document_row.document_type = doc_meta.get("document_type")
    document_row.fiscal_year = doc_meta.get("fiscal_year")
    document_row.file_hash = doc_meta.get("file_hash")
    document_row.file_path = str(file_path) if file_path else str(get_processed_artifact_path(doc_meta["filename"], "normalized"))
    document_row.page_count = doc_meta.get("extraction_result", {}).get("pages")
    document_row.is_ocr = bool(doc_meta.get("extraction_result", {}).get("ocr"))
    document_row.extraction_status = doc_meta.get("extraction_status") or "pending"
    document_row.downloaded_at = _resolve_latest_timestamp(doc_meta)
    await db.flush()
    return document_row


async def _clear_existing_document_rows(db: AsyncSession, document_id: int) -> None:
    await db.execute(delete(BudgetItem).where(BudgetItem.source_document_id == document_id))
    await db.execute(delete(MinistryAllocation).where(MinistryAllocation.source_document_id == document_id))
    await db.execute(delete(Revenue).where(Revenue.source_document_id == document_id))
    await db.execute(delete(Debt).where(Debt.source_document_id == document_id))
    await db.execute(delete(Creditor).where(Creditor.source_document_id == document_id))
    await db.execute(delete(PublishedNewsItem).where(PublishedNewsItem.source_document_id == document_id))
    await db.execute(delete(PublishedEconomicIndicator).where(PublishedEconomicIndicator.source_document_id == document_id))
    await db.execute(delete(IslandProject).where(IslandProject.source_document_id == document_id))
    await db.execute(delete(IslandAllocation).where(IslandAllocation.source_document_id == document_id))


async def delete_published_document_rows(db: AsyncSession, filename: str) -> dict[str, int]:
    """Delete published finance rows associated with one document filename."""
    result = await db.execute(select(Document).where(Document.filename == filename))
    document_row = result.scalars().first()
    if document_row is None:
        return {"documents": 0, "finance_rows": 0}

    await _clear_existing_document_rows(db, document_row.id)
    await db.execute(delete(Document).where(Document.id == document_row.id))
    return {"documents": 1, "finance_rows": 1}


async def _get_or_create_ministry(
    db: AsyncSession,
    *,
    name: str,
    code: str | None = None,
    sector: str | None = None,
) -> Ministry:
    result = await db.execute(select(Ministry).where(func.lower(Ministry.name) == name.lower()))
    ministry = result.scalars().first()
    if ministry is None and code:
        result = await db.execute(select(Ministry).where(Ministry.code == code))
        ministry = result.scalars().first()

    if ministry is None:
        ministry = Ministry(
            code=code or infer_ministry_code(name),
            name=name,
            sector=sector,
        )
        db.add(ministry)
        await db.flush()
        return ministry

    if sector and not ministry.sector:
        ministry.sector = sector
    if code and not ministry.code:
        ministry.code = code
    await db.flush()
    return ministry


def _resolve_item_ministry_name(item: dict[str, Any], ministry_names: list[str]) -> str | None:
    explicit_name = item.get("ministry_name")
    if explicit_name:
        return str(explicit_name)

    item_code = item.get("ministry_code")
    if item_code:
        for ministry_name in ministry_names:
            if infer_ministry_code(ministry_name) == str(item_code).upper():
                return ministry_name

    label = str(item.get("label") or "")
    lowered_label = label.lower()
    for ministry_name in ministry_names:
        lowered_ministry = ministry_name.lower()
        if lowered_label == lowered_ministry or lowered_ministry in lowered_label:
            return ministry_name
    return None


async def _publish_budget_like_document(
    db: AsyncSession,
    document_row: Document,
    normalized_payload: dict[str, Any],
    doc_meta: dict[str, Any],
) -> dict[str, int]:
    fiscal_year = normalized_payload.get("fiscal_year") or doc_meta.get("fiscal_year")
    ministry_names = list(dict.fromkeys(normalized_payload.get("ministries") or []))
    extracted_items = normalized_payload.get("extracted_items") or []

    ministries: dict[str, Ministry] = {}
    for ministry_name in ministry_names:
        ministries[ministry_name] = await _get_or_create_ministry(db, name=ministry_name)

    allocation_rollups: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "explicit_total_allocation": 0.0,
            "line_item_total": 0.0,
            "recurrent_expenditure": 0.0,
            "capital_expenditure": 0.0,
            "salaries": 0.0,
            "programs": 0.0,
            "grants": 0.0,
        }
    )
    budget_item_count = 0

    for raw_item in extracted_items:
        amount = _coerce_float(raw_item.get("amount"))
        if amount is None:
            continue

        category = _normalize_category(raw_item.get("category")) or "other"
        ministry_name = _resolve_item_ministry_name(raw_item, ministry_names)
        ministry_row = None
        if ministry_name:
            ministry_row = ministries.get(ministry_name)
            if ministry_row is None:
                ministry_row = await _get_or_create_ministry(
                    db,
                    name=ministry_name,
                    code=raw_item.get("ministry_code"),
                    sector=raw_item.get("sector"),
                )
                ministries[ministry_name] = ministry_row

        db.add(
            BudgetItem(
                ministry_id=ministry_row.id if ministry_row else None,
                fiscal_year=fiscal_year,
                item_code=raw_item.get("item_code"),
                item_name=str(raw_item.get("label") or raw_item.get("name") or "Untitled line item"),
                category=category,
                amount=amount,
                previous_year_amount=_coerce_float(raw_item.get("previous_year_amount")),
                source_document_id=document_row.id,
                source_page=raw_item.get("source_page"),
            )
        )
        budget_item_count += 1

        if ministry_name:
            rollup = allocation_rollups[ministry_name]
            is_explicit_allocation = category in ALLOCATION_CATEGORIES or str(raw_item.get("label", "")).lower() == ministry_name.lower()
            if is_explicit_allocation:
                rollup["explicit_total_allocation"] += amount
            else:
                rollup["line_item_total"] += amount
            if category in RECURRENT_CATEGORIES:
                rollup["recurrent_expenditure"] += amount
            if category in CAPITAL_CATEGORIES:
                rollup["capital_expenditure"] += amount
            if category == "salaries":
                rollup["salaries"] += amount
            if category == "programs":
                rollup["programs"] += amount
            if category == "grants":
                rollup["grants"] += amount

    allocation_count = 0
    for ministry_name, rollup in allocation_rollups.items():
        ministry_row = ministries[ministry_name]
        total_allocation = rollup["explicit_total_allocation"] or rollup["line_item_total"]
        if total_allocation <= 0:
            continue
        db.add(
            MinistryAllocation(
                ministry_id=ministry_row.id,
                fiscal_year=fiscal_year,
                total_allocation=total_allocation,
                recurrent_expenditure=rollup["recurrent_expenditure"] or None,
                capital_expenditure=rollup["capital_expenditure"] or None,
                salaries=rollup["salaries"] or None,
                programs=rollup["programs"] or None,
                grants=rollup["grants"] or None,
                source_document_id=document_row.id,
                source_page=None,
            )
        )
        allocation_count += 1

    await db.flush()
    return {
        "ministries": len(ministries),
        "ministry_allocations": allocation_count,
        "budget_items": budget_item_count,
    }


async def _publish_revenue_document(
    db: AsyncSession,
    document_row: Document,
    normalized_payload: dict[str, Any],
    doc_meta: dict[str, Any],
) -> dict[str, int]:
    fiscal_year = normalized_payload.get("fiscal_year") or doc_meta.get("fiscal_year")
    count = 0
    for raw_item in normalized_payload.get("extracted_items") or []:
        amount = _coerce_float(raw_item.get("amount"))
        if amount is None:
            continue
        db.add(
            Revenue(
                fiscal_year=fiscal_year,
                period=raw_item.get("period") or "annual",
                source_name=str(raw_item.get("label") or raw_item.get("name") or "Unknown revenue source"),
                source_category=_normalize_category(raw_item.get("category")),
                amount=amount,
                budget_estimate=_coerce_float(raw_item.get("budget_estimate")),
                source_document_id=document_row.id,
                source_page=raw_item.get("source_page"),
            )
        )
        count += 1
    await db.flush()
    return {"revenue_rows": count}


async def _publish_debt_document(
    db: AsyncSession,
    document_row: Document,
    normalized_payload: dict[str, Any],
    doc_meta: dict[str, Any],
) -> dict[str, int]:
    fiscal_year = normalized_payload.get("fiscal_year") or doc_meta.get("fiscal_year")
    extracted_items = normalized_payload.get("extracted_items") or []
    summary_values: dict[str, float] = {}
    creditor_count = 0

    for raw_item in extracted_items:
        amount = _coerce_float(raw_item.get("amount"))
        category = _normalize_category(raw_item.get("category"))
        label = slugify_name(str(raw_item.get("label") or ""))
        normalized_field = None
        if category in DEBT_FIELD_ALIASES:
            normalized_field = DEBT_FIELD_ALIASES[category]
        elif label in DEBT_FIELD_ALIASES:
            normalized_field = DEBT_FIELD_ALIASES[label]

        if normalized_field and amount is not None:
            summary_values[normalized_field] = amount
            continue

        if amount is None:
            continue

        if category and category.startswith("creditor"):
            creditor_category = category.split(":", 1)[1] if ":" in category else raw_item.get("creditor_category")
            db.add(
                Creditor(
                    name=str(raw_item.get("label") or raw_item.get("name") or "Unknown creditor"),
                    category=creditor_category or "other",
                    fiscal_year=fiscal_year,
                    amount_owed=amount,
                    interest_rate=_coerce_float(raw_item.get("interest_rate")),
                    source_document_id=document_row.id,
                )
            )
            creditor_count += 1

    if "total_debt" in summary_values:
        db.add(
            Debt(
                fiscal_year=fiscal_year,
                as_of_date=_resolve_latest_timestamp(doc_meta).date(),
                total_debt=summary_values["total_debt"],
                domestic_debt=summary_values.get("domestic_debt"),
                external_debt=summary_values.get("external_debt"),
                gdp=summary_values.get("gdp"),
                debt_to_gdp_ratio=summary_values.get("debt_to_gdp_ratio"),
                annual_interest=summary_values.get("annual_interest"),
                source_document_id=document_row.id,
                source_page=None,
            )
        )
        debt_rows = 1
    else:
        debt_rows = 0

    await db.flush()
    return {
        "debt_rows": debt_rows,
        "creditors": creditor_count,
    }


def _coerce_int(value: Any) -> int | None:
    number = _coerce_float(value)
    if number is None:
        return None
    return int(number)


def _coerce_date(value: Any):
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


async def _publish_news_document(
    db: AsyncSession,
    document_row: Document,
    normalized_payload: dict[str, Any],
    doc_meta: dict[str, Any],
) -> dict[str, int]:
    count = 0
    items = normalized_payload.get("news_items") or normalized_payload.get("items") or normalized_payload.get("extracted_items") or []
    if not items and normalized_payload.get("title"):
        items = [normalized_payload]

    for raw_item in items:
        title = str(raw_item.get("title") or raw_item.get("label") or "").strip()
        if not title:
            continue
        db.add(
            PublishedNewsItem(
                title=title,
                source=raw_item.get("source") or normalized_payload.get("source") or doc_meta.get("original_url"),
                url=raw_item.get("url"),
                published_date=_coerce_date(raw_item.get("published_date")),
                summary=raw_item.get("summary") or raw_item.get("executive_summary") or normalized_payload.get("executive_summary"),
                category=raw_item.get("category") or normalized_payload.get("category") or doc_meta.get("document_type"),
                source_document_id=document_row.id,
                source_page=raw_item.get("source_page"),
            )
        )
        count += 1

    await db.flush()
    return {"news_items": count}


async def _publish_economic_document(
    db: AsyncSession,
    document_row: Document,
    normalized_payload: dict[str, Any],
    doc_meta: dict[str, Any],
) -> dict[str, int]:
    count = 0
    items = normalized_payload.get("economic_indicators") or normalized_payload.get("items") or normalized_payload.get("extracted_items") or []

    for raw_item in items:
        indicator_type = raw_item.get("indicator_type") or raw_item.get("category")
        island = raw_item.get("island")
        year = _coerce_int(raw_item.get("year"))
        monthly = _coerce_float(raw_item.get("month_amount") or raw_item.get("monthly_amount") or raw_item.get("amount"))
        annual = _coerce_float(raw_item.get("annual_amount"))
        if not indicator_type or not island or year is None or monthly is None:
            continue
        if annual is None:
            annual = monthly * 12

        await db.execute(
            delete(PublishedEconomicIndicator).where(
                PublishedEconomicIndicator.indicator_type == str(indicator_type),
                PublishedEconomicIndicator.island == str(island),
                PublishedEconomicIndicator.year == year,
            )
        )
        db.add(
            PublishedEconomicIndicator(
                indicator_type=str(indicator_type),
                island=str(island),
                year=year,
                month_amount=monthly,
                annual_amount=annual,
                breakdown=raw_item.get("breakdown"),
                source_document=raw_item.get("source_document") or doc_meta.get("filename"),
                source_url=raw_item.get("source_url") or doc_meta.get("original_url"),
                author=raw_item.get("author"),
                published_date=_coerce_date(raw_item.get("published_date")),
                source_document_id=document_row.id,
            )
        )
        count += 1

    await db.flush()
    return {"economic_indicators": count}


async def _publish_island_projects_document(
    db: AsyncSession,
    document_row: Document,
    normalized_payload: dict[str, Any],
    doc_meta: dict[str, Any],
) -> dict[str, int]:
    islands = normalized_payload.get("islands") or normalized_payload.get("items") or []
    if not islands:
        return {"island_allocations": 0, "island_projects": 0}

    await db.execute(delete(IslandProject))
    await db.execute(delete(IslandAllocation))

    island_count = 0
    project_count = 0

    for raw_island in islands:
        island_id = str(raw_island.get("id") or slugify_name(str(raw_island.get("name") or ""))).strip()
        island_name = str(raw_island.get("name") or "").strip()
        allocation = _coerce_float(raw_island.get("allocation") or raw_island.get("total_allocation")) or 0.0
        if not island_id or not island_name:
            continue

        island_row = IslandAllocation(
            island_id=island_id,
            name=island_name,
            capital=raw_island.get("capital"),
            population=_coerce_int(raw_island.get("population")),
            total_allocation=allocation,
            source_document_id=document_row.id,
        )
        db.add(island_row)
        await db.flush()
        island_count += 1

        for raw_project in raw_island.get("projects") or []:
            project_name = str(raw_project.get("name") or raw_project.get("label") or "").strip()
            amount = _coerce_float(raw_project.get("amount"))
            if not project_name or amount is None:
                continue
            db.add(
                IslandProject(
                    island_id=island_row.id,
                    project_name=project_name,
                    category=raw_project.get("category"),
                    amount=amount,
                    source_document_id=document_row.id,
                    source_page=raw_project.get("source_page"),
                )
            )
            project_count += 1

    await db.flush()
    return {"island_allocations": island_count, "island_projects": project_count}


async def publish_document_to_finance_tables(
    db: AsyncSession,
    *,
    doc_meta: dict[str, Any],
) -> PublishResult:
    """Publish a reviewed document into finance tables when supported."""
    document_row = await _get_or_create_document_row(db, doc_meta)
    await _clear_existing_document_rows(db, document_row.id)

    normalized_payload = load_processed_artifact(doc_meta["filename"], "normalized")
    warnings: list[str] = []
    published_records: dict[str, int] = {}

    if doc_meta.get("document_type") in (FINANCE_DOCUMENT_TYPES | NEWS_DOCUMENT_TYPES | ECONOMIC_DOCUMENT_TYPES | ISLAND_DOCUMENT_TYPES) and not normalized_payload:
        warnings.append("No normalized artifact was found, so only the source document record was published.")
        await db.flush()
        return PublishResult(
            status="partial_success",
            published_records={"documents": 1},
            warnings=warnings,
        )

    if not normalized_payload:
        await db.flush()
        return PublishResult(
            status="success",
            published_records={"documents": 1},
            warnings=warnings,
        )

    document_type = normalized_payload.get("document_type") or doc_meta.get("document_type")
    if document_type in {"budget_book", "budget_communication", "capital_estimates", "mid_year_statement"}:
        published_records = await _publish_budget_like_document(db, document_row, normalized_payload, doc_meta)
    elif document_type == "revenue_estimates":
        published_records = await _publish_revenue_document(db, document_row, normalized_payload, doc_meta)
    elif document_type == "debt_report":
        published_records = await _publish_debt_document(db, document_row, normalized_payload, doc_meta)
    elif document_type in NEWS_DOCUMENT_TYPES:
        published_records = await _publish_news_document(db, document_row, normalized_payload, doc_meta)
    elif document_type in ECONOMIC_DOCUMENT_TYPES:
        published_records = await _publish_economic_document(db, document_row, normalized_payload, doc_meta)
    elif document_type in ISLAND_DOCUMENT_TYPES:
        published_records = await _publish_island_projects_document(db, document_row, normalized_payload, doc_meta)
    else:
        published_records = {}

    published_records = {"documents": 1, **published_records}
    await db.flush()
    return PublishResult(
        status="success",
        published_records=published_records,
        warnings=warnings,
    )
