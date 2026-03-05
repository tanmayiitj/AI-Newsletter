# Research: AI Pulse Newsletter

**Date**: 2026-03-03
**Feature**: `001-ai-pulse-newsletter`
**Purpose**: Resolve technology decisions, best practices, and patterns for the implementation plan.

---

## 1. Async MongoDB Driver for FastAPI

**Decision**: Use PyMongo's `AsyncMongoClient` (not Motor) with FastAPI's lifespan context manager.

**Rationale**: Motor is officially deprecated as of May 2025 (critical bug fixes ending May 2027). MongoDB now recommends PyMongo's `AsyncMongoClient` as the replacement. The official MongoDB + FastAPI tutorial has already migrated.

**Pattern**:
- Create `AsyncMongoClient` inside a `@asynccontextmanager` lifespan function.
- Ping the database to verify connectivity at startup.
- Close the client after `yield` (shutdown).
- Pass the lifespan to `FastAPI(lifespan=db_lifespan)`.
- Connection pooling is handled automatically by `AsyncMongoClient`.

**Alternatives considered**:
- Motor (`AsyncIOMotorClient`): Deprecated May 2026; still functional but migration recommended.
- Module-level client initialization: No clean shutdown, harder to test.
- `@app.on_event("startup")`/`"shutdown"`: Deprecated in favor of lifespan pattern.

**Impact on plan**: Replace Motor with `pymongo[async]` in dependencies. Update `backend/database/connection.py` to use `pymongo.AsyncMongoClient`.

---

## 2. Pydantic v2 + MongoDB ObjectId Handling

**Decision**: Use `Annotated[str, BeforeValidator(str)]` as a `PyObjectId` type alias.

**Rationale**: This is the canonical approach from MongoDB's official FastAPI tutorial. Coerces `ObjectId` to `str` via a `BeforeValidator`, making it JSON-serializable while accepting raw `ObjectId` from MongoDB. Uses `Field(alias="_id")` with `populate_by_name=True`.

**Alternatives considered**:
- Beanie ODM: Heavy dependency, opinionated layer — unnecessary for this app size.
- Custom `__get_pydantic_core_schema__`: More complex, no benefit over `Annotated` pattern.
- String-based UUIDs: Doesn't work with standard MongoDB `_id`.

---

## 3. FastAPI + Jinja2 Server-Side Rendering

**Decision**: Use `Jinja2Templates` from `fastapi.templating` with `StaticFiles` mount.

**Rationale**: First-class FastAPI support via Starlette. Minimal setup: `Jinja2Templates(directory=...)`, mount `StaticFiles`, return `TemplateResponse`. Templates get `url_for()` for static assets and route links. Template compilation is cached automatically.

**Key practices**:
- Declare `response_class=HTMLResponse` on template routes.
- Pass `request` as first argument to `TemplateResponse`.
- Use `url_for('static', path='/...')` in templates for CSS/JS references.
- Mount: `app.mount("/static", StaticFiles(directory="..."), name="static")`.

**Alternatives considered**:
- Mako/Chameleon: Less ecosystem support, no advantage.
- React/Vue SPA: Overkill for content-display app; violates constitution IX.

---

## 4. OpenAI API Structured Output

**Decision**: Use Structured Outputs with `response_format` passing a Pydantic `BaseModel` class directly.

**Rationale**: Guarantees 100% schema adherence (not just valid JSON). The Python SDK supports `client.chat.completions.parse(response_format=MyModel)` directly. Eliminates manual parsing/validation and handles refusals programmatically. Multi-section newsletter content is modeled as nested Pydantic models.

**Alternatives considered**:
- JSON mode (`type: "json_object"`): Only guarantees valid JSON, not schema adherence.
- Function calling with strict mode: Better for tool-use, not direct content generation.
- Manual prompt + `json.loads()`: Fragile, requires retry logic.
- LangChain/instructor: Unnecessary dependency; native SDK handles this.

---

## 5. API Key Authentication for Admin Endpoint

**Decision**: Use `Security()` with `APIKeyHeader` from `fastapi.security`, implemented as a `Depends()` dependency.

**Rationale**: FastAPI's built-in `APIKeyHeader` is idiomatic, integrates with OpenAPI docs (Swagger "Authorize" button), and uses dependency injection. The API key is read from `X-API-Key` header, compared using `secrets.compare_digest()` (constant-time, prevents timing attacks), loaded from `.env`.

**Alternatives considered**:
- Custom middleware: Runs on every request including static files; doesn't integrate with OpenAPI.
- HTTP Basic Auth: Requires username+password pair; more suited for browser flows.
- OAuth2/JWT: Massive overkill for a single static admin key.
- Query parameter API key: Leaks key in URL/logs; insecure.

---

## 6. Generation Concurrency Guard

**Decision**: Use `asyncio.Lock` for single-server deployments.

**Rationale**: FastAPI runs on a single asyncio event loop. An `asyncio.Lock` reliably prevents concurrent generation. If a second request arrives during generation, return 409 Conflict immediately by checking `lock.locked()`.

**Pattern**:
- `generation_lock = asyncio.Lock()` at module level.
- Check `lock.locked()` → 409 if busy.
- `async with generation_lock:` around generation logic.

**Alternatives considered**:
- Database-level locking (MongoDB status flag): Correct for multi-server but adds complexity for single-server MVP.
- `threading.Lock`: Wrong for async — blocks the event loop.
- Redis distributed lock: Adds infrastructure dependency; overkill.
- Background task queue (Celery/ARQ): Adds significant infrastructure; defer to later.

---

## 7. Dependency Update: Motor → pymongo[async]

**Decision**: Use `pymongo[async]` instead of `motor` as the MongoDB driver.

**Rationale**: Motor is deprecated. The `pymongo` package with the `[async]` extra provides `AsyncMongoClient` directly. This is the officially recommended driver going forward.

**Install command**: `pip install "pymongo[async]"`

**Impact**: Constitution principle VII (Explicit Dependency Management) requires documenting this. Updated install commands:

```bash
pip install fastapi "uvicorn[standard]" "pymongo[async]" pydantic pydantic-settings python-dotenv httpx jinja2
```
