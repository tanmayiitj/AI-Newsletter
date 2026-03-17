# Tasks 002 — Share Newsletter via Email

> **Plan:** [plan.md](./plan.md) | **Spec:** [spec.md](./spec.md)

---

## M1 — Backend Foundation

- [ ] **T-001** Add SMTP settings to `backend/config/settings.py`
  - Fields: `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`, `smtp_from_name`, `smtp_from_email`
  - Fields: `rate_limit_max_requests` (default 3), `rate_limit_window_seconds` (default 600)

- [ ] **T-002** Create `backend/models/share.py`
  - `ShareEmailRequest(BaseModel)` — `edition_id: str`, `recipients: list[EmailStr]` (min 1, max 5), `personal_note: Optional[str]` (max 300 chars)
  - `ShareEmailResponse(BaseModel)` — `success: bool`, `message: str`
  - Google-style docstrings on both classes

- [ ] **T-003** Create `backend/services/rate_limiter.py`
  - Sliding-window in-memory implementation keyed by IP string
  - `async def check_rate_limit(ip: str) -> bool`
  - Periodic cleanup of expired timestamps
  - Google-style docstrings on all public functions

- [ ] **T-004** Create `backend/services/email_service.py`
  - `async def send_share_email(recipients, edition_headline, edition_summary, edition_url, personal_note)`
  - Builds `email.message.EmailMessage` with plain-text + HTML alternative parts
  - Sends via `aiosmtplib.send()`
  - Sanitises `personal_note` (strip HTML tags)
  - Raises custom `EmailServiceError` on SMTP failure
  - Google-style docstrings on all public functions

- [ ] **T-005** Add `aiosmtplib` and `email-validator` to `requirements.txt`

---

## M2 — API Layer

- [ ] **T-006** Create `backend/routers/share.py`
  - `POST /api/v1/share/email` router
  - Extract client IP from `Request.client.host`
  - Call `rate_limiter.check_rate_limit(ip)` — return 429 if exceeded
  - Fetch edition from `newsletter_service.get_by_id()`
  - Build `edition_url` as `{request.base_url}edition/{edition_id}`
  - Call `email_service.send_share_email()`
  - Return `ShareEmailResponse`
  - Google-style docstrings on all public functions

- [ ] **T-007** Register `share.router` in `backend/main.py`
  - Add `from backend.routers import share` import
  - Add `app.include_router(share.router)`

- [ ] **T-008** Update `.env.example`
  - Add all 8 new env vars with descriptive comments

- [ ] **T-009** Update `README.md`
  - Add `POST /api/v1/share/email` to API Endpoints table
  - Add 8 new env vars to Environment Variables table

---

## M3 — Frontend

- [ ] **T-010** Create `frontend/static/js/email-share.js`
  - Block comment at file top explaining purpose
  - `openShareModal(editionId)` — inject modal HTML into DOM, focus first input
  - Form validation: RFC 5322 email regex, max 5 comma-separated recipients, max 300 char note
  - `submitShareForm()` — `fetch('POST /api/v1/share/email')`, show loading state
  - `showToast(message, type)` — success (green) / error (red) toast, auto-dismiss 4s
  - `closeShareModal()` — remove modal, restore focus
  - Full keyboard support (Escape closes modal, Tab traps focus inside modal)

- [ ] **T-011** Add email share modal CSS
  - Modal overlay, dialog, form inputs, send button, toast styles
  - All colours via existing CSS custom property tokens (`--color-surface`, `--color-accent`, etc.)
  - Mobile responsive (dialog is full-width on small screens)
  - Can be added to `frontend/static/css/sections.css` if it keeps it under 500 lines, otherwise new `frontend/static/css/email-share.css`

- [ ] **T-012** Update `frontend/templates/partials/share_button.html`
  - Add `📧 Share via Email` button alongside existing clipboard button
  - Button must have `data-edition-id="{{ edition.id }}"` attribute (available via template context)
  - `aria-label="Share this edition via email"`
  - Clicking it calls `openShareModal(editionId)`

- [ ] **T-013** Load `email-share.js` in templates
  - Add `<script src="{{ url_for('static', path='/js/email-share.js') }}"></script>` to `{% block extra_js %}` in `frontend/templates/index.html` and `frontend/templates/edition.html`

---

## M4 — Testing

- [ ] **T-014** Create `tests/test_rate_limiter.py`
  - Test: first N requests within window are allowed
  - Test: request N+1 within window is rejected
  - Test: requests after window expiry are allowed again
  - Test: different IPs have independent counters

- [ ] **T-015** Create `tests/test_email_service.py`
  - Mock `aiosmtplib.send`
  - Test: email built with correct subject, recipients, and body
  - Test: personal note is sanitised (HTML stripped)
  - Test: `EmailServiceError` raised on SMTP failure

- [ ] **T-016** Create `tests/test_share_router.py`
  - Test: valid request → 200 + `success: true`
  - Test: invalid email format → 422
  - Test: more than 5 recipients → 422
  - Test: rate limit exceeded → 429
  - Test: edition not found → 404
  - Test: SMTP failure → 502

---

## M5 — Hardening & Docs

- [ ] **T-017** Verify all new/modified files are ≤ 500 lines
  - `backend/services/email_service.py`
  - `backend/services/rate_limiter.py`
  - `backend/routers/share.py`
  - `frontend/static/js/email-share.js`
  - Any modified CSS file

- [ ] **T-018** Final spec-kit review
  - All tasks above ticked
  - Spec, plan, tasks files are consistent with implementation
  - `.specify/memory/constitution.md` reflects any new decisions made during implementation

---

## Task Summary

| ID | Milestone | Status |
|---|---|---|
| T-001 | M1 | ⬜ Todo |
| T-002 | M1 | ⬜ Todo |
| T-003 | M1 | ⬜ Todo |
| T-004 | M1 | ⬜ Todo |
| T-005 | M1 | ⬜ Todo |
| T-006 | M2 | ⬜ Todo |
| T-007 | M2 | ⬜ Todo |
| T-008 | M2 | ⬜ Todo |
| T-009 | M2 | ⬜ Todo |
| T-010 | M3 | ⬜ Todo |
| T-011 | M3 | ⬜ Todo |
| T-012 | M3 | ⬜ Todo |
| T-013 | M3 | ⬜ Todo |
| T-014 | M4 | ⬜ Todo |
| T-015 | M4 | ⬜ Todo |
| T-016 | M4 | ⬜ Todo |
| T-017 | M5 | ⬜ Todo |
| T-018 | M5 | ⬜ Todo |
