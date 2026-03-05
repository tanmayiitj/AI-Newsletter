# Tasks: AI Pulse Newsletter

**Input**: Design documents from `specs/001-ai-pulse-newsletter/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested — test tasks omitted per template rules.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/` for Python, `frontend/` for templates & static assets
- **Tests**: `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project scaffolding and environment configuration

- [x] T001 Create project directory structure with all folders and __init__.py files per plan.md
- [x] T002 [P] Create .env.example with placeholder values for MONGODB_URI, MONGODB_DB_NAME, OPENAI_API_KEY, OPENAI_MODEL, ADMIN_API_KEY, APP_ENV, APP_PORT in .env.example
- [x] T003 [P] Create .gitignore with Python, .venv, .env, __pycache__, IDE, and OS exclusions in .gitignore

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement Settings class with Pydantic BaseSettings loading all env vars from .env in backend/config/settings.py
- [x] T005 [P] Create JobListing model with LocationType and ExperienceTier enums in backend/models/job.py
- [x] T006 Create ContentItem, NewsletterSection, NewsletterEdition models with SectionType, EditionStatus enums and PyObjectId type in backend/models/newsletter.py
- [x] T007 Implement AsyncMongoClient database connection with FastAPI lifespan context manager in backend/database/connection.py
- [x] T008 Implement newsletter_service with create_edition, get_latest, get_by_id, and list_paginated CRUD operations in backend/services/newsletter_service.py
- [x] T009 [P] Implement health check endpoint (GET /api/v1/health) with DB ping in backend/routers/health.py
- [x] T010 [P] Create newsletter API router skeleton with empty APIRouter in backend/routers/newsletter.py
- [x] T011 [P] Create pages router skeleton with empty APIRouter in backend/routers/pages.py
- [x] T012 Create FastAPI app entrypoint with DB lifespan, router includes, StaticFiles mount, and Jinja2Templates setup in backend/main.py
- [x] T013 [P] Create base.html Jinja2 layout shell with meta tags, CSS includes, JS includes, and content blocks in frontend/templates/base.html
- [x] T014 [P] Create header.html navigation partial and footer.html partial in frontend/templates/partials/header.html and frontend/templates/partials/footer.html
- [x] T015 [P] Create CSS foundation files (reset.css, layout.css, typography.css) in frontend/static/css/

**Checkpoint**: Foundation ready — all models, DB, services, app entrypoint, and base templates in place. User story implementation can now begin.

---

## Phase 3: User Story 1 — Corporate Reader Browses Latest Newsletter (Priority: P1) 🎯 MVP

**Goal**: Display the latest newsletter edition on the homepage in a beautiful, story-driven layout with all content sections rendered in narrative order.

**Independent Test**: Navigate to `/` and verify a complete newsletter renders with all sections in order, styled with the story-flow layout, readable on desktop and mobile. If no editions exist, display the empty-state page.

### Implementation for User Story 1

- [x] T016 [P] [US1] Create section_trending.html, section_developments.html, section_tools.html, and section_future.html partial templates in frontend/templates/partials/
- [x] T017 [P] [US1] Create basic section_jobs.html partial with simple job listing rendering in frontend/templates/partials/section_jobs.html
- [x] T018 [P] [US1] Create sections.css with section-specific styles and story-flow visual transitions in frontend/static/css/sections.css
- [x] T019 [P] [US1] Create responsive.css with mobile (320px), tablet (768px), and desktop (1280px+) media queries in frontend/static/css/responsive.css
- [x] T020 [US1] Create index.html homepage template extending base.html with executive summary and all section partial includes in frontend/templates/index.html
- [x] T021 [US1] Create empty.html empty-state template with friendly message for first-time visitors in frontend/templates/empty.html
- [x] T022 [P] [US1] Implement GET /api/v1/newsletter/latest endpoint returning latest published edition in backend/routers/newsletter.py
- [x] T023 [US1] Implement homepage page route (GET /) calling newsletter_service.get_latest and rendering index.html or empty.html in backend/routers/pages.py

**Checkpoint**: Homepage displays the latest newsletter edition with all sections in story-flow layout. Empty state shown when no editions exist. Responsive on mobile/tablet/desktop.

---

## Phase 4: User Story 2 — Admin Triggers Newsletter Generation (Priority: P2)

**Goal**: Enable admin-triggered generation of complete newsletter editions via LLM, with content stored in MongoDB and immediately available for viewing.

**Independent Test**: Call `POST /api/v1/newsletter/generate` with valid API key and verify a complete edition is created in MongoDB with all 5 sections populated. Verify 409 on concurrent requests, 401 on missing/invalid key, 502 on LLM failure.

### Implementation for User Story 2

- [x] T024 [US2] Implement LLM client service with httpx, OpenAI-compatible API calls, and Pydantic structured output parsing in backend/services/llm_client.py
- [x] T025 [US2] Implement content generator service orchestrating section-by-section LLM generation with per-section validation and placeholder fallback in backend/services/content_generator.py
- [x] T026 [US2] Implement jobs service for job listing generation with experience tier (1-2yr, 2-4yr) segmentation in backend/services/jobs_service.py
- [x] T027 [US2] Implement API key auth dependency using APIKeyHeader and secrets.compare_digest in backend/routers/newsletter.py
- [x] T028 [US2] Implement POST /api/v1/newsletter/generate endpoint with asyncio.Lock concurrency guard and error handling in backend/routers/newsletter.py
- [x] T029 [US2] Add structured logging for generation pipeline (start/end timestamps, per-section success/failure, LLM call durations) in backend/services/content_generator.py

**Checkpoint**: Admin can trigger newsletter generation via API. Full edition created with 5 sections. Concurrent requests rejected (409). Invalid keys rejected (401). LLM failures handled gracefully (502). Generation events logged.

---

## Phase 5: User Story 3 — Reader Browses Newsletter Archive (Priority: P3)

**Goal**: Provide a paginated archive page listing past editions. Clicking an edition loads its full content in the story-flow layout.

**Independent Test**: Navigate to `/archive`, verify editions listed newest-first paginated at 10 per page. Click an edition, verify it renders fully at `/edition/{id}`.

### Implementation for User Story 3

- [x] T030 [P] [US3] Create archive.html template with paginated edition list (date, headline, summary) and pagination controls in frontend/templates/archive.html
- [x] T031 [P] [US3] Create edition.html single-edition full-view template reusing section partials in frontend/templates/edition.html
- [x] T032 [P] [US3] Create archive.js for pagination link interactions in frontend/static/js/archive.js
- [x] T033 [US3] Implement GET /api/v1/newsletter/archive endpoint with page/per_page pagination in backend/routers/newsletter.py
- [x] T034 [US3] Implement GET /api/v1/newsletter/{edition_id} endpoint in backend/routers/newsletter.py
- [x] T035 [US3] Implement archive page route (GET /archive) and edition page route (GET /edition/{edition_id}) in backend/routers/pages.py

**Checkpoint**: Archive page displays past editions paginated at 10/page. Individual editions render in full story-flow layout. API endpoints return correct JSON for archive and single editions.

---

## Phase 6: User Story 4 — Reader Explores the AI Jobs Board (Priority: P4)

**Goal**: Enhance the jobs section to display listings segmented by experience tier (1-2 years / 2-4 years) with full metadata (role, company, location, description, apply link).

**Independent Test**: View the jobs section of any edition and verify listings appear under two labeled tier headers with complete metadata and working apply links.

### Implementation for User Story 4

- [x] T036 [US4] Enhance section_jobs.html with experience tier segmentation headers ("1-2 Years Experience" / "2-4 Years Experience") and full metadata display (role title, company, location type, description, apply URL) in frontend/templates/partials/section_jobs.html
- [x] T037 [US4] Add jobs-board CSS styles for tier headers, job listing cards, location badges, and apply link buttons in frontend/static/css/sections.css

**Checkpoint**: Jobs section renders with two clearly labeled experience tiers. Each listing shows all metadata fields. Empty tiers display placeholder message.

---

## Phase 7: User Story 5 — Reader Shares a Newsletter Section (Priority: P5)

**Goal**: Enable readers to share specific newsletter sections via anchor deep-links with copy-to-clipboard functionality and smooth scrolling.

**Independent Test**: Click the share button on any section, verify the anchor URL is copied to clipboard. Navigate to a section anchor URL directly, verify the page scrolls to that section.

### Implementation for User Story 5

- [x] T038 [P] [US5] Add unique anchor IDs to all section partial templates for deep-linking in frontend/templates/partials/section_*.html
- [x] T039 [P] [US5] Create share_button.html partial with copy-link button UI in frontend/templates/partials/share_button.html
- [x] T040 [P] [US5] Implement share.js with Clipboard API for URL copy and visual feedback in frontend/static/js/share.js
- [x] T041 [US5] Implement smooth-scroll.js for smooth anchor-based navigation on page load and click in frontend/static/js/smooth-scroll.js
- [x] T042 [US5] Integrate share buttons into all section partials and update index.html/edition.html to include share functionality in frontend/templates/

**Checkpoint**: Every section has a unique anchor ID. Share button copies section URL to clipboard. Direct anchor URLs scroll to the correct section.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and end-to-end validation

- [x] T043 [P] Create README.md with project overview, architecture summary, and setup instructions in README.md
- [x] T044 [P] Create AGENTS.md with AI agent development guidelines and constitution reference in AGENTS.md
- [x] T045 Run quickstart.md end-to-end validation: install deps, start server, generate edition, verify all pages and acceptance scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — **BLOCKS all user stories**
- **User Story 1 (Phase 3)**: Depends on Foundational — can start immediately after Phase 2
- **User Story 2 (Phase 4)**: Depends on Foundational — can start in parallel with US1
- **User Story 3 (Phase 5)**: Depends on Foundational — can start in parallel with US1/US2
- **User Story 4 (Phase 6)**: Depends on US1 (section_jobs.html exists from T017)
- **User Story 5 (Phase 7)**: Depends on US1 (section partials exist from T016/T017)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 2 — independent of US1 (backend-only)
- **User Story 3 (P3)**: Can start after Phase 2 — reuses section partials from US1 in edition.html but can create its own initially
- **User Story 4 (P4)**: Depends on US1 (enhances section_jobs.html created in T017)
- **User Story 5 (P5)**: Depends on US1 (adds anchor IDs/share buttons to partials from T016/T017)

### Within Each User Story

- Templates/CSS before page routes (frontend assets must exist before rendering)
- Services before endpoints (business logic before API layer)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- Setup: T002 and T003 can run in parallel
- Foundational: T005, T009, T010, T011, T013, T014, T015 can all run in parallel (different files)
- US1: T016, T017, T018, T019 can run in parallel (different files); T022 parallel with T023
- US2: T024 → T025/T026 → T027 → T028 (mostly sequential — same-layer dependencies)
- US3: T030, T031, T032 can run in parallel (frontend); T033/T034 then T035 (backend sequential)
- US4: T036 → T037 (sequential — CSS follows template changes)
- US5: T038, T039, T040 can run in parallel; then T041 → T042
- US1, US2, US3 can proceed in parallel after Foundational phase

---

## Parallel Example: User Story 1

```bash
# Launch all frontend assets in parallel:
Task T016: "Create section partial templates in frontend/templates/partials/"
Task T017: "Create basic section_jobs.html partial in frontend/templates/partials/"
Task T018: "Create sections.css in frontend/static/css/sections.css"
Task T019: "Create responsive.css in frontend/static/css/responsive.css"

