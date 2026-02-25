"""
Test script to verify RAG system can query health strategy content.
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

from app.rag.pipeline import get_rag_pipeline
import asyncio


async def test_health_strategy_queries():
    """Test queries about the health strategy document."""
    print("🇧🇸 Testing Health Strategy RAG Queries")
    print("=" * 50)
    
    # Initialize RAG pipeline
    try:
        pipeline = get_rag_pipeline()
    except Exception as e:
        print(f"❌ Failed to initialize RAG pipeline: {e}")
        print("   Make sure OPENAI_API_KEY and PINECONE_API_KEY are set")
        return
    
    # Test queries
    test_queries = [
        "What is the Bahamas National Health Strategy?",
        "What are the main goals of the health strategy?",
        "What health targets are mentioned in the strategy?",
        "What is the time period covered by the health strategy?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}/{len(test_queries)}: {query}")
        print("-" * 50)
        
        try:
            response = await pipeline.ask(query)
            
            print(f"Answer: {response.answer[:200]}...")
            print(f"Confidence: {response.confidence:.2f}")
            print(f"Citations: {len(response.citations)}")
            
            for j, citation in enumerate(response.citations[:2], 1):
                print(f"  [{j}] {citation.document} (Page {citation.page})")
                print(f"      {citation.snippet[:100]}...")
            
            if response.numbers:
                print(f"Numbers extracted: {response.numbers}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("✅ Testing complete!")


if __name__ == "__main__":
    asyncio.run(test_health_strategy_queries())

