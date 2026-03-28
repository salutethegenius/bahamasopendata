# Data Ingestion Format Spec

This document defines how source data should be formatted when it enters the Bahamas Open Data ingestion pipeline.

It is the contract for:

- admin/API uploads
- manual CLI uploads
- scraper downloads
- future agent-driven ingestion jobs

For the Gemini prompt contract itself, see `AI_NORMALIZATION_PROMPT_SPEC.md`.

## Current Scope

Today, the supported ingestion input is **PDF-first**.

- `POST /api/v1/documents/upload` accepts PDF files only
- `ingestion/process_upload.py` processes PDF files only
- `ingestion/scraper.py` is expected to download source PDFs only
- `ingestion/ai_normalizer.py` optionally converts parsed outputs into validated normalized JSON using Gemini

Direct CSV or JSON uploads are **not** currently supported as ingestion inputs. Structured CSV/JSON files are generated **after** parsing.

## Canonical Storage Layout

All ingestion flows should converge on the same storage model:

- `data/raw/`
  Canonical source PDFs used by the parser, document API, and downstream processing.
- `data/uploads/`
  Temporary/manual drop area for CLI-assisted uploads only. Files should be copied into `data/raw/` through the shared registration path.
- `data/processed/`
  Parser and normalization outputs such as extracted text, extracted tables, chunks, budget item CSVs, and normalized JSON artifacts.
- `data/embeddings/`
  Local embedding metadata files written after vector creation.
- `data/document_metadata.json`
  The ledger of ingested documents and processing status.

## Supported Ingestion Inputs

### 1. API upload

Endpoint:

- `POST /api/v1/documents/upload`

Authentication:

- Requires an authenticated admin user
- Use `POST /api/v1/auth/login` first to obtain an access token

Request format:

- `Content-Type: multipart/form-data`

Fields:

| Field | Type | Required | Format | Notes |
|------|------|----------|--------|-------|
| `file` | file | yes | PDF | Must be a non-empty `.pdf` upload |
| `document_type` | string | no | snake_case | See allowed/recommended values below |
| `fiscal_year` | string | no | `YYYY/YY` preferred | Example: `2025/26` |
| `source_url` | string | no | absolute URL | Use the upstream source page or direct PDF URL |

Example:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer <access-token>" \
  -F "file=@/absolute/path/to/Bahamas BudgetFINAL(2025-2026).pdf;type=application/pdf" \
  -F "document_type=budget_book" \
  -F "fiscal_year=2025/26" \
  -F "source_url=https://www.bahamasbudget.gov.bs/budget-documents/budget-book/"
```

### 2. Manual CLI upload

Entrypoint:

- `python ingestion/process_upload.py "<filename>.pdf" [document_type] [fiscal_year]`

Expected source location:

- the input PDF should exist in `data/uploads/`

Result:

- the file is registered through the same shared helper used by the API
- the canonical stored file ends up in `data/raw/`

### 3. Scraper ingestion

Entrypoint:

- `python ingestion/scraper.py`

Expected behavior for all scrapers:

- download PDFs into canonical raw storage
- populate provenance such as `original_url`
- register metadata in `data/document_metadata.json`
- avoid duplicate entries by file hash

## Filename Rules

Incoming filenames are normalized before canonical storage.

Rules:

- preserve letters, numbers, spaces, `.`, `_`, and `-`
- replace any other character with `_`
- force a `.pdf` suffix if missing
- if a sanitized filename already exists, append `_1`, `_2`, and so on

Examples:

- `Bahamas BudgetFINAL(2025-2026).pdf` -> `Bahamas BudgetFINAL_2025-2026_.pdf`
- `Budget#Book?.pdf` -> `Budget_Book_.pdf`

Important:

- duplicate detection is based on **SHA-256 file hash**, not filename
- identical files should resolve to a single metadata record even if uploaded with different names

## Document Type Values

`document_type` is currently freeform in code, but we should treat the following values as the canonical set:

