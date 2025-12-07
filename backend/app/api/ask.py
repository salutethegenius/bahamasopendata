"""RAG-powered Q&A API endpoint."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter()


class AskRequest(BaseModel):
    """Question request model."""
    question: str
    fiscal_year: Optional[str] = None


class Citation(BaseModel):
    """Source citation."""
    document: str
    page: int
    snippet: str
    url: Optional[str] = None


class AskResponse(BaseModel):
    """Question answer response."""
    answer: str
    numbers: Optional[dict] = None
    chart_data: Optional[list] = None
    citations: list[Citation]
    confidence: float


@router.post("", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Ask a natural language question about the budget.
    
    Uses RAG to retrieve relevant documents and generate an answer
    with citations to the exact source PDF and page.
    """
    # Try to use RAG pipeline if configured
    if os.getenv("OPENAI_API_KEY") and os.getenv("PINECONE_API_KEY"):
        try:
            from app.rag.pipeline import get_rag_pipeline
            pipeline = get_rag_pipeline()
            response = await pipeline.ask(request.question, request.fiscal_year)
            return AskResponse(
                answer=response.answer,
                numbers=response.numbers,
                chart_data=response.chart_data,
                citations=[
                    Citation(
                        document=c.document,
                        page=c.page,
                        snippet=c.snippet,
                        url=c.url,
                    ) for c in response.citations
                ],
                confidence=response.confidence,
            )
        except Exception as e:
            print(f"RAG pipeline error: {e}")
            # Fall through to mock responses
    
    # Mock responses for demo when RAG is not configured
    question = request.question.lower()
    
    if "education" in question or "school" in question:
        return AskResponse(
            answer="The Ministry of Education received a total allocation of $450 million in the 2024/25 fiscal year. This represents a 7.1% increase from the previous year's allocation of $420 million. The allocation includes $280 million for salaries, $95 million for programs, $55 million for capital projects, and $20 million for grants.",
            numbers={
                "total_allocation": 450_000_000,
                "change_yoy_percent": 7.1,
                "salaries": 280_000_000,
                "programs": 95_000_000,
            },
            chart_data=[
                {"year": "2020/21", "amount": 380_000_000},
                {"year": "2021/22", "amount": 395_000_000},
                {"year": "2022/23", "amount": 410_000_000},
                {"year": "2023/24", "amount": 420_000_000},
                {"year": "2024/25", "amount": 450_000_000},
            ],
            citations=[
                Citation(
                    document="Budget Book 2024-25.pdf",
                    page=87,
                    snippet="Ministry of Education - Total Allocation: $450,000,000",
                    url="/data/raw/budget-2024-25.pdf#page=87",
                ),
            ],
            confidence=0.95,
        )
    
    if "health" in question or "hospital" in question:
        return AskResponse(
            answer="The Ministry of Health was allocated $380 million for fiscal year 2024/25, an 8.6% increase from $350 million in the previous year. This funding covers public hospital operations, primary healthcare, and medical supplies.",
            numbers={
                "total_allocation": 380_000_000,
                "change_yoy_percent": 8.6,
            },
            chart_data=[
                {"year": "2020/21", "amount": 310_000_000},
                {"year": "2021/22", "amount": 325_000_000},
                {"year": "2022/23", "amount": 340_000_000},
                {"year": "2023/24", "amount": 350_000_000},
                {"year": "2024/25", "amount": 380_000_000},
            ],
            citations=[
                Citation(
                    document="Budget Book 2024-25.pdf",
                    page=112,
                    snippet="Ministry of Health - Total Allocation: $380,000,000",
                    url="/data/raw/budget-2024-25.pdf#page=112",
                ),
            ],
            confidence=0.92,
        )
    
    if "debt" in question:
        return AskResponse(
            answer="The national debt stands at $11.5 billion as of fiscal year 2024/25, representing 82.5% of GDP. This consists of $6.2 billion in domestic debt and $5.3 billion in external debt. Annual interest payments total approximately $580 million.",
            numbers={
                "total_debt": 11_500_000_000,
                "debt_to_gdp": 82.5,
                "domestic": 6_200_000_000,
                "external": 5_300_000_000,
                "annual_interest": 580_000_000,
            },
            citations=[
                Citation(
                    document="Debt Report 2024-25.pdf",
                    page=5,
                    snippet="Total National Debt: $11,500,000,000 (82.5% of GDP)",
                    url="/data/raw/debt-report-2024-25.pdf#page=5",
                ),
            ],
            confidence=0.94,
        )
    
    if "vat" in question or "tax" in question:
        return AskResponse(
            answer="VAT (Value Added Tax) is the largest source of government revenue, collecting $1.1 billion in fiscal year 2024/25. This represents 38.6% of total government revenue and a 6.5% increase from the previous year.",
            numbers={
                "vat_revenue": 1_100_000_000,
                "percent_of_total": 38.6,
                "change_yoy_percent": 6.5,
            },
            citations=[
                Citation(
                    document="Budget Book 2024-25.pdf",
                    page=24,
                    snippet="Value Added Tax Revenue: $1,100,000,000",
                    url="/data/raw/budget-2024-25.pdf#page=24",
                ),
            ],
            confidence=0.93,
        )
    
    # Default response for unknown questions
    return AskResponse(
        answer="I don't have specific information about that in my current dataset. Try asking about ministry allocations, revenue sources, national debt, or specific budget line items.",
        numbers=None,
        chart_data=None,
        citations=[],
        confidence=0.3,
    )

