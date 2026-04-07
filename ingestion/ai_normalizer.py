"""
Bahamas Open Data - Gemini normalization pipeline

Uses Gemini to normalize parsed document content into a consistent JSON artifact
that downstream ingestion jobs can validate and consume.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from pydantic import BaseModel, Field, ValidationError
from tqdm import tqdm

DATA_DIR = Path(__file__).parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
METADATA_FILE = DATA_DIR / "document_metadata.json"
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from backend.app.core.config import settings as app_settings
except Exception:  # pragma: no cover - fallback for standalone script use
    app_settings = None


def get_gemini_api_key() -> str:
    """Return the configured Gemini API key from canonical settings or env."""
    if app_settings and getattr(app_settings, "GEMINI_API_KEY", ""):
        return app_settings.GEMINI_API_KEY
    return os.getenv("GEMINI_API_KEY", "")


def get_openai_api_key() -> str:
    """Return the configured OpenAI API key from canonical settings or env."""
    if app_settings and getattr(app_settings, "OPENAI_API_KEY", ""):
        return app_settings.OPENAI_API_KEY
    return os.getenv("OPENAI_API_KEY", "")


def get_openai_model() -> str:
    """Return the configured OpenAI chat model from canonical settings or env."""
    if app_settings and getattr(app_settings, "CHAT_MODEL", ""):
        return app_settings.CHAT_MODEL
    return os.getenv("CHAT_MODEL", "gpt-4o-mini")


def get_gemini_model() -> str:
    """Return the configured Gemini model from canonical settings or env."""
    if app_settings and getattr(app_settings, "GEMINI_MODEL", ""):
        return app_settings.GEMINI_MODEL
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_gemini_api_base() -> str:
    """Return the Gemini base URL from env or the default public API."""
    return os.getenv(
        "GEMINI_API_BASE",
        "https://generativelanguage.googleapis.com/v1beta",
    )


def get_normalizer_provider() -> str:
    """Determine which AI provider to use: gemini (preferred) or openai."""
    if get_gemini_api_key():
        return "gemini"
    if get_openai_api_key():
        return "openai"
    return "none"

CANONICAL_DOCUMENT_TYPES = [
    "budget_book",
    "budget_communication",
    "revenue_estimates",
    "capital_estimates",
    "mid_year_statement",
    "debt_report",
    "health_strategy",
    "procurement_report",
    "legal_ruling",
    "other",
]


class NormalizedLineItem(BaseModel):
    """A normalized quantitative row extracted from a source document."""

    label: str
    amount: float | None = None
    currency: str = "BSD"
    category: str | None = None
    ministry_code: str | None = None
    source_page: int | None = None


class NormalizedDocument(BaseModel):
    """Validated output schema for Gemini normalization."""

    source_document: str
    title: str | None = None
    document_type: str = "other"
    fiscal_year: str | None = None
    executive_summary: str = ""
    ministries: list[str] = Field(default_factory=list)
    extracted_items: list[NormalizedLineItem] = Field(default_factory=list)
    notable_topics: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    needs_review: bool = True


def load_metadata() -> dict:
    """Load document metadata from disk."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE) as file_obj:
            return json.load(file_obj)
    return {"documents": []}


def save_metadata(metadata: dict) -> None:
    """Persist document metadata to disk."""
    with open(METADATA_FILE, "w") as file_obj:
        json.dump(metadata, file_obj, indent=2, default=str)


def load_processed_inputs(doc_meta: dict) -> tuple[dict | None, dict | None]:
    """Load parser outputs needed for AI normalization."""
    filename = doc_meta["filename"]
    base_name = Path(filename).stem

    text_path = PROCESSED_DIR / f"{base_name}_text.json"
    tables_path = PROCESSED_DIR / f"{base_name}_tables.json"

    text_payload = None
    tables_payload = None

    if text_path.exists():
        with open(text_path) as file_obj:
            text_payload = json.load(file_obj)

    if tables_path.exists():
        with open(tables_path) as file_obj:
            tables_payload = json.load(file_obj)

    return text_payload, tables_payload


def build_prompt(doc_meta: dict, text_payload: dict | None, tables_payload: dict | None) -> str:
    """Create a normalization prompt from parsed inputs."""
    page_summaries: list[str] = []
    if text_payload:
        for page in text_payload.get("pages", [])[:12]:
            text = (page.get("text") or "").strip()
            if not text:
                continue
            compact = " ".join(text.split())
            page_summaries.append(
                f"Page {page.get('page_number')}: {compact[:2500]}"
            )

    table_summaries: list[dict] = []
    if tables_payload:
        for table in tables_payload.get("tables", [])[:10]:
            table_summaries.append(
                {
                    "page_number": table.get("page_number"),
                    "columns": table.get("columns", []),
                    "rows": table.get("data", [])[:10],
                }
            )

    schema_description = {
        "source_document": "string",
        "title": "string|null",
        "document_type": CANONICAL_DOCUMENT_TYPES,
        "fiscal_year": "string|null using YYYY/YY where possible",
        "executive_summary": "string",
        "ministries": ["string"],
        "extracted_items": [
            {
                "label": "string",
                "amount": "number|null",
                "currency": "string",
                "category": "string|null",
                "ministry_code": "string|null",
                "source_page": "integer|null",
            }
        ],
        "notable_topics": ["string"],
        "warnings": ["string"],
        "confidence": "number between 0 and 1",
        "needs_review": "boolean",
    }

    return (
        "You are normalizing parsed government-finance documents for Bahamas Open Data.\n"
        "Return JSON only. Do not include markdown fences.\n"
        "Do not invent data that is not supported by the document.\n"
        "If a value is uncertain, use null and add a warning.\n"
        "Use one of the canonical document_type values exactly.\n\n"
        f"Document metadata:\n{json.dumps(doc_meta, indent=2)}\n\n"
        f"Required output schema:\n{json.dumps(schema_description, indent=2)}\n\n"
        f"Table samples:\n{json.dumps(table_summaries, indent=2)}\n\n"
        f"Page text samples:\n{json.dumps(page_summaries, indent=2)}"
    )


