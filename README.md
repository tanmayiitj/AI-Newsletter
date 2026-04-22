# AI Pulse Newsletter

A production-ready AI-powered newsletter platform that automatically curates the latest AI industry news, tools, and job opportunities into a beautiful, themed weekly digest — with a built-in RAG chatbot for conversational Q&A over archived editions.

## Features

### Newsletter Platform
- **Automated Content Generation** — Scrapes real AI news from 7 RSS feeds (TechCrunch, The Verge, VentureBeat, Ars Technica, WIRED, MIT News, Google AI Blog) and uses OpenAI GPT to generate curated newsletter sections
- **Real Job Listings** — Scrapes AI/ML jobs from RemoteOK and Arbeitnow with intelligent keyword filtering
- **5 Newsletter Sections** — Trending Topics, Top Developments, Corporate Tools, Future Requirements, Jobs Board
- **Section Summaries** — Each section includes an AI-generated preview description shown when collapsed
- **Expandable Sections** — All sections collapse by default with smooth animations; click to expand
- **Theme System** — Light, Dark, and Warm themes with localStorage persistence and no-flash loading
- **Archive with Search** — Full-text search across all newsletters with custom themed year/month filter dropdowns
- **Responsive Design** — Mobile-first layout with Inter + Newsreader fonts, soft shadows, and subtle background patterns
- **Production-Ready** — OpenGraph meta tags, favicon, SSL certificate handling for MongoDB Atlas

### RAG Chatbot
- **Conversational Q&A** — Ask questions about any newsletter content, AI news, tools, or job listings
- **Floating Chat Widget** — Bottom-right chat icon integrated on every page
- **Newsletter Ingestion Pipeline** — MongoDB editions → OpenAI summarization (300–500 words per section) → ChromaDB vector embeddings
- **Temporal Query Intelligence** — Automatically detects time references ("AI news in March", "last month", "this month"); defaults to current month for temporal queries, searches all data for general questions
- **Source Citations** — Every answer includes clickable links back to the source edition
- **Session Management** — In-memory conversation history with sliding window (5 turns) and TTL expiration
- **Retry Resilience** — Exponential backoff on OpenAI rate limits during ingestion

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12+, FastAPI, Uvicorn |
| **Database** | MongoDB Atlas (pymongo async) |
| **LLM** | OpenAI API (GPT-4o-mini default) |
| **RAG** | LangChain, LangChain-OpenAI, ChromaDB |
| **Scraping** | httpx, feedparser (RSS) |
| **Frontend** | Vanilla HTML/CSS/JS, Jinja2 templates |
| **Styling** | CSS custom properties, 3 themes |

## Architecture

The project runs as **two microservices**:

| Service | Port | Description |
|---------|------|-------------|
| **Backend** | 8000 | Newsletter generation, archive, pages, auth |
| **Chatbot** | 8001 | RAG chatbot, ingestion pipeline |

```
User Browser
    │
    ├──► Backend (port 8000)
    │       ├── Pages (HTML via Jinja2)
    │       ├── Newsletter API (generate, search, archive)
    │       ├── Auth (Google OAuth)
    │       └── Share (email-to-self)
    │
    └──► Chatbot (port 8001)
            ├── Chat API (RAG Q&A)
            ├── Ingestion API (admin)
            └── ChromaDB (vector store)
```

## Project Structure

```
backend/
├── config/          # Settings, Jinja2 templates config
├── database/        # MongoDB async connection + lifespan
├── models/          # Pydantic data models (newsletter, jobs, share)
├── routers/         # API endpoints (newsletter, auth, pages, share, health)
└── services/        # LLM client, content generator, news/jobs scrapers,
                     #   email service, rate limiter
chatbot/
├── config/          # Chatbot settings (ports, ChromaDB, session config)
├── ingestion/       # Ingestion pipeline
│   ├── embedder.py  #   ChromaDB vector store management
│   ├── ingest.py    #   MongoDB → summarize → embed pipeline
│   └── summarizer.py#   OpenAI section summarization with retry
├── models/          # Pydantic schemas (ChatRequest, ChatResponse, etc.)
├── retrieval/       # RAG retrieval
│   ├── chain.py     #   LangChain LCEL chain (prompt → LLM → parse)
│   └── vector_store.py  # Retriever abstraction over ChromaDB
├── routers/         # API routes (/chat, /ingest)
└── services/        # Chat orchestration, session mgmt, temporal parsing
frontend/
├── static/
│   ├── css/         # reset, typography, layout, sections, chat, responsive
│   └── js/          # theme, sections, archive, chat, share, smooth-scroll
└── templates/       # Jinja2 HTML templates + partials (incl. chat widget)
specs/               # Feature specifications
tests/               # Test suite
```

## Quick Start

### 1. Clone & setup

```bash
git clone https://github.com/tanmayiitj/AI-Newsletter.git
cd AI-Newsletter
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

| Variable | Description |
|----------|-------------|
| `MONGODB_URI` | MongoDB Atlas connection string |
| `OPENAI_API_KEY` | OpenAI API key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `ADMIN_API_KEY` | Admin key for generation/ingestion — generate one: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `SESSION_SECRET_KEY` | Secret for session signing |
| `CHATBOT_PORT` | Chatbot service port (default: 8001) |
| `CHROMA_PERSIST_DIR` | ChromaDB storage directory (default: `./chroma_data`) |

### 3. Run the services

**Terminal 1 — Backend (port 8000):**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — Chatbot (port 8001):**
```bash
uvicorn chatbot.main:app --host 0.0.0.0 --port 8001
```

### 4. Generate a newsletter

```bash
curl -X POST http://localhost:8000/api/v1/newsletter/generate \
  -H "X-API-Key: YOUR_ADMIN_KEY"
