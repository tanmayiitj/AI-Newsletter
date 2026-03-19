# Plan 002 — Share Newsletter via Email (Google Login)

> **Spec:** [spec.md](./spec.md) | **Status:** Revised | **Date:** 2026-03-18

---

## Milestones

### M1 · Backend Auth + Settings
- Google OAuth settings in `backend/config/settings.py`
- `backend/routers/auth.py` — login, callback, logout, me endpoints
- Session cookie with `itsdangerous` signed cookies

### M2 · Backend Email Rework
- Rework `backend/models/share.py` — `SendToSelfRequest`
- Rework `backend/services/email_service.py` — full newsletter email builder
- Rework `backend/routers/share.py` — `POST /api/v1/share/send-to-self`
- Rate limiter keyed by user email instead of IP

### M3 · Frontend
- `frontend/static/js/auth.js` — login state, profile dropdown, send-to-self
- `frontend/static/css/email-share.css` — avatar, dropdown, send button, toast
- Update `header.html` — login button + profile picture placeholder
- Update `index.html`, `edition.html` — send-to-self button + script tags

### M4 · Testing
- `tests/test_auth_router.py` — OAuth flow, session, logout
- Update `tests/test_share_router.py` — send-to-self scenarios
- Update `tests/test_email_service.py` — full newsletter email

### M5 · Hardening & Docs
- Update `.env.example`, `README.md`
- Verify all files ≤ 500 lines
- Clean up old email-share.js (replace contents)

---

## Dependencies

| Dependency | Type | Notes |
|---|---|---|
| `httpx` | Existing | Used for Google token exchange + userinfo fetch |
| `itsdangerous` | New package | Signed session cookies (no external session store) |
| `aiosmtplib` | Existing | Async SMTP sending |
| Google OAuth credentials | External | Client ID + secret from Google Cloud Console |

---

## Constraints

- **No user database** — identity lives only in the signed session cookie
- **No new infrastructure** — no Redis, no Celery
- **Single-server deployment** — in-memory rate limiter is acceptable
- **Send to self only** — no multi-recipient flow
