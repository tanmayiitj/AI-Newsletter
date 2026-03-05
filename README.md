# AI Pulse Newsletter

An AI-powered newsletter web application that curates and presents the latest AI industry content in a beautiful, story-driven layout.

## Architecture

- **Backend**: Python 3.11+ / FastAPI with Pydantic v2 models
- **Database**: MongoDB via pymongo AsyncMongoClient
- **Frontend**: Vanilla HTML/CSS/JS with Jinja2 server-side rendering
- **LLM**: OpenAI API with Structured Outputs for content generation

### Project Structure

```
backend/           # FastAPI application
├── config/        # Settings, templates
├── models/        # Pydantic data models
├── services/      # Business logic (LLM, content generation, CRUD)
├── routers/       # API endpoints and page routes
└── database/      # MongoDB connection

frontend/          # Static assets and templates
├── templates/     # Jinja2 HTML templates
└── static/        # CSS, JS, images

tests/             # pytest test suite
```

### 4-Layer Architecture

1. **Config** — Settings, environment variables
2. **Models** — Pydantic schemas, enums, validation
3. **Services** — Business logic, LLM interaction, database CRUD
4. **Routers** — HTTP endpoints, request/response handling

## Setup

### Prerequisites

- Python 3.11+
- MongoDB 7.x (local or Docker)
- OpenAI API key

### Quick Start

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# Install dependencies
pip install fastapi "uvicorn[standard]" "pymongo[async]" pydantic pydantic-settings python-dotenv httpx jinja2

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB URI, OpenAI API key, and admin key

# Start MongoDB (Docker)
docker run -d -p 27017:27017 --name ai-pulse-mongo mongo:7

# Run the server
uvicorn backend.main:app --reload --port 8000
```

### Generate a Newsletter

```bash
curl -X POST http://localhost:8000/api/v1/newsletter/generate \
  -H "X-API-Key: your-admin-key-here"
```

## Key URLs

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | Homepage (latest newsletter) |
| `http://localhost:8000/archive` | Newsletter archive |
| `http://localhost:8000/api/v1/health` | Health check |
| `http://localhost:8000/docs` | OpenAPI documentation |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/newsletter/generate` | API Key | Generate new edition |
| GET | `/api/v1/newsletter/latest` | None | Get latest edition |
| GET | `/api/v1/newsletter/archive` | None | Paginated archive |
| GET | `/api/v1/newsletter/{id}` | None | Get edition by ID |
| GET | `/api/v1/health` | None | Health check |