def extract_response_text(response_payload: dict) -> str:
    """Extract response text from a Gemini generateContent payload."""
    candidates = response_payload.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini response did not include candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = [part.get("text", "") for part in parts if part.get("text")]
    if not text_parts:
        raise ValueError("Gemini response did not include text content")

    response_text = "\n".join(text_parts).strip()
    if response_text.startswith("```"):
        response_text = response_text.strip("`")
        if response_text.lower().startswith("json"):
            response_text = response_text[4:].strip()
    return response_text


def call_gemini(prompt: str) -> dict:
    """Call Gemini generateContent and return parsed JSON."""
    gemini_api_key = get_gemini_api_key()
    gemini_model = get_gemini_model()
    gemini_api_base = get_gemini_api_base()

    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set")

    endpoint = f"{gemini_api_base}/models/{gemini_model}:generateContent"
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt,
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1,
        },
    }

    response = httpx.post(
        endpoint,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": gemini_api_key,
        },
        json=payload,
        timeout=120.0,
    )
    response.raise_for_status()
    response_text = extract_response_text(response.json())
    return json.loads(response_text)


def call_openai(prompt: str) -> dict:
    """Call OpenAI chat completions and return parsed JSON."""
    api_key = get_openai_api_key()
    model = get_openai_model()

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You normalize government-finance documents into structured JSON. Return JSON only, no markdown fences.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        },
        timeout=120.0,
    )
    response.raise_for_status()
    data = response.json()
    text = data["choices"][0]["message"]["content"].strip()
    return json.loads(text)


def call_ai(prompt: str) -> tuple[dict, str, str]:
    """Call the best available AI provider. Returns (parsed_json, provider, model)."""
    provider = get_normalizer_provider()
    if provider == "gemini":
        return call_gemini(prompt), "gemini", get_gemini_model()
    if provider == "openai":
        return call_openai(prompt), "openai", get_openai_model()
    raise ValueError("No AI API key is set (need GEMINI_API_KEY or OPENAI_API_KEY)")


def normalize_document(doc_meta: dict) -> dict:
    """Normalize one extracted document with the best available AI provider."""
    text_payload, tables_payload = load_processed_inputs(doc_meta)
    if not text_payload and not tables_payload:
        return {
            "status": "no_processed_input",
            "normalized_count": 0,
        }

    prompt = build_prompt(doc_meta, text_payload, tables_payload)
    raw_response, provider, model = call_ai(prompt)
    normalized = NormalizedDocument.model_validate(raw_response)

    base_name = Path(doc_meta["filename"]).stem
    output_path = PROCESSED_DIR / f"{base_name}_normalized.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                **normalized.model_dump(),
                "normalization_provider": provider,
                "normalization_model": model,
                "normalized_at": datetime.now().isoformat(),
            },
            indent=2,
        )
    )

    return {
        "status": "success",
        "normalized_count": len(normalized.extracted_items),
        "output_file": output_path.name,
        "confidence": normalized.confidence,
        "needs_review": normalized.needs_review,
    }


def main() -> None:
    """Normalize all extracted documents with the best available AI provider."""
    print("🇧🇸 Bahamas Open Data - AI Normalizer")
    print("=" * 40)

    metadata = load_metadata()
    if not metadata.get("documents"):
        print("No documents found. Run scraper.py or process_upload.py first.")
        return

    provider = get_normalizer_provider()
    if provider == "none":
        print("❌ No AI key set. Need GEMINI_API_KEY or OPENAI_API_KEY.")
        return

    model = get_gemini_model() if provider == "gemini" else get_openai_model()
    print(f"   Provider: {provider} ({model})")

    normalized_documents = 0

    for doc in tqdm(metadata["documents"], desc="Normalizing documents"):
        if doc.get("extraction_status") != "success":
            print(f"⊙ Skipping (not extracted): {doc['filename']}")
            continue

        if doc.get("normalization_status") == "success":
            print(f"⊙ Skipping (already normalized): {doc['filename']}")
            continue

        try:
            result = normalize_document(doc)
        except ValidationError as exc:
            result = {
                "status": "validation_error",
                "normalized_count": 0,
                "error": exc.errors(),
            }
        except Exception as exc:
            result = {
                "status": "error",
                "normalized_count": 0,
                "error": str(exc),
            }

        doc["normalization_status"] = result["status"]
        doc["normalization_result"] = result
        doc["normalization_provider"] = provider
        doc["normalization_model"] = model
        doc["normalized_at"] = datetime.now().isoformat()
        doc["normalized_count"] = result.get("normalized_count", 0)

        if result["status"] == "success":
            normalized_documents += 1

        save_metadata(metadata)

    print("\n" + "=" * 40)
    print("✅ AI normalization complete!")
    print(f"   Normalized documents: {normalized_documents}")
    print(f"   Provider: {provider} ({model})")


if __name__ == "__main__":
    main()
