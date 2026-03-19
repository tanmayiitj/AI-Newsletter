# AI Pulse Newsletter — Project Constitution

> **Status:** Active | **Version:** 1.0 | **Last Updated:** 2026-03-17

---

## Purpose

This constitution defines the non-negotiable rules, architectural decisions, and governance model for the AI Pulse Newsletter project. Every contributor — human or AI agent — must read, understand, and follow these principles before touching a line of code.

---

## Core Principles (NON-NEGOTIABLE)

### P1 · File Size Discipline
**No file may exceed 500 lines.** If a file approaches this limit, split it by responsibility before adding more code. This applies to Python, HTML, CSS, and JavaScript alike.

### P2 · Modular 4-Layer Architecture
The backend enforces strict separation across exactly four layers, in dependency order:

```
config → models → services → routers
```

- `config/` — settings and shared infrastructure (templates, DB config). No business logic.
- `models/` — Pydantic data schemas only. No I/O, no service calls.
- `services/` — all business logic, DB access, LLM calls, scraping. No HTTP concerns.
- `routers/` — HTTP boundary only. Calls services, returns responses. No direct DB or LLM calls.

**A layer may only import from layers to its left.** Routers import services. Services import models. Models import nothing internal. Config imports nothing internal.

### P3 · Security-First Credentials
**All secrets MUST be loaded via `.env` + `pydantic_settings.BaseSettings`.** No secret string may be hardcoded anywhere in the codebase. The `.env.example` file must be kept in sync whenever new env vars are added.

---

## Mandatory Technical Decisions

| Concern | Decision | Rationale |
|---|---|---|
| MongoDB async driver | `pymongo[async]` (`AsyncMongoClient`) | Motor is deprecated |
| ObjectId serialisation | `PyObjectId = Annotated[str, BeforeValidator(str)]` with `Field(alias="_id")` | Consistent Pydantic v2 pattern |
| API authentication | `APIKeyHeader` + `secrets.compare_digest()` | Constant-time comparison prevents timing attacks |
| Concurrency guard | `asyncio.Lock` — check `lock.locked()` before acquiring | Prevents duplicate generation runs |
| LLM structured output | OpenAI API with `"response_format": {"type": "json_object"}` + Pydantic response models | Reliable parsing |
| Templates | Shared `Jinja2Templates` instance in `backend/config/templates.py` | Avoids circular imports |
| Frontend stack | Vanilla HTML/CSS/JS — **no frontend frameworks** | Simplicity and zero build step |
| Python docstrings | Google-style on all public functions | Consistent documentation |
| HTML/CSS/JS comments | Block comment at file top explaining purpose | Orientation for every file |
| Email transport | SMTP via `smtplib` (stdlib) or `aiosmtplib` for async — credentials in `.env` | No external SDK dependency |
| Rate limiting | In-memory token-bucket or simple timestamp tracking per IP in `services/` | Prevent email abuse without Redis dependency |

---

## Project Structure

```
backend/
├── config/          # Settings, Jinja2 templates, DB lifespan
├── database/        # AsyncMongoClient connection + lifespan
├── models/          # Pydantic schemas (newsletter, jobs, share)
├── routers/         # FastAPI routers (newsletter, pages, health, share)
└── services/        # Business logic (content_generator, newsletter_service,
│                    #   jobs_service, llm_client, jobs_scraper, email_service,
│                    #   rate_limiter)
frontend/
├── static/
│   ├── css/         # reset, typography, layout, sections, responsive
│   └── js/          # theme, sections, archive, share, smooth-scroll, email-share
└── templates/       # Jinja2 HTML templates + partials
specs/               # Feature specifications (spec-kit format)
tests/               # Pytest test suite
```

---

## Governance

### Adding a New Feature
1. Create a spec directory: `specs/NNN-feature-name/`
2. Write `spec.md`, `plan.md`, `tasks.md` (and optionally `data-model.md`, `contracts/`, `research.md`)
3. Open a PR for spec review before any implementation begins
4. Implementation PR must reference the spec

### Amending This Constitution
- Amendments require a dedicated PR with the subject `chore: amend constitution — <topic>`
- Changes to NON-NEGOTIABLE principles (P1–P3) require explicit acknowledgement in the PR description

### Definition of Done (per task)
- [ ] Code passes all existing tests
- [ ] New code has corresponding unit/integration tests
- [ ] No file exceeds 500 lines
- [ ] All public functions have Google-style docstrings
- [ ] `.env.example` updated if new env vars added
- [ ] Spec `tasks.md` checkbox ticked

---

## Existing Features Reference

| Feature ID | Name | Spec Location | Status |
|---|---|---|---|
| 001 | AI Pulse Newsletter (core) | `specs/001-ai-pulse-newsletter/` | ✅ Shipped |
| 002 | Share Newsletter via Email | `specs/002-email-share/` | 🔵 Planned |
