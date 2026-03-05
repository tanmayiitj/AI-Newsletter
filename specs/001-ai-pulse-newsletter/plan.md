# Implementation Plan: AI Pulse Newsletter

**Branch**: `001-ai-pulse-newsletter` | **Date**: 2026-03-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-ai-pulse-newsletter/spec.md`

---

## Summary

Build an AI-powered newsletter web application that curates and presents the latest AI industry content in a beautiful, story-driven layout. The backend (Python/FastAPI) handles content generation via LLM APIs and stores editions in MongoDB. The frontend (HTML/CSS/JS via Jinja2) renders newsletters in a flowing, magazine-style reading experience. Target audience: corporate employees seeking AI industry updates, tools, and career opportunities.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, pymongo[async] (AsyncMongoClient), Pydantic v2, Jinja2, python-dotenv, httpx (for LLM API calls)
**Storage**: MongoDB (via pymongo AsyncMongoClient)
**Testing**: pytest + pytest-asyncio
**Target Platform**: Linux/macOS/Windows server, modern web browsers
**Project Type**: Web application (backend API + server-rendered frontend)
**Performance Goals**: < 2s page load, 50 concurrent readers
**Constraints**: No file > 500 lines, vanilla HTML/CSS/JS only, all credentials via `.env`
**Scale/Scope**: Single-server deployment, ~5 page types, ~6 content sections per edition

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | File Size Discipline (NON-NEG) | ✅ PASS | Architecture splits logic across many small modules; line estimates all < 200 |
| II | Documentation-In-Code | ✅ PASS | Google-style docstrings mandated in all Python; block comments in HTML/CSS/JS |
| III | Explicit Consent for Changes | ✅ PASS | This plan documents all architectural decisions for owner approval |
| IV | Root Markdown Restriction | ✅ PASS | Only README.md and AGENTS.md at project root |
| V | Modular Architecture (NON-NEG) | ✅ PASS | Strict 4-layer separation: routers / models / services / config |
| VI | Security-First Credentials (NON-NEG) | ✅ PASS | `.env` + python-dotenv; `.env.example` provided; `.gitignore` covers `.env` |
| VII | Explicit Dependency Management | ✅ PASS | All `pip install` commands documented; no auto-generated requirements.txt |
| VIII | Simplicity & YAGNI | ✅ PASS | No frameworks beyond FastAPI; vanilla frontend; no unnecessary abstractions |
| IX | Performance-Conscious Frontend | ✅ PASS | No frontend frameworks; vanilla HTML/CSS/JS; < 2s page load target |

**GATE RESULT**: ✅ ALL PASS — proceeding to Phase 0.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-pulse-newsletter/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── newsletter.md
│   └── health.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── main.py                      # FastAPI app entrypoint & ASGI config
├── config/
│   ├── __init__.py
│   └── settings.py              # Pydantic Settings, loads .env
│
├── models/
│   ├── __init__.py
│   ├── newsletter.py            # Edition, Section, ContentItem models
│   └── job.py                   # JobListing model
│
├── services/
│   ├── __init__.py
│   ├── llm_client.py            # LLM API interaction (OpenAI-compatible)
│   ├── content_generator.py     # Orchestrates section-by-section generation
│   ├── newsletter_service.py    # MongoDB CRUD for editions
│   └── jobs_service.py          # Job listing generation & tier parsing
│
├── routers/
│   ├── __init__.py
│   ├── newsletter.py            # REST API endpoints (generate, get, list)
│   ├── pages.py                 # Jinja2 HTML page routes
│   └── health.py                # Health check endpoint
│
└── database/
    ├── __init__.py
    └── connection.py            # AsyncMongoClient setup & lifespan

frontend/
├── templates/
│   ├── base.html                # Base Jinja2 layout shell
│   ├── index.html               # Homepage — latest newsletter
│   ├── archive.html             # Archive listing page (paginated)
│   ├── edition.html             # Single edition full view
│   ├── empty.html               # Empty state (no editions)
│   └── partials/
│       ├── header.html          # Site header/nav
│       ├── footer.html          # Site footer
│       ├── section_trending.html
│       ├── section_developments.html
│       ├── section_tools.html
│       ├── section_future.html
│       ├── section_jobs.html
│       └── share_button.html    # Copy-link share widget
│
└── static/
    ├── css/
    │   ├── reset.css            # CSS reset
    │   ├── layout.css           # Grid & story-flow layout
    │   ├── typography.css       # Fonts, headings, body text
    │   ├── sections.css         # Section-specific styles
    │   └── responsive.css       # Media queries (mobile/tablet/desktop)
    │
    ├── js/
    │   ├── share.js             # Copy-to-clipboard & share
    │   ├── smooth-scroll.js     # Smooth anchor scrolling
    │   └── archive.js           # Archive pagination interactions
    │
    └── images/
        └── logo.svg             # Site logo

tests/
├── conftest.py                  # Shared fixtures (mock DB, mock LLM)
├── test_models.py               # Pydantic model validation tests
├── test_services.py             # Service logic unit tests
├── test_routers.py              # API endpoint integration tests
└── test_content_generator.py    # Content generation tests

.env.example                     # Environment variable template
.gitignore
README.md
AGENTS.md
```

**Structure Decision**: Web application layout (backend + frontend + tests at root) selected. The backend follows the constitution's 4-layer architecture (config → models → services → routers). The frontend uses Jinja2 templates served by FastAPI with static CSS/JS assets. Tests are co-located at root under `tests/`.

---

## Complexity Tracking

> No constitution violations detected. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
