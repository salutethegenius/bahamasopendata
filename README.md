# 🇧🇸 Bahamas Open Data

**BahamasOpenData.com — The National Dashboard for Bahamas Public Finance**

A civic instrument panel that makes government budget data clear, visual, and accessible to all Bahamians. Think of it as a national Fitbit — the country's heartbeat in real numbers.

![Bahamas Open Data](https://img.shields.io/badge/Bahamas-Open_Data-00CED1)
![License](https://img.shields.io/badge/license-MIT-blue)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)

---

## 🎯 Vision

Bahamas Open Data transforms scattered government PDFs into a living, queryable dashboard. No more digging through 200-page documents or dead links — see where the money goes in seconds.

**What you get:**
- 📊 **Budget at a glance** — Revenue, expenditure, debt, ministry allocations
- 📈 **Trend charts** — 10-year historical data with year-over-year comparisons
- 🏛️ **Ministry breakdown** — Drill into any ministry's line items with sources
- 💬 **Ask Anything** — Natural language Q&A powered by RAG with PDF citations
- 📍 **Island view** — Capital projects by island across the archipelago
- 📥 **Data exports** — CSV/JSON downloads and developer API
- 🔗 **Source transparency** — Every number links to its official PDF source

---

## 🖥️ Screenshots

| Home Dashboard | Ministry Detail | Ask Anything |
|----------------|-----------------|--------------|
| Budget summary, debt clock, sector breakdown | Line items, historical trends, sources | Natural language Q&A with citations |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, Tailwind CSS, Recharts, Framer Motion |
| **Backend** | FastAPI, PostgreSQL, SQLAlchemy |
| **AI/RAG** | OpenAI (text-embedding-3-small, GPT-4o-mini), Pinecone |
| **Ingestion** | Playwright (scraping), pdfplumber (parsing) |
| **Deploy** | Vercel (frontend), Heroku (backend) |

---

## 📁 Project Structure

```
bahamasopendata/
├── backend/                 # FastAPI API server
│   ├── app/
│   │   ├── api/             # Route handlers (budget, ministries, revenue, debt, ask, export)
│   │   ├── core/            # Config, settings
│   │   ├── db/              # Database models (SQLAlchemy)
│   │   └── rag/             # RAG pipeline (retrieval + generation)
│   ├── main.py              # FastAPI entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # Next.js dashboard
│   └── src/
│       ├── app/             # Pages (7 routes)
│       │   ├── page.tsx     # Home - Bahamas Open Data dashboard
│       │   ├── ministries/  # Ministry allocations grid
│       │   ├── revenue/     # Revenue breakdown
│       │   ├── debt/        # Debt & loans view
│       │   ├── map/         # Island spending map
│       │   ├── news/        # Official updates feed
│       │   └── export/      # Data downloads & API docs
│       ├── components/      # Reusable UI (StatCard, AskBar, Charts)
│       ├── lib/             # API client, formatters
│       └── types/           # TypeScript types
├── ingestion/               # Data pipeline
│   ├── scraper.py           # Downloads PDFs from govt sites
│   ├── parser.py            # Extracts tables from PDFs → CSV
│   ├── ai_normalizer.py     # Uses Gemini to normalize parsed outputs → JSON
│   ├── embeddings.py        # Creates Pinecone vectors for RAG
│   ├── Dockerfile
│   └── requirements.txt
├── data/                    # Data storage
│   ├── raw/                 # Original PDFs
│   ├── processed/           # Extracted JSON/CSV
│   └── embeddings/          # Vector metadata
├── Dockerfile               # API image (repo root: backend + ingestion)
├── docker-compose.yml       # Full stack orchestration
├── Procfile                 # Heroku process definitions
├── heroku.yml               # Heroku Docker config
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or 3.12
- Node.js 18+
- PostgreSQL (or use Docker)
- OpenAI API key (for RAG features)
- Pinecone API key (for vector search)

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/bahamasopendata.git
cd bahamasopendata
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your keys
cat > .env << EOF
DATABASE_URL=postgresql://localhost:5432/bahamasopendata
OPENAI_API_KEY=your-openai-key
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=bahamas-open-data
EOF

# Run the API server
uvicorn main:app --reload
```

API will be available at `http://localhost:8000`

### 3. Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Set API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Run development server
npm run dev
```

Dashboard will be available at `http://localhost:3000`

### 4. Data ingestion (optional)

```bash
cd ingestion

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Download budget PDFs from official sources
python scraper.py

# Parse PDFs and extract data
python parser.py

# Normalize extracted data with Gemini into validated JSON artifacts (optional)
python ai_normalizer.py

# Create embeddings for RAG (requires OpenAI + Pinecone keys)
python embeddings.py

# Or run the managed ingestion pipeline end-to-end
python run_pipeline.py
```

For ingestion formatting and AI normalization rules, see:

- `DATA_INGESTION_FORMAT_SPEC.md`
- `AI_NORMALIZATION_PROMPT_SPEC.md`

---

## 🐳 Docker

Run the full stack with Docker Compose:

```bash
# Start backend + database
docker-compose up -d

# Include ingestion worker
docker-compose --profile ingestion up -d
```

---

## 🔌 API Endpoints

Base URL: `https://api.bahamasopendata.com/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/budget/summary` | Budget summary (revenue, expenditure, debt) |
| `GET` | `/budget/monthly` | Monthly breakdown |
| `GET` | `/budget/historical` | 10-year trend data |
| `GET` | `/ministries` | All ministries with allocations |
| `GET` | `/ministries/{id}` | Ministry detail with line items |
| `GET` | `/revenue` | Revenue breakdown by source |
| `GET` | `/debt` | Debt summary |
| `GET` | `/debt/creditors` | Creditor breakdown |
| `GET` | `/debt/repayment-schedule` | 5-year repayment schedule |
| `POST` | `/documents/upload` | Upload a source PDF into canonical raw storage |
| `POST` | `/ingestion/run` | Run the ingestion pipeline on demand |
| `GET` | `/ingestion/status` | View latest ingestion status and document counts |
| `POST` | `/ask` | Ask a question (RAG with citations) |
| `GET` | `/export/{dataset}` | Export data (JSON/CSV) |

### Example: Ask a question

```bash
curl -X POST "https://api.bahamasopendata.com/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "How much was allocated for education this year?"}'
```

### Example: Upload a source PDF

`POST /api/v1/documents/upload` currently accepts PDF files only and expects `multipart/form-data`.

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer <access-token>" \
  -F "file=@/absolute/path/to/Bahamas BudgetFINAL(2025-2026).pdf;type=application/pdf" \
  -F "document_type=budget_book" \
  -F "fiscal_year=2025/26" \
  -F "source_url=https://www.bahamasbudget.gov.bs/budget-documents/budget-book/"
```

The full data-format contract for uploads, metadata, processed files, and scraper expectations lives in `DATA_INGESTION_FORMAT_SPEC.md`.

The Gemini prompt and validation contract lives in `AI_NORMALIZATION_PROMPT_SPEC.md`.

---

## 📊 Data Sources

| Source | URL | Data |
|--------|-----|------|
| Ministry of Finance | [bahamasbudget.gov.bs](https://www.bahamasbudget.gov.bs/) | Budget books, communications |
| Central Bank | [centralbankbahamas.com](https://www.centralbankbahamas.com/) | GDP, debt, macro data |

---

## ☁️ Deployment

### Backend → Heroku

```bash
# Login and create app
heroku login
heroku create bahamasopendata-api

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set OPENAI_API_KEY=xxx
heroku config:set PINECONE_API_KEY=xxx
heroku config:set PINECONE_INDEX_NAME=bahamas-open-data

# Deploy
git push heroku main
```

### Backend → Railway (monorepo)

The API image is built from the **repository root** [`Dockerfile`](Dockerfile) so both `backend/` and `ingestion/` are present (`PYTHONPATH=/srv`). Do **not** set the service root to `backend` only, or the build will miss `ingestion` and Uvicorn will fail with `ModuleNotFoundError: No module named 'ingestion'`.

1. **New Project** → Deploy from GitHub → select this repo.
2. **Settings** → **Build**:
   - **Root Directory:** leave empty (repo root), **not** `backend`.
   - **Dockerfile path:** `Dockerfile` (at repo root).
3. Add **PostgreSQL** to the project; Railway sets `DATABASE_URL` automatically.
4. In **Variables**, set: `OPENAI_API_KEY`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `PINECONE_ENVIRONMENT`, `POLLS_ADMIN_API_KEY`.
5. Deploy; the container runs `uvicorn main:app` from `/srv/backend` on `$PORT` (see root `Dockerfile`).

### Frontend → Railway (or Vercel)

The frontend **must** know the backend URL. Set this **before** (or with) the first deploy; then **redeploy** so the value is baked into the build.

1. In Railway (or Vercel), open your **frontend** service.
2. Go to **Variables** and add:
   - **`NEXT_PUBLIC_API_URL`** = `https://<your-backend-public-url>/api/v1`
3. Use your **backend’s real URL** (e.g. Railway backend URL like `https://something.up.railway.app`). Do **not** use a custom domain here until its DNS and SSL point to your backend, or you’ll get “Failed to fetch” / TLS errors.
4. **Redeploy** the frontend (new build required for `NEXT_PUBLIC_*` to take effect).

---

## 🎨 Design System

| Element | Value |
|---------|-------|
| Background | White (`#ffffff`) |
| Primary | Turquoise (`#00CED1`) |
| Accent | Yellow (`#FCD116`) |
| Text | Black (`#0a0a0a`) |
| Typography | Geist Sans |

Colors are inspired by the Bahamas flag 🇧🇸

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

© 2025 Registered. All rights reserved.

Development by **Kemis Group of Companies Inc.**

---

## 📝 Attribution

When using this data, please attribute:

> Data from **Bahamas Open Data** (bahamasopendata.com), sourced from official Bahamas Ministry of Finance and Central Bank publications.

---

## 🙏 Acknowledgments

- Ministry of Finance, Bahamas
- Central Bank of The Bahamas
- Kemis Group of Companies Inc.

---

**Built for the people of The Bahamas** 🇧🇸

*Making the fog disappear, one chart at a time.*

---

**© 2025 Registered | Development by Kemis Group of Companies Inc.**
