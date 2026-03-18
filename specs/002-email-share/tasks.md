# Tasks 002 — Share Newsletter via Email (Google Login)

> **Plan:** [plan.md](./plan.md) | **Spec:** [spec.md](./spec.md)

---

## M1 — Backend Auth + Settings

- [X] **T-001** Add Google OAuth + session settings to `backend/config/settings.py`
- [X] **T-002** Add `itsdangerous` to `requirements.txt`
- [X] **T-003** Create `backend/routers/auth.py` (login, callback, logout, me)

## M2 — Backend Email Rework

- [X] **T-004** Rework `backend/models/share.py` — `SendToSelfRequest`
- [X] **T-005** Rework `backend/services/email_service.py` — full newsletter builder
- [X] **T-006** Rework `backend/routers/share.py` — send-to-self with session auth
- [X] **T-007** Update rate limiter to key by user email

## M3 — Frontend

- [X] **T-008** Rewrite `frontend/static/css/email-share.css` — auth + send styles
- [X] **T-009** Replace `frontend/static/js/email-share.js` with `auth.js`
- [X] **T-010** Update `frontend/templates/partials/header.html` — login + profile
- [X] **T-011** Update `frontend/templates/index.html` — send button + scripts
- [X] **T-012** Update `frontend/templates/edition.html` — send button + scripts
- [X] **T-013** Register auth router in `backend/main.py`

## M4 — Testing

- [X] **T-014** Create `tests/test_auth_router.py`
- [X] **T-015** Update `tests/test_share_router.py`
- [X] **T-016** Update `tests/test_email_service.py`

## M5 — Hardening & Docs

- [X] **T-017** Update `.env.example` and `README.md`
- [X] **T-018** Verify all files ≤ 500 lines
- [X] **T-019** Final review — mark all tasks

---

## Task Summary

| ID | Milestone | Status |
|---|---|---|
| T-001 | M1 | ✅ Done |
| T-002 | M1 | ✅ Done |
| T-003 | M1 | ✅ Done |
| T-004 | M2 | ✅ Done |
| T-005 | M2 | ✅ Done |
| T-006 | M2 | ✅ Done |
| T-007 | M2 | ✅ Done |
| T-008 | M3 | ✅ Done |
| T-009 | M3 | ✅ Done |
| T-010 | M3 | ✅ Done |
| T-011 | M3 | ✅ Done |
| T-012 | M3 | ✅ Done |
| T-013 | M3 | ✅ Done |
| T-014 | M4 | ✅ Done |
| T-015 | M4 | ✅ Done |
| T-016 | M4 | ✅ Done |
| T-017 | M5 | ✅ Done |
| T-018 | M5 | ✅ Done |
| T-019 | M5 | ✅ Done |