# Then build page templates (depend on partials):
Task T020: "Create index.html in frontend/templates/index.html"
Task T021: "Create empty.html in frontend/templates/empty.html"

# Then implement routes (depend on templates + services):
Task T022: "Implement GET /api/v1/newsletter/latest in backend/routers/newsletter.py"  # parallel
Task T023: "Implement homepage page route (GET /) in backend/routers/pages.py"         # parallel
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (**CRITICAL** — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Navigate to `/`, verify newsletter renders with story-flow layout
5. Deploy/demo if ready — this is a viable MVP

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Homepage works → **Deploy/Demo (MVP!)**
3. Add User Story 2 → Content generation works → Deploy/Demo
4. Add User Story 3 → Archive browsing works → Deploy/Demo
5. Add User Story 4 → Jobs tiers enhanced → Deploy/Demo
6. Add User Story 5 → Section sharing works → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers after Foundational is complete:

- **Developer A**: User Story 1 (frontend: templates, CSS, page routes)
- **Developer B**: User Story 2 (backend: LLM client, generator, API endpoint)
- **Developer C**: User Story 3 (both: archive templates + API endpoints)
- Stories 4 & 5 wait for Story 1 completion (they enhance US1 partials)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks within the same phase
- [Story] label maps each task to a specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- No file exceeds 500 lines (Constitution Principle I)
- All Python functions include Google-style docstrings (Constitution Principle II)
- All HTML/CSS/JS files include block comments at top explaining purpose (Constitution Principle II)
