# AI Pulse — Complete Setup & Operations Guide

Step-by-step guide to run the entire AI Pulse Newsletter platform: backend, chatbot, newsletter generation, and ingestion.

---

## Prerequisites

- **Python 3.12+** installed
- **MongoDB Atlas** account with a cluster (or local MongoDB)
- **OpenAI API key** from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Git** installed

---

## Step 1: Clone & Create Virtual Environment

```bash
git clone https://github.com/tanmayiitj/AI-Newsletter.git
cd AI-Newsletter
```

Create and activate a virtual environment:

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

> **Verify:** Your terminal prompt should show `(.venv)` prefix.

---

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, Uvicorn, pymongo, LangChain, ChromaDB, and all other dependencies.

---

## Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Or create it manually with these values:

```env
# Database — replace with your MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?appName=Cluster0
MONGODB_DB_NAME=ai_pulse

# OpenAI — replace with your real API key
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Admin API Key — used for newsletter generation + chatbot ingestion
# Generate one: python -c "import secrets; print(secrets.token_urlsafe(32))"
ADMIN_API_KEY=your-admin-api-key-here

# App config
APP_ENV=development
APP_PORT=8000
SESSION_SECRET_KEY=your-session-secret-here

# Chatbot config
CHATBOT_PORT=8001
CHROMA_PERSIST_DIR=./chroma_data
```

### Required values you must set:

| Variable | Where to get it |
|----------|----------------|
| `MONGODB_URI` | MongoDB Atlas → Connect → Drivers → Connection String |
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `ADMIN_API_KEY` | Run: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `SESSION_SECRET_KEY` | Run: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |

---

## Step 4: Start the Backend (Port 8000)

Open **Terminal 1** and run:

```bash
# Make sure venv is activated
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

# Start backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Verify:** Open [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) in your browser. You should see:
```json
{"status": "ok"}
```

> **Note:** If you see a MongoDB connection error, check that your `MONGODB_URI` is correct and your IP is whitelisted in MongoDB Atlas (Network Access → Add Current IP).

---

## Step 5: Start the Chatbot (Port 8001)

Open **Terminal 2** and run:

```bash
# Make sure venv is activated
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

