web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
worker: cd ingestion && python scraper.py && python parser.py && python embeddings.py

