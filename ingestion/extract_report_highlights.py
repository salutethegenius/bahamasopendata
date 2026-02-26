"""
Extract structured highlights, key stats, and chart data from a parsed report PDF.
Run after parser.py has produced <base>_text.json. Requires OPENAI_API_KEY.

Usage:
  python extract_report_highlights.py <base_name> [--slug SLUG] [--title TITLE] [--source SOURCE] [--year YEAR]
Example:
  python extract_report_highlights.py "FieldingandBallanceSweethearting2023FINAL" --slug sweethearting-2023 --title "Sweethearting in Public Procurement" --source "Fielding & Balance" --year 2023
"""
import argparse
import json
import os
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MAX_CONTEXT_CHARS = 120_000  # ~30k tokens; leave room for prompt


def load_text_json(base_name: str) -> str:
    """Load parsed text and concatenate for context."""
    text_file = PROCESSED_DIR / f"{base_name}_text.json"
    if not text_file.exists():
        raise FileNotFoundError(f"Parsed text not found: {text_file}. Run parser.py first.")
    with open(text_file) as f:
        data = json.load(f)
    parts = []
    total = 0
    for page in data.get("pages", []):
        text = (page.get("text") or "").strip()
        if not text:
            continue
        if total + len(text) > MAX_CONTEXT_CHARS:
            parts.append(text[: MAX_CONTEXT_CHARS - total])
            break
        parts.append(text)
        total += len(text)
    return "\n\n".join(parts)


def extract_with_llm(context: str, openai_client, model: str = "gpt-4o-mini") -> dict:
    """Call OpenAI to extract highlights, key_stats, and chart_data."""
    system_prompt = """You are a data analyst extracting structured summary from a report.
Given the document text, produce a JSON object with:
- "highlights": array of 4-6 short bullet-point strings (key findings or takeaways). Each string should be a single sentence or phrase.
- "key_stats": array of objects with "label" (string), "value" (number), "unit" (string, e.g. "%", "BSD", "million", ""). Extract notable percentages, dollar amounts, and figures.
- "chart_data": array of objects suitable for a bar or pie chart, e.g. {"name": "Category name", "amount": number} or {"name": "...", "value": number}. Include 4-8 data points if the document has comparable categories or time series.

Use only information explicitly stated in the document. If few numbers exist, return shorter arrays. Respond with valid JSON only, no markdown."""

    user_prompt = f"Document text:\n\n{context[:MAX_CONTEXT_CHARS]}"

    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    raw = response.choices[0].message.content.strip()
    # Strip markdown code block if present
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description="Extract report highlights for Hot Topics")
    parser.add_argument("base_name", help="Base filename (no .pdf) of the parsed document, e.g. FieldingandBallanceSweethearting2023FINAL")
    parser.add_argument("--slug", default=None, help="URL slug, e.g. sweethearting-2023")
    parser.add_argument("--title", default=None, help="Report title for the UI")
    parser.add_argument("--source", default=None, help="Report source, e.g. Fielding & Balance")
    parser.add_argument("--year", default=None, help="Year, e.g. 2023")
    parser.add_argument("--pdf-filename", default=None, help="PDF filename as stored in data/raw (for document link)")
    args = parser.parse_args()

    base_name = args.base_name.strip()
    if not base_name:
        parser.error("base_name is required")

    # Default slug from base_name: lowercase, replace spaces/underscores with hyphens
    slug = args.slug or re.sub(r"[_\s]+", "-", base_name).lower().replace(".pdf", "")[:50]
    title = args.title or base_name.replace("_", " ").replace(".pdf", "")
    source = args.source or "Report"
    year = args.year or ""
    pdf_filename = args.pdf_filename or f"{base_name}.pdf"

    try:
        import openai
    except ImportError:
        print("openai package required. pip install openai")
        return 1

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY environment variable is required.")
        return 1

    print(f"Loading text for: {base_name}")
    context = load_text_json(base_name)
    print(f"  Context length: {len(context)} chars")

    client = openai.OpenAI(api_key=api_key)
    print("Calling OpenAI to extract highlights and stats...")
    extracted = extract_with_llm(context, client)

    report = {
        "slug": slug,
        "title": title,
        "source": source,
        "year": year,
        "pdf_filename": pdf_filename,
        "highlights": extracted.get("highlights", []),
        "key_stats": extracted.get("key_stats", []),
        "chart_data": extracted.get("chart_data", []),
    }

    out_file = PROCESSED_DIR / f"{base_name}_report.json"
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Wrote: {out_file}")
    return 0


if __name__ == "__main__":
    exit(main())
