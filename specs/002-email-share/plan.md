# Plan 002 — Share Newsletter via Email

> **Spec:** [spec.md](./spec.md) | **Status:** Planned | **Date:** 2026-03-17

---

## Milestones

### M1 · Backend Foundation *(estimated: 1 day)*
- New settings fields for SMTP + rate limiting
- `backend/models/share.py` — request/response Pydantic models
- `backend/services/rate_limiter.py` — in-memory sliding-window
- `backend/services/email_service.py` — async SMTP send

### M2 · API Layer *(estimated: 0.5 day)*
- `backend/routers/share.py` — `POST /api/v1/share/email`
- Register router in `backend/main.py`
- Update `.env.example` with new env vars

### M3 · Frontend — Modal & JS *(estimated: 1 day)*
- `frontend/static/js/email-share.js` — modal, validation, API call, toast
- `frontend/static/css/sections.css` or new `email-share.css` — modal + toast styles
- `frontend/templates/partials/share_button.html` — add email share button
- Load `email-share.js` in `index.html`, `edition.html`, `archive.html`

### M4 · Testing *(estimated: 0.5 day)*
- `tests/test_rate_limiter.py` — unit tests for sliding window logic
- `tests/test_email_service.py` — mock SMTP, verify message construction
- `tests/test_share_router.py` — integration tests (valid request, rate limit, bad input)

### M5 · Hardening & Docs *(estimated: 0.5 day)*
- Verify all new files ≤ 500 lines
- Update `README.md` — add new env vars to the table and new API endpoint
- Verify `.env.example` is complete
- Close all tasks in `tasks.md`

---

## Timeline

| Milestone | Target Date |
|---|---|
| M1 Backend Foundation | 2026-03-18 |
| M2 API Layer | 2026-03-18 |
| M3 Frontend | 2026-03-19 |
| M4 Testing | 2026-03-19 |
| M5 Hardening & Docs | 2026-03-20 |
| **Feature complete** | **2026-03-20** |

---

## Dependencies

| Dependency | Type | Notes |
|---|---|---|
| `aiosmtplib` | New Python package | Async SMTP client; must be added to `requirements.txt` |
| `email-validator` | New Python package | Required by Pydantic `EmailStr`; may already be present |
| Existing `backend/config/settings.py` | Internal | Extend `Settings` class with new SMTP + rate-limit fields |
| Existing `backend/routers/__init__.py` | Internal | Register new share router |
| `frontend/templates/partials/share_button.html` | Internal | Add second button without breaking existing clipboard share |

---

## Resources

- Developer: @tanmayiitj
- Reference: [aiosmtplib docs](https://aiosmtplib.readthedocs.io/)
- Reference: [Python email.message docs](https://docs.python.org/3/library/email.message.html)
- Reference: Existing `backend/services/newsletter_service.py` for DB access pattern
- Reference: Existing `frontend/static/js/share.js` for clipboard share pattern to extend

---

## Constraints

- **No new infrastructure** — must work without Redis, Celery, or any new server component
- **Single-server deployment** — in-memory rate limiter is acceptable
- **Max 5 recipients** — enforced both client-side (UX) and server-side (Pydantic validation)
- **No login required** — endpoint is fully public; rate limiting is the only abuse control
