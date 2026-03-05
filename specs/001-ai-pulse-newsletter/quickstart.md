# Quickstart: AI Pulse Newsletter

**Feature**: `001-ai-pulse-newsletter`
**Date**: 2026-03-03

---

## Prerequisites

- Python 3.11+
- MongoDB 7.x running locally or accessible via URI
- An OpenAI-compatible API key

---

## 1. Clone & Branch

```bash
git clone <repo-url>
cd ai-pulse-newsletter
git checkout 001-ai-pulse-newsletter
```

---

## 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows
```

---

## 3. Install Dependencies

```bash
pip install fastapi "uvicorn[standard]" "pymongo[async]" pydantic pydantic-settings python-dotenv httpx jinja2
```

Dev dependencies:

```bash
pip install pytest pytest-asyncio ruff mypy
```

---

## 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=ai_pulse
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
ADMIN_API_KEY=your-admin-key-here
APP_ENV=development
APP_PORT=8000
```

---

## 5. Start MongoDB

**Option A — Docker** (recommended for development):

```bash
docker run -d -p 27017:27017 --name ai-pulse-mongo mongo:7
```

**Option B — Local install**: See https://www.mongodb.com/docs/manual/installation/

---

## 6. Run the Server

```bash
uvicorn backend.main:app --reload --port 8000
```

Visit http://localhost:8000 in your browser. If no editions exist, you'll see the empty-state page.

---

## 7. Generate Your First Newsletter

```bash
curl -X POST http://localhost:8000/api/v1/newsletter/generate \
  -H "X-API-Key: your-admin-key-here"
```

Refresh the homepage to see the generated newsletter.

---

## 8. Run Tests

```bash
pytest tests/ -v
```

---

## 9. Run Linter & Type Checker

```bash
ruff check backend/ tests/
mypy backend/
```

---

## Key URLs

| URL | Description |
|-----|-------------|
| http://localhost:8000 | Homepage (latest newsletter) |
| http://localhost:8000/archive | Newsletter archive |
| http://localhost:8000/edition/{id} | Specific edition |
| http://localhost:8000/api/v1/health | Health check |
| http://localhost:8000/docs | Swagger UI (auto-generated) |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Connection refused` on MongoDB | Ensure MongoDB is running: `docker ps` or check local service |
| `401 Unauthorized` on generate | Verify `X-API-Key` header matches `ADMIN_API_KEY` in `.env` |
| `502 Bad Gateway` on generate | Check `OPENAI_API_KEY` is valid and the model name is correct |
| Import errors | Ensure virtual environment is activated and dependencies installed |
