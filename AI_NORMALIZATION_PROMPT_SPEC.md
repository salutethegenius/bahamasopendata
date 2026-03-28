# AI Normalization Prompt Spec

This document explains the prompt contract used by the Gemini normalization layer in `ingestion/ai_normalizer.py`.

The goal is to keep the AI step transparent, versionable, and safe to evolve.

## Purpose

The Gemini normalization stage exists to transform parsed PDF outputs into a consistent structured JSON artifact.

It should help with:

- document classification
- fiscal year normalization
- ministry and topic extraction
- row extraction from messy tables
- producing a safe summary artifact for later DB publication

It should **not** replace raw file storage or parser outputs.

## Inputs Sent To Gemini

The normalizer builds a prompt from three inputs:

1. document metadata from `data/document_metadata.json`
2. extracted table samples from `data/processed/<stem>_tables.json`
3. extracted page text samples from `data/processed/<stem>_text.json`

Current sampling strategy:

- up to 12 pages of text
- up to 10 tables
- up to 10 rows per sampled table
- page text compacted before prompt inclusion

This keeps the prompt bounded while still giving Gemini enough context to normalize the document.

## Prompt Goals

The prompt instructs Gemini to:

- return JSON only
- avoid markdown fences
- avoid unsupported or invented facts
- use `null` when uncertain
- add warnings when confidence is limited
- select from the canonical `document_type` values

## Canonical Prompt Template

The current prompt structure in `ingestion/ai_normalizer.py` is:

```text
You are normalizing parsed government-finance documents for Bahamas Open Data.
Return JSON only. Do not include markdown fences.
Do not invent data that is not supported by the document.
If a value is uncertain, use null and add a warning.
Use one of the canonical document_type values exactly.

Document metadata:
{...doc_meta...}

Required output schema:
{...schema_description...}

Table samples:
{...table_summaries...}

Page text samples:
{...page_summaries...}
```

## Required Output Schema

The model is expected to return a JSON object that validates against the `NormalizedDocument` Pydantic model.

```json
{
  "source_document": "string",
  "title": "string|null",
  "document_type": "budget_book|budget_communication|revenue_estimates|capital_estimates|mid_year_statement|debt_report|health_strategy|procurement_report|legal_ruling|other",
  "fiscal_year": "string|null",
  "executive_summary": "string",
  "ministries": ["string"],
  "extracted_items": [
    {
      "label": "string",
      "amount": "number|null",
      "currency": "string",
      "category": "string|null",
      "ministry_code": "string|null",
      "source_page": "integer|null"
    }
  ],
  "notable_topics": ["string"],
  "warnings": ["string"],
  "confidence": "number between 0 and 1",
  "needs_review": "boolean"
}
```

## Validation Rules

Gemini output is **not trusted by default**.

Before it is saved:

1. the raw response text is extracted from the Gemini API response
2. JSON is parsed
3. the payload is validated with Pydantic
4. only validated output is written to `data/processed/<stem>_normalized.json`

If validation fails:

- the document gets `normalization_status = "validation_error"`
- the validation details are saved into metadata

## Prompt Design Rules

When updating the prompt, keep these rules:

1. Keep the instruction that the model must return JSON only.
2. Keep the instruction not to invent unsupported data.
3. Keep the canonical `document_type` list in the prompt.
4. Prefer explicit schema descriptions over vague prose.
5. Prefer sampled parser outputs over raw full-document dumps.
6. If new fields are added, update both:
   - the prompt schema description
   - the Pydantic models in `ingestion/ai_normalizer.py`

## Known Limitations

- The current prompt is optimized for PDF-derived finance documents, not arbitrary tabular imports.
- Ministry names are returned as strings today; DB publication logic still needs to resolve them into canonical entities.
- The model may still miss rows or merge categories when the parser output is low quality.
- The prompt does not yet use a machine-enforced Gemini response schema; validation currently happens after the response returns.

## Recommended Future Improvements

1. Add a stricter regex or enum validation layer for `document_type` and `fiscal_year`.
2. Add field-level provenance for each extracted row.
3. Add a retry path with a narrower prompt when validation fails.
4. Consider using Gemini structured-output schema support directly in addition to Pydantic validation.
5. Split prompts by document family:
   - budget docs
   - debt docs
   - legal/report docs
