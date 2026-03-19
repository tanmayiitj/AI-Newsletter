# AI Pulse Newsletter

A production-ready AI-powered newsletter platform that automatically curates the latest AI industry news, tools, and job opportunities into a beautiful, themed weekly digest.

## Features

- **Automated Content Generation** — Scrapes real AI news from 7 RSS feeds (TechCrunch, The Verge, VentureBeat, Ars Technica, WIRED, MIT News, Google AI Blog) and uses OpenAI GPT to generate curated newsletter sections
- **Real Job Listings** — Scrapes AI/ML jobs from RemoteOK and Arbeitnow with intelligent keyword filtering
- **5 Newsletter Sections** — Trending Topics, Top Developments, Corporate Tools, Future Requirements, Jobs Board
- **Section Summaries** — Each section includes an AI-generated preview description shown when collapsed
- **Expandable Sections** — All sections collapse by default with smooth animations; click to expand
- **Theme System** — Light, Dark, and Warm themes with localStorage persistence and no-flash loading
- **Archive with Search** — Full-text search across all newsletters with custom themed year/month filter dropdowns
- **Responsive Design** — Mobile-first layout with Inter + Newsreader fonts, soft shadows, and subtle background patterns
- **Production-Ready** — OpenGraph meta tags, favicon, SSL certificate handling for MongoDB Atlas

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.9+, FastAPI, Uvicorn |
| **Database** | MongoDB Atlas (pymongo async) |
| **LLM** | OpenAI API (GPT-4o-mini default) |
| **Scraping** | httpx, feedparser (RSS) |
| **Frontend** | Vanilla HTML/CSS/JS, Jinja2 templates |
| **Styling** | CSS custom properties, 3 themes |

## Project Structure

```
backend/
├── config/          # Settings, Jinja2 templates config
├── database/        # MongoDB async connection + lifespan
├── models/          # Pydantic data models (newsletter, jobs)
├── routers/         # API endpoints, page routes
└── services/        # LLM client, content generator, news/jobs scrapers
frontend/
├── static/
│   ├── css/         # reset, typography, layout, sections, responsive
│   └── js/          # theme, sections, archive, share, smooth-scroll
└── templates/       # Jinja2 HTML templates + partials
```

## Quick Start

### 1. Clone & setup

```bash
git clone https://github.com/tanmayiitj/AI-Newsletter.git
cd AI-Newsletter
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux
pip install fastapi "uvicorn[standard]" "pymongo[async]" pydantic-settings httpx feedparser certifi
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
- **MongoDB Atlas** connection string
- **OpenAI API key** from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Admin API key** — generate one: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### 3. Run the server

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 4. Generate a newsletter

```bash
curl -X POST http://localhost:8000/api/v1/newsletter/generate -H "X-API-Key: YOUR_ADMIN_KEY"
```

### 5. View it

Open [http://localhost:8000](http://localhost:8000) in your browser.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | — | Latest newsletter |
| `GET` | `/archive` | — | Archive with search & filters |
| `GET` | `/edition/{id}` | — | Specific edition |
| `POST` | `/api/v1/newsletter/generate` | API Key | Generate new edition |
| `GET` | `/api/v1/newsletter/search` | — | Search newsletters (`?q=&year=&month=`) |
| `GET` | `/api/v1/newsletter/months` | — | Available years |
| `POST` | `/api/v1/share/send-to-self` | Session | Send newsletter to your email |
| `GET` | `/auth/login` | — | Google OAuth login redirect |
| `GET` | `/auth/callback` | — | Google OAuth callback |
| `POST` | `/auth/logout` | Session | Clear session |
| `GET` | `/auth/me` | Session | Current user info |
| `GET` | `/api/v1/health` | — | Health check |

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
