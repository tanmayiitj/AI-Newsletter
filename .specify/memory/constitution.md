<!--
  Sync Impact Report
  - Version change: N/A → 1.0.0
  - Modified principles: None (initial creation)
  - Added sections:
    - 9 Core Principles (I–IX)
    - Technology Constraints
    - Development Workflow
    - Governance
  - Removed sections: None
  - Templates requiring updates:
    - ✅ plan-template.md — "Constitution Check" uses generic gate;
         no update needed
    - ✅ spec-template.md — generic placeholders; no update needed
    - ✅ tasks-template.md — generic phase structure; no update needed
    - ✅ No commands/ directory exists; nothing to update
  - Follow-up TODOs: None
-->

# AI Pulse Newsletter Constitution

## Core Principles

### I. File Size Discipline (NON-NEGOTIABLE)

No single source file MUST exceed 500 lines of code. If a module
approaches this limit, it MUST be refactored into smaller, focused
sub-modules before merge. This applies to Python files, HTML
templates, CSS stylesheets, and JavaScript files equally.

### II. Documentation-In-Code

Every public function, class, and module MUST contain extensive
in-line docstrings explaining purpose, parameters, return values,
and side effects. Docstrings follow Google-style format for Python.
HTML/CSS/JS files MUST contain block comments at the top explaining
the file's role in the system.

### III. Explicit Consent for Changes

Before making arbitrary, large, or architectural changes, the
developer (or AI agent) MUST ask for explicit consent from the
project owner. No sweeping refactors, dependency additions, or
structural changes without documented approval.

### IV. Root Markdown Restriction

Only two markdown files are permitted in the project root directory:
`README.md` and `AGENTS.md`. All other documentation MUST reside in
`docs/`, `specs/`, or `.specify/` directories.

### V. Modular Architecture (NON-NEGOTIABLE)

The codebase MUST maintain strict separation of concerns:

- **API Routers**: FastAPI endpoint definitions only — no business
  logic.
- **Database Models**: Pydantic schemas and MongoDB document models
  only.
- **Service Logic**: All LLM/API interactions, content aggregation,
  and business rules.
- **Configuration**: Centralized config loading, environment
  management.

No layer may directly depend on another layer's internals;
communication happens through well-defined interfaces.

### VI. Security-First Credential Management (NON-NEGOTIABLE)

Database credentials, API keys, and secrets MUST never be hardcoded.
All sensitive values MUST be loaded from a `.env` file via
`python-dotenv`. The `.env` file MUST be listed in `.gitignore`.
A `.env.example` file MUST be provided with placeholder values.

### VII. Explicit Dependency Management

Developers MUST provide exact terminal commands (e.g.,
`pip install fastapi uvicorn`) for all dependencies. No silent
creation of `requirements.txt` with hallucinated versions.
A `requirements.txt` is maintained manually with pinned versions
only after explicit installation and verification.

### VIII. Simplicity & YAGNI

Start with the simplest implementation that fulfils the
specification. Do not add abstractions, patterns, or features
"just in case." Every piece of complexity MUST be justified by a
concrete, current requirement.

### IX. Performance-Conscious Frontend

The frontend uses vanilla HTML, CSS, and JavaScript for maximum
performance. No frontend frameworks unless explicitly approved.
Assets MUST be optimized (minified CSS/JS in production, compressed
images). Page load target: < 2 seconds on 3G connection.

## Technology Constraints

- **Backend Language**: Python 3.11+
- **Web Framework**: FastAPI
- **Database**: MongoDB (via Motor async driver)
- **LLM Integration**: OpenAI API (or compatible) for content
  generation
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Templating**: Jinja2 (served via FastAPI)
- **Environment Management**: python-dotenv
- **ASGI Server**: Uvicorn

## Development Workflow

- All features follow spec-driven development:
  Specify → Plan → Tasks → Implement.
- Every PR MUST pass linting (`ruff`), type checks (`mypy`), and
  existing tests before merge.
- Commit messages follow Conventional Commits format.
- Code reviews MUST verify constitution compliance.

## Governance

This constitution supersedes all other development practices for the
AI Pulse Newsletter project. Amendments require:

1. A written proposal documenting the change and rationale.
2. Explicit approval from the project owner.
3. Version bump of this document.
4. Propagation to all dependent templates and agent files.

**Version**: 1.0.0 | **Ratified**: 2026-03-03 | **Last Amended**: 2026-03-03