- `budget_book`
- `budget_communication`
- `revenue_estimates`
- `capital_estimates`
- `mid_year_statement`
- `debt_report`
- `health_strategy`
- `procurement_report`
- `legal_ruling`
- `other`

Guidance:

- use lowercase snake_case only
- prefer one of the values above instead of inventing a near-duplicate
- add a new value only when a document class is meaningfully different

## Fiscal Year Format

Preferred format:

- `YYYY/YY`

Examples:

- `2025/26`
- `2024/25`

Acceptable input rules:

- API and CLI callers may pass a value explicitly
- if omitted, fiscal year may be inferred from filename heuristics
- if a document does not map cleanly to a fiscal year, `null` is acceptable

Avoid:

- `FY25`
- `2025-2026` in stored metadata when `2025/26` is available
- mixing calendar dates and fiscal years in the same field

## Metadata Record Format

Each ingested document should produce one object inside `data/document_metadata.json` under `documents`.

Current record shape:

```json
{
  "filename": "Bahamas BudgetFINAL_2025-2026_.pdf",
  "original_filename": "Bahamas BudgetFINAL(2025-2026).pdf",
  "original_url": "https://www.bahamasbudget.gov.bs/budget-documents/budget-book/",
  "name": "Bahamas BudgetFINAL(2025-2026)",
  "file_hash": "<sha256>",
  "downloaded_at": "2026-03-25T10:30:00.000000",
  "file_size": 4407254,
  "extraction_status": "pending",
  "document_type": "budget_book",
  "fiscal_year": "2025/26",
  "upload_source": "api"
}
```

Field guidance:

| Field | Required | Source | Notes |
|------|----------|--------|-------|
| `filename` | yes | generated | Canonical filename in `data/raw/` |
| `original_filename` | yes for uploaded files | caller | Original client-side or discovered filename |
| `original_url` | recommended for scraped files | scraper/API | Upstream page or direct PDF URL |
| `name` | yes | derived | Human-readable title without `.pdf` |
| `file_hash` | yes | generated | SHA-256 of the PDF bytes |
| `downloaded_at` | yes | generated | ISO 8601 timestamp |
| `file_size` | yes | generated | Bytes |
| `extraction_status` | yes | pipeline | Usually starts as `pending` |
| `document_type` | yes | caller or inferred | Use canonical values above |
| `fiscal_year` | no | caller or inferred | Prefer `YYYY/YY` |
| `upload_source` | yes | caller/pipeline | Recommended values below |

Recommended `upload_source` values:

- `api`
- `manual`
- `scraper`
- `agent`
- `filesystem`

## Processing Status Conventions

These values are not fully centralized yet, but documentation should follow the statuses already visible in the code and metadata.

Recommended current conventions:

- `extraction_status`
  - `pending`
  - `success`
  - `file_not_found`
- `embedding_status`
  - `success`
  - `no_chunks`
  - `pending`

As orchestration endpoints are added, we should tighten these into a single enum set and document it here.

Recommended normalization conventions:

- `normalization_status`
  - `success`
  - `no_processed_input`
  - `validation_error`
  - `error`

## Processed Artifact Formats

For a source file named `Bahamas BudgetFINAL_2025-2026_.pdf`, the parser may generate the following artifacts.

### `<stem>_text.json`

Path:

- `data/processed/Bahamas BudgetFINAL_2025-2026__text.json`

Shape:

```json
{
  "source": "Bahamas BudgetFINAL_2025-2026_.pdf",
  "pages": [
    {
      "page_number": 1,
      "text": "Page text...",
      "char_count": 1234
    }
  ],
  "extracted_at": "2026-03-25T10:40:00.000000"
}
```

### `<stem>_tables.json`

Path:

- `data/processed/Bahamas BudgetFINAL_2025-2026__tables.json`

Shape:

```json
{
  "source": "Bahamas BudgetFINAL_2025-2026_.pdf",
  "tables": [
    {
      "page_number": 71,
      "table_index": 0,
      "columns": ["Ministry", "Amount"],
      "row_count": 10,
      "data": [
        {
          "Ministry": "Education",
          "Amount": "$450,000,000"
        }
      ]
    }
  ],
  "parsed_budgets": [
    {
      "items": [
        {
          "name": "Education",
          "amount": 450000000.0,
          "ministry_code": "MOE"
        }
      ],
      "page_number": 71,
      "table_index": 0
    }
  ],
  "extracted_at": "2026-03-25T10:40:00.000000"
}
```

### `<stem>_budget_items.csv`

Path:

- `data/processed/Bahamas BudgetFINAL_2025-2026__budget_items.csv`

Columns:

- `name`
- `amount`
- `ministry_code`
- `source_page`
- `source_file`

### `<stem>_chunks.json`

Path:

- `data/processed/Bahamas BudgetFINAL_2025-2026__chunks.json`

Shape:

```json
{
  "source": "Bahamas BudgetFINAL_2025-2026_.pdf",
  "chunk_count": 329,
  "chunks": [
    {
      "id": "Bahamas BudgetFINAL_2025-2026__chunk_0",
      "document": "Bahamas BudgetFINAL_2025-2026_.pdf",
      "page_number": 1,
      "content": "Chunk text...",
      "char_count": 998
    }
  ],
  "created_at": "2026-03-25T10:42:00.000000"
}
```

### `<stem>_embeddings.json`

Path:

- `data/embeddings/Bahamas BudgetFINAL_2025-2026__embeddings.json`

Shape:

```json
{
  "source": "Bahamas BudgetFINAL_2025-2026_.pdf",
  "embedding_count": 329,
  "model": "text-embedding-3-small",
  "created_at": "2026-03-25T10:45:00.000000",
  "chunk_ids": [
    "Bahamas BudgetFINAL_2025-2026__chunk_0"
  ]
}
```

### `<stem>_normalized.json`

Path:

- `data/processed/Bahamas BudgetFINAL_2025-2026__normalized.json`

Shape:

```json
{
  "source_document": "Bahamas BudgetFINAL_2025-2026_.pdf",
  "title": "Bahamas Budget 2025-2026",
  "document_type": "budget_book",
  "fiscal_year": "2025/26",
  "executive_summary": "High-level summary...",
  "ministries": ["MOE", "MOH"],
  "extracted_items": [
    {
      "label": "Ministry of Education",
      "amount": 450000000.0,
      "currency": "BSD",
      "category": "ministry_allocation",
      "ministry_code": "MOE",
      "source_page": 71
    }
  ],
  "notable_topics": ["Education funding", "Capital projects"],
  "warnings": [],
  "confidence": 0.86,
  "needs_review": false,
  "normalization_provider": "gemini",
  "normalization_model": "gemini-2.5-flash",
  "normalized_at": "2026-03-25T10:50:00.000000"
}
```

## Scraper And Agent Requirements

Any scraper or agent that adds data should follow these rules:

1. Always register files through the shared ingestion path rather than writing ad hoc metadata.
2. Prefer canonical `document_type` values from this spec.
3. Include `original_url` whenever a document came from the web.
4. Use `upload_source="scraper"` for scraper jobs and `upload_source="agent"` for agent-driven intake.
5. Write PDFs into canonical `data/raw/`, not directly into `data/processed/`.
6. Do not create duplicate metadata records for the same file bytes.
7. Treat parser outputs as derived artifacts, not as source-of-truth inputs.
8. If using Gemini, validate the model output before saving `*_normalized.json`.

## Current Limitations

These are important so nobody builds against assumptions that are not true yet:

- there is no CSV/JSON ingestion endpoint today
- there is no document processing endpoint today
- there is no ingestion run/status endpoint today
- Gemini normalization is currently a script stage, not yet an API endpoint
- `document_type` and status values are documented conventions, not enforced enums yet
- `data/uploads/` still exists during the transition to fully canonical `data/raw/` storage

## Recommended Next Extension

When we add non-PDF structured imports later, this document should grow to include:

- CSV schema for budget line items
- CSV schema for revenue rows
- CSV schema for debt schedules
- JSON schema for source manifests
- validation rules for scraper-produced manifests
