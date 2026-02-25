#!/usr/bin/env python3
"""Test RAG connection to Pinecone."""
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from pinecone import Pinecone
import openai

print("🔍 Testing RAG Connection")
print("=" * 50)

# Check environment variables
print(f"\n📋 Configuration:")
print(f"   OpenAI API Key: {'✅ Set' if settings.OPENAI_API_KEY else '❌ Missing'}")
print(f"   Pinecone API Key: {'✅ Set' if settings.PINECONE_API_KEY else '❌ Missing'}")
print(f"   Pinecone Index: {settings.PINECONE_INDEX_NAME}")
print(f"   Pinecone Environment: {settings.PINECONE_ENVIRONMENT}")

if not settings.OPENAI_API_KEY:
    print("\n❌ OPENAI_API_KEY is not set!")
    sys.exit(1)

if not settings.PINECONE_API_KEY:
    print("\n❌ PINECONE_API_KEY is not set!")
    sys.exit(1)

# Test OpenAI
print(f"\n🧪 Testing OpenAI connection...")
try:
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input="test"
    )
    print(f"   ✅ OpenAI connection successful")
except Exception as e:
    print(f"   ❌ OpenAI error: {e}")
    sys.exit(1)

# Test Pinecone
print(f"\n🧪 Testing Pinecone connection...")
try:
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    
    # List indexes
    indexes = pc.list_indexes()
    index_names = [idx.name for idx in indexes]
    print(f"   Available indexes: {index_names}")
    
    if settings.PINECONE_INDEX_NAME not in index_names:
        print(f"   ⚠️  Index '{settings.PINECONE_INDEX_NAME}' not found!")
        print(f"   Available indexes: {index_names}")
        if index_names:
            print(f"   💡 Try setting PINECONE_INDEX_NAME to one of the above")
    else:
        print(f"   ✅ Index '{settings.PINECONE_INDEX_NAME}' found")
        
        # Test query
        index = pc.Index(settings.PINECONE_INDEX_NAME)
        stats = index.describe_index_stats()
        print(f"   📊 Index stats: {stats.total_vector_count} vectors")
        
        # Try a simple query
        test_embedding = response.data[0].embedding
        query_result = index.query(
            vector=test_embedding,
            top_k=1,
            include_metadata=True
        )
        print(f"   ✅ Query successful: {len(query_result.matches)} matches")
        
except Exception as e:
    print(f"   ❌ Pinecone error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("✅ All tests passed! RAG is ready to use.")
print("\n💡 To use RAG, make sure:")
print("   1. PINECONE_API_KEY is set in environment")
print("   2. PINECONE_INDEX_NAME matches your Pinecone index")
print("   3. OPENAI_API_KEY is set in environment")
print("   4. The index contains embedded documents")