# Start chatbot
uvicorn chatbot.main:app --host 0.0.0.0 --port 8001
```

**Expected output:**
```
INFO:     Initializing chatbot service...
INFO:     ChromaDB initialized at ./chroma_data
INFO:     ChromaDB vector store ready
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Verify:** Open [http://localhost:8001/health](http://localhost:8001/health). You should see:
```json
{"status": "ok", "service": "chatbot"}
```

---

## Step 6: Generate Your First Newsletter

With the backend running (Terminal 1), open **Terminal 3** and run:

```bash
# Windows (PowerShell)
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/newsletter/generate" -Headers @{"X-API-Key"="YOUR_ADMIN_API_KEY"}

# macOS / Linux / curl
curl -X POST http://localhost:8000/api/v1/newsletter/generate \
  -H "X-API-Key: YOUR_ADMIN_API_KEY"
```

Replace `YOUR_ADMIN_API_KEY` with the value you set in `.env`.

**What happens:**
1. Scrapes AI news from 7 RSS feeds (TechCrunch, The Verge, VentureBeat, etc.)
2. Scrapes AI/ML jobs from RemoteOK and Arbeitnow
3. Sends scraped content to OpenAI GPT-4o-mini to generate 5 curated sections
4. Saves the edition to MongoDB as "published"

**This takes 1–3 minutes.** Watch Terminal 1 for progress logs.

**Verify:** Open [http://localhost:8000](http://localhost:8000) to see your newsletter.

---

## Step 7: Ingest Newsletter(s) into the Chatbot

After generating one or more newsletters, ingest them into ChromaDB so the chatbot can answer questions about them.

### Ingest new newsletters only (skips already-ingested editions):

```bash
# Windows (PowerShell)
Invoke-RestMethod -Method POST -Uri "http://localhost:8001/api/v1/ingest" -Headers @{"X-API-Key"="YOUR_ADMIN_API_KEY"}

# curl
curl -X POST http://localhost:8001/api/v1/ingest \
  -H "X-API-Key: YOUR_ADMIN_API_KEY"
```

**What happens:**
1. Connects to MongoDB and fetches all published editions
2. Skips editions already stored in ChromaDB
3. For each new edition, summarizes every section (300–500 words) using OpenAI
4. Embeds the summaries into ChromaDB as vector documents
5. Stores metadata (edition number, section type, year, month, edition ID) for filtering

**Expected response:**
```json
{
  "ingested": 1,
  "skipped": 0,
  "errors": []
}
```

### Re-ingest ALL newsletters (full re-index):

```bash
# Windows (PowerShell)
Invoke-RestMethod -Method POST -Uri "http://localhost:8001/api/v1/ingest?full_reindex=true" -Headers @{"X-API-Key"="YOUR_ADMIN_API_KEY"}

# curl
curl -X POST "http://localhost:8001/api/v1/ingest?full_reindex=true" \
  -H "X-API-Key: YOUR_ADMIN_API_KEY"
```

Use this if you want to re-summarize and re-embed everything from scratch.

---

## Step 8: Use the Chatbot

### Option A: Chat Widget (UI)

1. Open [http://localhost:8000](http://localhost:8000)
2. Click the **purple chat icon** in the bottom-right corner
3. Ask questions like:
   - "What were the major AI news this month?"
   - "How many job roles were listed?"
   - "Tell me about OpenAI's latest announcements"
   - "What AI tools were mentioned in the newsletter?"

### Option B: Chat API (curl/Postman)

```bash
# curl
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What were the major AI news?", "session_id": null}'

# Windows (PowerShell)
$body = @{message="What were the major AI news?"; session_id=$null} | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:8001/api/v1/chat" -ContentType "application/json" -Body $body
```

**Response includes:**
- `answer` — The AI-generated response grounded in newsletter content
- `sources` — Edition numbers and section titles used to generate the answer
- `session_id` — UUID for conversation continuity (pass it in subsequent requests)

---

## Complete Workflow Summary

```
┌─────────────────────────────────────────────────────────┐
│                    ONE-TIME SETUP                        │
│  1. Clone repo                                          │
│  2. Create venv + install deps                          │
│  3. Configure .env                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   START SERVICES                         │
│  Terminal 1: uvicorn backend.main:app --port 8000       │
│  Terminal 2: uvicorn chatbot.main:app --port 8001       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              GENERATE NEWSLETTER                         │
│  POST http://localhost:8000/api/v1/newsletter/generate   │
│  Header: X-API-Key: YOUR_KEY                            │
│  (Scrapes news + jobs → GPT generates sections → saves) │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│           INGEST INTO CHATBOT                            │
│  POST http://localhost:8001/api/v1/ingest                │
│  Header: X-API-Key: YOUR_KEY                            │
│  (Summarizes sections → embeds in ChromaDB)             │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 USE THE APP                               │
│  Browser: http://localhost:8000  (read newsletters)     │
│  Chat widget: click purple icon (ask questions)         │
│  Archive: http://localhost:8000/archive (search/filter) │
└─────────────────────────────────────────────────────────┘
```

---

## Generating Multiple Newsletters

Each time you call the generate endpoint, a new edition is created with the next edition number. To build up an archive:

```bash
# Generate edition #1
curl -X POST http://localhost:8000/api/v1/newsletter/generate -H "X-API-Key: YOUR_KEY"

# Wait for it to complete (check Terminal 1 logs)...

# Generate edition #2
curl -X POST http://localhost:8000/api/v1/newsletter/generate -H "X-API-Key: YOUR_KEY"

# After generating all editions, ingest them all at once:
curl -X POST http://localhost:8001/api/v1/ingest -H "X-API-Key: YOUR_KEY"
```

The ingestion endpoint automatically detects which editions are new and only processes those.

---

## Troubleshooting

### Backend won't start — MongoDB connection error
- Check `MONGODB_URI` in `.env` is correct
- Whitelist your IP in MongoDB Atlas: **Network Access → Add Current IP Address**
- Ensure the database user has read/write permissions

### Chatbot won't start — ModuleNotFoundError
- Make sure your venv is activated: `(.venv)` should appear in your prompt
- Run `pip install -r requirements.txt` again
- Check you're using the venv Python: `python -c "import sys; print(sys.executable)"`

### Port already in use
```bash
# Windows — find and kill process on port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# macOS/Linux
lsof -i :8000 | awk 'NR>1 {print $2}' | xargs kill -9
```

### Newsletter generation returns 409 Conflict
A generation is already in progress. Wait for it to finish (watch backend logs).

### Chatbot says "No newsletter data has been ingested yet"
You need to run the ingestion step (Step 7) after generating newsletters.

### Chat answers are only from the current month
This is by design for temporal queries like "latest news". For general questions (e.g., "What is LangChain?"), the chatbot searches all editions automatically.

### OpenAI rate limit errors during ingestion
The ingestion pipeline retries automatically with exponential backoff (up to 4 attempts). If it still fails, wait a minute and re-run the ingest command — already-processed editions will be skipped.

---

## Quick Reference — All Commands

| Action | Command |
|--------|---------|
| Activate venv (Windows) | `.venv\Scripts\activate` |
| Activate venv (macOS/Linux) | `source .venv/bin/activate` |
| Install dependencies | `pip install -r requirements.txt` |
| Start backend | `uvicorn backend.main:app --host 0.0.0.0 --port 8000` |
| Start chatbot | `uvicorn chatbot.main:app --host 0.0.0.0 --port 8001` |
| Generate newsletter | `curl -X POST http://localhost:8000/api/v1/newsletter/generate -H "X-API-Key: YOUR_KEY"` |
| Ingest into chatbot | `curl -X POST http://localhost:8001/api/v1/ingest -H "X-API-Key: YOUR_KEY"` |
| Full re-ingest | `curl -X POST "http://localhost:8001/api/v1/ingest?full_reindex=true" -H "X-API-Key: YOUR_KEY"` |
| Chat (API) | `curl -X POST http://localhost:8001/api/v1/chat -H "Content-Type: application/json" -d '{"message":"your question"}'` |
| Health check (backend) | `curl http://localhost:8000/api/v1/health` |
| Health check (chatbot) | `curl http://localhost:8001/health` |
| View app | Open `http://localhost:8000` |
| View archive | Open `http://localhost:8000/archive` |
