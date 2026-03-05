# AI Agent Development Guidelines

## Project Constitution

This project follows a constitution defined in `.specify/memory/constitution.md` with 9 core principles. Three are **NON-NEGOTIABLE**:

1. **File Size Discipline** — No file exceeds 500 lines
2. **Modular Architecture** — Strict 4-layer separation (config → models → services → routers)
3. **Security-First Credentials** — All secrets via `.env`, never hardcoded

## Key Technical Decisions

- **MongoDB driver**: Use `pymongo[async]` (AsyncMongoClient), NOT Motor (deprecated)
- **ObjectId handling**: `PyObjectId = Annotated[str, BeforeValidator(str)]` with `Field(alias="_id")`
- **API auth**: `APIKeyHeader` + `secrets.compare_digest()` — constant-time comparison
- **Concurrency**: `asyncio.Lock` for generation guard — check `lock.locked()` before acquiring
- **LLM output**: OpenAI Structured Outputs with `response_format` + Pydantic models
- **Templates**: Shared `Jinja2Templates` instance in `backend/config/templates.py` (avoids circular imports)

## Coding Standards

- Python: Google-style docstrings on all public functions
- HTML/CSS/JS: Block comments at file top explaining purpose
- No frontend frameworks — vanilla HTML/CSS/JS only
- All dependencies installed explicitly (no auto-generated requirements.txt)

## Specification Documents

Feature specifications live in `specs/001-ai-pulse-newsletter/`:
- `spec.md` — Feature specification
- `plan.md` — Implementation plan
- `data-model.md` — Entity schemas
- `contracts/` — API contracts
- `research.md` — Technology decisions
- `tasks.md` — Implementation tasks
