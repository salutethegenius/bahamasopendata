# API image: build from repository root (Railway, Heroku, docker compose).
# Includes backend + ingestion so `import ingestion` and REPO_ROOT=/srv resolve correctly.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV PYTHONPATH=/srv

WORKDIR /srv

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend /srv/backend
COPY ingestion /srv/ingestion

RUN mkdir -p /srv/data/raw /srv/data/processed /srv/data/uploads /srv/data/embeddings

RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /srv

USER appuser
WORKDIR /srv/backend

EXPOSE $PORT

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
