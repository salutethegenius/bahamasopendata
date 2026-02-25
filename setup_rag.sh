#!/bin/bash
# Setup script for RAG connection

echo "🔗 Setting up RAG Connection for Bahamas Open Data"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating backend/.env file..."
    cat > backend/.env << 'EOF'
# Pinecone Configuration
PINECONE_API_KEY=
PINECONE_INDEX_NAME=national-pulse
PINECONE_ENVIRONMENT=us-east-1

# OpenAI Configuration  
OPENAI_API_KEY=

# Database
DATABASE_URL=postgresql://localhost:5432/nationalpulse
EOF
    echo "✅ Created backend/.env file"
else
    echo "✅ backend/.env already exists"
fi

echo ""
echo "📋 Next steps:"
echo "1. Edit backend/.env and add your credentials:"
echo "   - PINECONE_API_KEY: Get from Pinecone dashboard > API keys"
echo "   - PINECONE_INDEX_NAME: Your index name (e.g., 'quickstart' or 'national-pulse')"
echo "   - OPENAI_API_KEY: Your OpenAI API key"
echo ""
echo "2. Test the connection:"
echo "   cd backend && python3 test_rag_connection.py"
echo ""
echo "3. Restart the backend:"
echo "   pm2 restart bahamasopendata-backend --update-env"
echo ""
echo "4. Test RAG via API:"
echo "   curl -X POST http://localhost:8007/api/v1/ask \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"question\": \"What is the Bahamas National Health Strategy?\"}'"
echo ""

