# ⚡ AI Pulse Newsletter — Complete Setup Guide

Step-by-step instructions for running the full AI Pulse Newsletter platform locally, from cloning to generating your first edition and chatting with the built-in AI assistant.

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed and available:

| Requirement | Minimum Version | Notes |
|---|---|---|
| **Python** | 3.10+ | 3.12 recommended; check with `python --version` |
| **pip** | Latest | Comes with Python; upgrade with `pip install --upgrade pip` |
| **Git** | Any recent | For cloning the repository |
| **Web browser** | Any modern | For using the frontend |
| **MongoDB Atlas account** | — | Free tier works; or run MongoDB locally |
| **OpenAI API key** | — | Requires a paid/credits account at [platform.openai.com](https://platform.openai.com/) |

> **Node.js is NOT required.** The frontend is pure HTML/CSS/JS served by FastAPI — no build step.

---

## 📥 1. Clone the Repository

```bash
git clone https://github.com/tanmayiitj/AI-Newsletter.git
cd AI-Newsletter
```

---

## 🐍 2. Set Up a Python Virtual Environment

A virtual environment keeps project dependencies isolated from your system Python.

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows — PowerShell:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows — Command Prompt (CMD):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

> **Verify activation:** Your terminal prompt should show `(.venv)` at the beginning. Every subsequent command in this guide assumes the environment is active.

---

## 📦 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, Uvicorn, pymongo, LangChain, ChromaDB, feedparser, httpx, Jinja2, Pydantic Settings, itsdangerous, tenacity, and certifi.

> **If you see an error about `chromadb`**, ensure you are running Python 3.10+:
> ```bash
> python --version
> ```

---

## 🔐 4. Configure Environment Variables

### 4a. Copy the example file

```bash
cp .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

### 4b. Open `.env` in your editor and fill in every value

```env
# ── Database ─────────────────────────────────────────────────────────
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?appName=Cluster0
MONGODB_DB_NAME=ai_pulse

# ── OpenAI ───────────────────────────────────────────────────────────
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini

# ── Admin API key (protects /generate and /ingest) ───────────────────
ADMIN_API_KEY=your-admin-api-key-here

# ── App ──────────────────────────────────────────────────────────────
APP_ENV=development
APP_PORT=8000

# ── Google OAuth (needed for login + email-to-self) ──────────────────
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# ── Session ──────────────────────────────────────────────────────────
SESSION_SECRET_KEY=your-session-secret-here
SESSION_MAX_AGE=86400

# ── Rate limiting (share endpoint) ───────────────────────────────────
RATE_LIMIT_MAX_REQUESTS=3
RATE_LIMIT_WINDOW_SECONDS=600
```

### 4c. How to obtain each required value

| Variable | How to get it |
|---|---|
| `MONGODB_URI` | 1. Log in to [mongodb.com/atlas](https://www.mongodb.com/atlas) → your cluster → **Connect** → **Drivers** → copy the connection string. 2. Replace `<username>` and `<password>` with your database user credentials. 3. Whitelist your IP under **Network Access → Add Current IP**. |
| `OPENAI_API_KEY` | Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys) → **Create new secret key**. Ensure your account has credits. |
| `ADMIN_API_KEY` | Generate a random key: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` | 1. Open [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials). 2. Create a project. 3. **Create Credentials → OAuth 2.0 Client ID** → Application type: **Web application**. 4. Add `http://localhost:8000/auth/callback` under **Authorised redirect URIs**. 5. Enable the **Gmail API** and **Google People API** for your project. |
| `SESSION_SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |

> **Google OAuth is optional.** If you skip `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`, the login button will redirect to an error. Newsletter generation and the chatbot work without Google credentials.

---

## 🗄️ 5. Database Setup

AI Pulse uses **MongoDB** for storing newsletter editions. **No manual schema or migration steps are required** — the application creates indexes automatically on startup.

If you are using **MongoDB Atlas (recommended)**:
1. Make sure your cluster is running and the user in `MONGODB_URI` has **Read and Write** access to the `ai_pulse` database.
2. Whitelist your machine's IP address under **Network Access** (or use `0.0.0.0/0` for development).

If you prefer to run **MongoDB locally**:
```bash
# macOS (Homebrew)
brew services start mongodb/brew/mongodb-community

# Ubuntu / Debian
sudo systemctl start mongod
```
Set `MONGODB_URI=mongodb://localhost:27017` in your `.env`.

> **ChromaDB** (the vector store for the chatbot) stores its data locally in the `./chroma_data/` directory. This directory is created automatically on first use and is excluded from Git via `.gitignore`. No extra setup is needed.

---

## ▶️ 6. Run the Backend

The backend serves everything — pages, REST API, and the chatbot — on a single port.

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Expected startup output:**
```
INFO | backend.database.connection | Connecting to MongoDB ...
INFO | backend.database.connection | MongoDB connection established
INFO | backend.database.connection | MongoDB indexes ensured
INFO | backend.main                | ChromaDB vector store ready
INFO | backend.main                | Auto-ingest complete: {'ingested': 0, 'skipped': 0, 'errors': []}
INFO | uvicorn.server              | Application startup complete.
INFO | uvicorn.server              | Uvicorn running on http://0.0.0.0:8000
```

> **For development with auto-reload:**
> ```bash
> uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
> ```

---

## 🌐 7. Open the Frontend

The frontend is rendered server-side by FastAPI's Jinja2 engine. Once the backend is running, open your browser:

```
http://localhost:8000
```

If no editions have been generated yet, you will see the empty state page. After generating your first edition (Step 9), the homepage will display it automatically.

| Page | URL |
|---|---|
| Homepage (latest edition) | `http://localhost:8000/` |
| Archive | `http://localhost:8000/archive` |
| Individual edition | `http://localhost:8000/edition/<edition_id>` |
| Health check (JSON) | `http://localhost:8000/api/v1/health` |

---

## 💬 8. Use the Chatbot

The chatbot is embedded in the main backend — **no separate process is needed**.

### Via the UI (recommended)

1. Open `http://localhost:8000` in your browser.
2. Click the **⚡ purple chat icon** in the bottom-right corner.
3. Type a question such as:
   - *"What were the major AI developments this month?"*
   - *"List all AI job roles mentioned in the newsletter."*
   - *"What tools were recommended for corporate teams?"*

The chatbot answers based only on ingested newsletter content and cites the edition and section for every fact.

### Via the API

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What AI tools were mentioned?", "session_id": null}'
```

**Windows (PowerShell):**
```powershell
$body = @{ message = "What AI tools were mentioned?"; session_id = $null } | ConvertTo-Json
Invoke-RestMethod -Method POST `
  -Uri "http://localhost:8000/api/v1/chat" `
  -ContentType "application/json" `
  -Body $body
```

> **The chatbot needs ingested data to answer questions.** If no newsletters have been generated and ingested yet, it will reply that it has no information. Follow Steps 9 and 10 to populate its knowledge base.

---

## 📨 9. Generate a Newsletter Edition

Newsletter generation is triggered manually via the admin API. It scrapes live news and jobs, calls OpenAI to generate all five sections, and saves the result to MongoDB.

```bash
curl -X POST http://localhost:8000/api/v1/newsletter/generate \
  -H "X-API-Key: YOUR_ADMIN_API_KEY"
```

**Windows (PowerShell):**
```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://localhost:8000/api/v1/newsletter/generate" `
  -Headers @{ "X-API-Key" = "YOUR_ADMIN_API_KEY" }
```

Replace `YOUR_ADMIN_API_KEY` with the value you set in `.env`.

**What happens behind the scenes:**

1. Scrapes up to 5 recent articles from each of 7 AI RSS feeds (TechCrunch, The Verge, VentureBeat, Ars Technica, WIRED, MIT News, Google AI Blog).
2. Scrapes AI/ML job listings from RemoteOK and Arbeitnow, filtered by keyword.
3. Calls OpenAI GPT to generate each of the five sections as structured JSON:
   - Trending AI Topics
   - Top Developments
   - Corporate AI Tools
   - Future Requirements & Trends
   - AI Jobs Board
4. Generates an overall edition headline and executive summary.
5. Saves the completed edition to MongoDB with status `published`.

> **Generation takes 1–3 minutes.** Watch the backend terminal for progress logs.  
> A `409 Conflict` response means a generation is already in progress — wait for it to finish.

After generation completes, refresh `http://localhost:8000` to see the new edition.

---

## 🔄 10. Ingest Newsletters into the Chatbot

After generating one or more editions, ingest them into ChromaDB so the chatbot can answer questions about them.

### Incremental ingestion (recommended — only processes new editions)

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "X-API-Key: YOUR_ADMIN_API_KEY"
```

**Windows (PowerShell):**
```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://localhost:8000/api/v1/ingest" `
  -Headers @{ "X-API-Key" = "YOUR_ADMIN_API_KEY" }
```

**Expected response:**
```json
{ "ingested": 1, "skipped": 0, "errors": [] }
```

### Full re-index (re-processes all editions from scratch)

```bash
curl -X POST "http://localhost:8000/api/v1/ingest?full_reindex=true" \
  -H "X-API-Key: YOUR_ADMIN_API_KEY"
```

> **Note:** The backend also runs an incremental auto-ingest at startup. If you restart the server after generating new editions, they are picked up automatically — you do not need to trigger ingestion manually unless you want immediate results or a full re-index.

---

## 🧪 11. Testing the Setup

Run through this checklist to confirm everything is working correctly:

- [ ] **Backend is healthy:** `curl http://localhost:8000/api/v1/health` returns `{"status":"healthy","database":"connected",...}`
- [ ] **Frontend loads:** `http://localhost:8000` opens without errors (empty state is expected before first generation)
- [ ] **Newsletter generation works:** `POST /api/v1/newsletter/generate` completes and `http://localhost:8000` shows a new edition
- [ ] **Archive works:** `http://localhost:8000/archive` lists editions
- [ ] **Chatbot responds:** click the chat icon and ask *"What is in this newsletter?"* — you receive an answer with source citations
- [ ] **Google login works** (optional): clicking **Login** redirects to Google consent screen and returns you logged in
- [ ] **Email share works** (optional): after logging in, open any edition, click **Send Newsletter**, and check your Gmail inbox

---

## 🚀 12. Deployment

### Backend — Render

The live deployment runs on [Render](https://render.com). To deploy your own instance:

1. Push your repository to GitHub.
2. Create a new **Web Service** on Render, select your repo.
3. Set **Build Command:** `pip install -r requirements.txt`
4. Set **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables from your `.env` in the **Environment** tab.
6. Update `GOOGLE_REDIRECT_URI` to your Render service URL (e.g., `https://your-app.onrender.com/auth/callback`) and add it to your Google OAuth client's authorised redirect URIs.
7. Deploy.

> ⚠️ **Warning — ChromaDB persistence on Render:** Render's free tier does **not** persist disk storage between deploys. Every new deployment will wipe the `chroma_data/` directory, requiring a full re-ingest. For production use, either add a **Render Disk** (paid) or replace ChromaDB with a cloud-hosted vector database before deploying.

### Backend — Railway / Fly.io

The same start command works on any platform that supports Python:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Set all environment variables in the platform dashboard.

### Frontend

The frontend is served by FastAPI itself — there is no separate static hosting needed. It is deployed automatically as part of the backend service.

---

## 🐛 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | Virtual environment not active | Run `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\Activate.ps1` (Windows), then re-run the command. |
| `ModuleNotFoundError: No module named 'chromadb'` | Python version too old or deps not installed | Ensure Python ≥ 3.10, then run `pip install -r requirements.txt`. |
| Backend fails to start — `ServerSelectionTimeoutError` | MongoDB URI wrong or IP not whitelisted | Double-check `MONGODB_URI` in `.env`. In Atlas, go to **Network Access → Add Current IP**. |
| `Port 8000 already in use` | Another process holds the port | **macOS/Linux:** `lsof -i :8000 \| awk 'NR>1 {print $2}' \| xargs kill -9` **Windows (PowerShell):** `Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess \| Stop-Process -Force` |
| `POST /generate` returns `401 Unauthorized` | Wrong or missing admin API key | Check the `ADMIN_API_KEY` value in `.env` matches what you send in the `X-API-Key` header. |
| `POST /generate` returns `409 Conflict` | Generation already in progress | Wait for the current generation to finish (watch backend logs), then retry. |
| OpenAI errors during generation or ingestion | Invalid key, quota exceeded, or rate limit | Check your key at [platform.openai.com](https://platform.openai.com/), verify you have credits, and retry (the ingestion pipeline retries automatically with backoff). |
| Chatbot replies "I don't have that information" | No data ingested into ChromaDB | Generate at least one edition, then trigger ingestion: `POST /api/v1/ingest`. |
| CORS error in browser console | Frontend calling wrong origin | Ensure you are accessing the app via `http://localhost:8000`, not a different host or port. |
| Google login fails — `400 Google login failed` | OAuth credentials wrong or redirect URI mismatch | Verify `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` match exactly what is configured in Google Cloud Console. |
| Gmail send fails — `502 Email could not be sent` | Gmail API not enabled or OAuth scope missing | In Google Cloud Console, enable the **Gmail API** and ensure the OAuth scope `https://www.googleapis.com/auth/gmail.send` is listed. |

---

## ❓ FAQ

**Q: Do I need to run a separate process for the chatbot?**  
A: No. The chatbot router is embedded inside the main backend (`backend/main.py`). A single `uvicorn backend.main:app` process runs everything on port 8000. The `chatbot/main.py` file exists for advanced users who want to run the chatbot as a standalone microservice.

**Q: How often should I generate a new newsletter?**  
A: There is no built-in scheduler. Call `POST /api/v1/newsletter/generate` whenever you want a new edition — weekly is the intended cadence. Each call creates one edition with the next sequential number.

**Q: Will the chatbot answer questions about the internet or topics outside the newsletters?**  
A: No. The chatbot is configured to answer only from the newsletter content stored in ChromaDB. If the requested information is not in any ingested edition, it will say so explicitly.

**Q: What does it cost to run?**  
A: The main costs are OpenAI API usage (each generation call uses roughly 4,000–6,000 output tokens across all five sections) and MongoDB Atlas (free tier is sufficient for dozens of editions). ChromaDB runs locally at no cost.

**Q: Can I change the OpenAI model?**  
A: Yes. Set `OPENAI_MODEL` in `.env` to any OpenAI chat model, for example `gpt-4o` or `gpt-3.5-turbo`. Larger models produce higher quality content but cost more per generation.

**Q: How do I delete an edition?**  
A: Currently there is no delete endpoint in the API. You can delete documents directly from MongoDB Atlas using the Data Explorer or `mongosh`.

---

## 📞 Support

If you encounter a problem not covered in this guide, please [open an issue](https://github.com/tanmayiitj/AI-Newsletter/issues) on GitHub with:
- The exact error message and stack trace
- The command you ran
- Your Python version (`python --version`) and operating system