```

### 5. Ingest newsletters into the chatbot

```bash
curl -X POST http://localhost:8001/api/v1/ingest \
  -H "X-API-Key: YOUR_ADMIN_KEY"
```

This summarizes each newsletter section (300–500 words) and stores the embeddings in ChromaDB. Only new editions are processed; already-ingested editions are skipped.

To force a full re-index:
```bash
curl -X POST "http://localhost:8001/api/v1/ingest?full_reindex=true" \
  -H "X-API-Key: YOUR_ADMIN_KEY"
```

### 6. View it

Open [http://localhost:8000](http://localhost:8000) in your browser. The chat widget appears as a floating icon in the bottom-right corner.

## API Endpoints

### Backend (port 8000)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | — | Latest newsletter |
| `GET` | `/archive` | — | Archive with search & filters |
| `GET` | `/edition/{id}` | — | Specific edition |
| `POST` | `/api/v1/newsletter/generate` | API Key | Generate new edition |
| `GET` | `/api/v1/newsletter/latest` | — | Latest published edition (JSON) |
| `GET` | `/api/v1/newsletter/archive` | — | Paginated archive (JSON) |
| `GET` | `/api/v1/newsletter/search` | — | Search newsletters (`?q=&year=&month=`) |
| `GET` | `/api/v1/newsletter/months` | — | Available publication years |
| `GET` | `/api/v1/newsletter/{id}` | — | Specific edition (JSON) |
| `POST` | `/api/v1/share/send-to-self` | Session | Send newsletter to your email |
| `GET` | `/auth/login` | — | Google OAuth login redirect |
| `GET` | `/auth/callback` | — | Google OAuth callback |
| `POST` | `/auth/logout` | Session | Clear session |
| `GET` | `/auth/me` | Session | Current user info |
| `GET` | `/api/v1/health` | — | Health check |

### Chatbot (port 8001)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/chat` | — | Send a chat message, get RAG-powered answer |
| `POST` | `/api/v1/ingest` | API Key | Trigger newsletter ingestion into ChromaDB |
| `GET` | `/health` | — | Health check |

### Chat Request/Response

**Request:**
```json
{
  "message": "What were the major AI news in March?",
  "session_id": "optional-uuid"
}
```

**Response:**
```json
{
  "answer": "Based on Edition #5, the major AI news in March included...",
  "sources": [
    {
      "edition_id": "65f...",
      "edition_number": 5,
      "section_type": "trending_topics",
      "section_title": "Trending Topics",
      "published_at": "2026-03-15T00:00:00"
    }
  ],
  "session_id": "uuid"
}
```

## RAG Pipeline

```
Newsletter Generation                    Chatbot Ingestion
┌─────────────────────┐                 ┌──────────────────────────────┐
│ RSS Feeds (7 sources)│                │ MongoDB (published editions) │
│ Job APIs (2 sources) │                │            │                 │
│         │            │                │            ▼                 │
│         ▼            │                │   OpenAI Summarization       │
│   OpenAI GPT-4o-mini │                │   (300-500 words/section)    │
│         │            │                │            │                 │
│         ▼            │                │            ▼                 │
│   MongoDB (editions) │──── ingest ───►│   ChromaDB (embeddings)      │
└─────────────────────┘                 └──────────────────────────────┘
                                                     │
                                                     ▼
                                        ┌──────────────────────────────┐
                                        │   User Query                 │
                                        │      │                       │
                                        │      ▼                       │
                                        │   Temporal Preprocessing     │
                                        │   (extract month/year)       │
                                        │      │                       │
                                        │      ▼                       │
                                        │   ChromaDB Retrieval (top 5) │
                                        │      │                       │
                                        │      ▼                       │
                                        │   LLM Answer + Sources       │
                                        └──────────────────────────────┘
```

## Security

- **API Key Auth** — Admin endpoints use `X-API-Key` header with constant-time comparison (`secrets.compare_digest`)
- **Session ID Validation** — Chat sessions accept only valid UUIDs
- **CORS Restricted** — Chatbot only accepts requests from the backend origin
- **No Hardcoded Secrets** — All credentials via `.env` file
- **Rate Limiting** — Share endpoint rate-limited per session

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URI` | MongoDB Atlas connection string | Yes |
| `MONGODB_DB_NAME` | Database name (default: `ai_pulse`) | No |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `OPENAI_MODEL` | Model name (default: `gpt-4o-mini`) | No |
| `ADMIN_API_KEY` | Key for generation endpoint | Yes |
| `APP_ENV` | `development` or `production` | No |
| `APP_PORT` | Server port (default: `8000`) | No |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Yes* |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | Yes* |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL (default: `http://localhost:8000/auth/callback`) | No |
| `SESSION_SECRET_KEY` | Secret for signing session cookies | Yes |
| `SESSION_MAX_AGE` | Session TTL in seconds (default: `86400`) | No |
| `RATE_LIMIT_MAX_REQUESTS` | Max emails per user per window (default: `3`) | No |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate-limit window in seconds (default: `600`) | No |

\* Required only if using the Google login + email share feature.

## Themes

The newsletter supports three themes, toggled via the button in the header:

- **☀️ Light** — Clean slate palette with indigo accents
- **🌙 Dark** — Deep navy, perfect for night reading
- **🍂 Warm** — Cozy amber tones, easy on the eyes

Theme preference is saved in localStorage and applied before page render (no flash).

## License

MIT
