# RAG Setup Guide

## Current Status
✅ Health Strategy PDF has been embedded (62 vectors)
✅ Backend RAG pipeline code is ready
⚠️  Need to configure Pinecone API key and index name

## Steps to Connect RAG

### 1. Get Your Pinecone Credentials
From your Pinecone dashboard:
- **API Key**: Found in "API keys" section
- **Index Name**: The name of your index (e.g., "quickstart", "national-pulse", etc.)

### 2. Set Environment Variables for Backend

The backend needs these environment variables. You can set them in PM2:

```bash
# Option 1: Set in PM2 ecosystem config (recommended)
# Edit /home/ubuntu/apps/ecosystem.config.js and add to bahamasopendata-backend env:
#   PINECONE_API_KEY: "your-api-key-here"
#   PINECONE_INDEX_NAME: "your-index-name"  # e.g., "quickstart" or "national-pulse"
#   OPENAI_API_KEY: "your-openai-key"  # If not already set

# Option 2: Create .env file in backend directory
cd /home/ubuntu/apps/bahamasopendata/backend
cat > .env << EOF
PINECONE_API_KEY=your-api-key-here
PINECONE_INDEX_NAME=your-index-name
OPENAI_API_KEY=your-openai-key
EOF

# Then restart PM2
pm2 restart bahamasopendata-backend --update-env
```

### 3. Test the Connection

Run the test script:
```bash
cd /home/ubuntu/apps/bahamasopendata/backend
python test_rag_connection.py
```

This will verify:
- ✅ OpenAI API key is valid
- ✅ Pinecone API key is valid
- ✅ Index exists and is accessible
- ✅ Can query the index

### 4. Verify RAG is Working

1. Restart the backend:
   ```bash
   pm2 restart bahamasopendata-backend --update-env
   ```

2. Test via API:
   ```bash
   curl -X POST http://localhost:8007/api/v1/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the Bahamas National Health Strategy?"}'
   ```

3. Test via frontend:
   - Go to bahamasopendata.com
   - Click "Ask about the budget" button
   - Ask: "What is the Bahamas National Health Strategy?"
   - Should get answer with citations from the PDF

## Troubleshooting

### Issue: "Index not found"
- Check the index name matches exactly (case-sensitive)
- List your indexes: The test script will show available indexes

### Issue: "No vectors in index"
- The health strategy PDF is embedded (62 vectors)
- Make sure you're using the correct index name
- Check that embeddings were uploaded to the right index

### Issue: "API key invalid"
- Verify the API key in Pinecone dashboard
- Make sure it's set in PM2 environment or .env file
- Restart PM2 after setting: `pm2 restart bahamasopendata-backend --update-env`

## Current Configuration

From `backend/app/core/config.py`:
- Default index name: `"national-pulse"`
- Default environment: `"us-east-1"`
- Embedding model: `"text-embedding-3-small"`
- Chat model: `"gpt-4o-mini"`

If your index has a different name, set `PINECONE_INDEX_NAME` to match it.

