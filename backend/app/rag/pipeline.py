"""
Bahamas Open Data - RAG Pipeline
Retrieval-Augmented Generation for budget Q&A.
"""
import os
from typing import Optional
from pydantic import BaseModel
import openai
from pinecone import Pinecone
from app.core.config import settings


class Citation(BaseModel):
    """Source citation for an answer."""
    document: str
    page: int
    snippet: str
    url: Optional[str] = None


class RAGResponse(BaseModel):
    """RAG response with answer and sources."""
    answer: str
    numbers: Optional[dict] = None
    chart_data: Optional[list] = None
    citations: list[Citation]
    confidence: float


class RAGPipeline:
    """RAG pipeline for budget Q&A."""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pinecone_client.Index(settings.PINECONE_INDEX_NAME)
    
    def create_embedding(self, text: str) -> list[float]:
        """Create embedding for a query."""
        response = self.openai_client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding
    
    def retrieve(self, query: str, top_k: int = 5, fiscal_year: Optional[str] = None) -> list[dict]:
        """Retrieve relevant documents from Pinecone."""
        # Create query embedding
        query_embedding = self.create_embedding(query)
        
        # Build filter
        filter_dict = {}
        if fiscal_year:
            filter_dict["fiscal_year"] = fiscal_year
        
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict if filter_dict else None,
        )
        
        # Format results
        documents = []
        for match in results.matches:
            documents.append({
                "id": match.id,
                "score": match.score,
                "content": match.metadata.get("content", ""),
                "document": match.metadata.get("document", ""),
                "page_number": match.metadata.get("page_number", 0),
                "fiscal_year": match.metadata.get("fiscal_year", ""),
                "document_type": match.metadata.get("document_type", ""),
            })
        
        return documents
    
    def generate_answer(
        self, 
        query: str, 
        documents: list[dict],
        fiscal_year: Optional[str] = None,
    ) -> RAGResponse:
        """Generate an answer using retrieved documents."""
        
        if not documents:
            return RAGResponse(
                answer="I don't have specific information about that in my current dataset. Try asking about ministry allocations, revenue sources, national debt, or specific budget line items.",
                citations=[],
                confidence=0.2,
            )
        
        # Build context from retrieved documents
        context_parts = []
        for i, doc in enumerate(documents):
            context_parts.append(
                f"[Source {i+1}: {doc['document']}, Page {doc['page_number']}]\n{doc['content']}"
            )
        context = "\n\n---\n\n".join(context_parts)
        
        # System prompt
        system_prompt = """You are a helpful assistant for Bahamas Open Data, the Bahamas civic finance dashboard. 
Your role is to answer questions about the Bahamas national budget, government spending, revenue, debt, and national strategies (including health strategy).

Guidelines:
- Answer based ONLY on the provided context from official documents
- Always cite your sources using the source numbers provided
- If the answer isn't in the context, say you don't have that information
- Use a clear, factual, neutral tone - no political commentary
- Format currency in Bahamian dollars (BSD)
- When giving numbers, be precise and include the fiscal year or time period
- For strategy documents, focus on goals, targets, and key initiatives

You must respond in JSON format with these fields:
{
  "answer": "Your detailed answer here",
  "numbers": {"key": value} or null,
  "confidence": 0.0 to 1.0,
  "source_indices": [1, 2, 3]
}

Numbers should extract key figures mentioned (e.g., {"total_allocation": 450000000, "change_percent": 7.1}).
Confidence should reflect how well the context answers the question."""

        # User prompt
        user_prompt = f"""Question: {query}
{f'Fiscal Year: {fiscal_year}' if fiscal_year else ''}

Context from official budget documents:

{context}

Please answer the question based on the context above. Respond in JSON format."""

        # Generate answer
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            
            # Parse response
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Build citations from source indices
            source_indices = result.get("source_indices", list(range(1, len(documents) + 1)))
            citations = []
            for idx in source_indices:
                if 1 <= idx <= len(documents):
                    doc = documents[idx - 1]
                    citations.append(Citation(
                        document=doc["document"],
                        page=doc["page_number"],
                        snippet=doc["content"][:200] + "...",
                        url=f"/data/raw/{doc['document']}#page={doc['page_number']}",
                    ))
            
            return RAGResponse(
                answer=result.get("answer", "Unable to generate answer."),
                numbers=result.get("numbers"),
                chart_data=None,  # Could be enhanced to generate chart data
                citations=citations,
                confidence=result.get("confidence", 0.5),
            )
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            return RAGResponse(
                answer=f"An error occurred while generating the answer. Please try again.",
                citations=[],
                confidence=0.0,
            )
    
    async def ask(self, query: str, fiscal_year: Optional[str] = None) -> RAGResponse:
        """Main entry point for asking questions."""
        # Retrieve relevant documents
        documents = self.retrieve(query, top_k=5, fiscal_year=fiscal_year)
        
        # Generate answer
        response = self.generate_answer(query, documents, fiscal_year)
        
        return response


# Singleton instance
_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline instance."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline

