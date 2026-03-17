# Spec 002 — Share Newsletter via Email

> **Status:** Draft | **Author:** @tanmayiitj | **Date:** 2026-03-17

---

## Overview

Allow any public visitor on the AI Pulse Newsletter site to share a newsletter edition (or a specific section anchor) with someone else by providing a recipient email address. The system sends an email containing a short description and a direct link. No login, no account creation, no subscription — purely ephemeral public sharing.

---

## Motivation

The existing `share.js` copies a section URL to the clipboard. This is useful for sharing on chat apps, but many users want to send a link directly to a specific person via email without leaving the page. Adding an email share flow lowers the friction for distributing individual editions to colleagues or friends.

---

## Goals

- **G1** — Any visitor can open a "Share via Email" dialog from any newsletter edition page or edition card in the archive.
- **G2** — The visitor enters one or more recipient email addresses and an optional personal note.
- **G3** — The backend sends a transactional email containing the edition headline, a 1-sentence summary, the optional note, and a direct link to the edition.
- **G4** — Rate limiting prevents abuse: maximum **3 share emails per IP per 10 minutes**.
- **G5** — No user login or authentication required to use this feature.
- **G6** — The share dialog is accessible (keyboard navigable, screen-reader friendly).
- **G7** — The feature works across all three existing themes (Light, Dark, Warm).

---

## Non-Goals

- **NG1** — No email subscription management (no opt-in lists, no unsubscribe flows).
- **NG2** — No tracking pixels or open-rate analytics.
- **NG3** — No SMS or social-media sharing in this spec.
- **NG4** — No login / user account system introduced.
- **NG5** — No batch/bulk email sending (each share sends to at most 5 recipients).
- **NG6** — No email template rendering (plain-text + minimal HTML email only).

---

## User Flow

```
Visitor on edition page
  └─► Clicks "📧 Share via Email" button
        └─► Modal dialog opens
              ├─ Input: recipient email(s) — comma-separated, max 5
              ├─ Input: optional personal note (max 300 chars)
              └─ Clicks "Send"
                    ├─ [Frontend] validates email format client-side
                    ├─ [Frontend] POST /api/v1/share/email
                    └─ [Backend]
                          ├─ Validates inputs (Pydantic)
                          ├─ Checks rate limit (IP-based, 3/10min)
                          ├─ Fetches edition headline + summary from DB
                          ├─ Sends email via SMTP
                          └─ Returns 200 OK / error
                                └─ [Frontend] shows success or error toast
```

---

## Detailed Design

### Backend

#### New service: `backend/services/email_service.py`
Responsibilities:
- Build the email body (plain-text + HTML multipart).
- Send via `aiosmtplib` (async SMTP).
- Accept: `recipients: list[str]`, `edition_headline: str`, `edition_summary: str`, `edition_url: str`, `personal_note: str | None`.

#### New service: `backend/services/rate_limiter.py`
Responsibilities:
- In-memory sliding-window rate limiter keyed by client IP.
- Configuration: `RATE_LIMIT_MAX_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS` from settings.
- Expose `async def check_rate_limit(ip: str) -> bool` — returns `True` if allowed, `False` if exceeded.
- Periodic cleanup of expired entries to prevent memory growth.

#### New model: `backend/models/share.py`
```python
class ShareEmailRequest(BaseModel):
    edition_id: str
    recipients: list[EmailStr]  # min 1, max 5
    personal_note: Optional[str] = Field(default=None, max_length=300)

class ShareEmailResponse(BaseModel):
    success: bool
    message: str
```

#### New router: `backend/routers/share.py`
```
POST /api/v1/share/email
  Body: ShareEmailRequest
  Response: ShareEmailResponse
  Auth: None (public endpoint)
  Rate limit: 3 requests per IP per 10 minutes
```

#### Settings additions (`backend/config/settings.py`)
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-smtp-user@gmail.com
SMTP_PASSWORD=your-smtp-app-password
SMTP_FROM_NAME=AI Pulse Newsletter
SMTP_FROM_EMAIL=your-smtp-user@gmail.com
RATE_LIMIT_MAX_REQUESTS=3
RATE_LIMIT_WINDOW_SECONDS=600
```

### Frontend

#### New JS module: `frontend/static/js/email-share.js`
- Renders the share modal (dynamically injected into DOM).
- Handles form validation (RFC 5322 email regex, max 5 recipients).
- Calls `POST /api/v1/share/email`.
- Shows success/error toast notification.
- Respects current theme via CSS custom properties.

#### Template change: `frontend/templates/partials/share_button.html`
- Add a second button: `📧 Share via Email` alongside the existing clipboard share button.

#### New CSS: included in `frontend/static/css/sections.css` or a new `email-share.css`
- Modal overlay, dialog box, form inputs, toast — all using existing CSS custom property tokens for theme compatibility.

---

## Email Template

### Subject
```
[AI Pulse] {edition_headline}
```

### Plain-text body
```
Someone shared an AI Pulse Newsletter edition with you.

"{edition_headline}"
{edition_summary}

{personal_note if present}

Read the full edition here:
{edition_url}

---
AI Pulse Newsletter · You received this because someone shared it with you.
```

### HTML body
Minimal inline-styled HTML. No images. Uses the edition headline as an `<h2>`, summary as a `<p>`, optional note in a `<blockquote>`, and a prominent CTA link button.

---

## Error Handling

| Scenario | HTTP Status | User message |
|---|---|---|
| Invalid email format | 422 | "Please enter a valid email address." |
| More than 5 recipients | 422 | "You can share with up to 5 people at once." |
| Rate limit exceeded | 429 | "You've shared too many times recently. Try again in a few minutes." |
| SMTP failure | 502 | "Email could not be sent. Please try again later." |
| Edition not found | 404 | "This edition no longer exists." |

---

## Security Considerations

- **Input sanitisation** — Pydantic `EmailStr` validates all recipient addresses server-side.
- **Rate limiting** — IP-based sliding window prevents bulk sending.
- **No header injection** — Use `email.message.EmailMessage` (stdlib) with explicit field setters, never string interpolation into headers.
- **Personal note sanitisation** — Strip HTML tags from `personal_note` before embedding in email body.
- **SMTP credentials** — Loaded exclusively from `.env` via `Settings`. Never logged.

---

## Alternatives Considered

| Option | Rejected because |
|---|---|
| Third-party email SDK (SendGrid, Mailgun) | Adds paid external dependency; stdlib SMTP + aiosmtplib is sufficient |
| Server-side rendered share page | Overkill; a modal is simpler and keeps the user on the edition |
| `mailto:` link | Opens native mail client — not all users have one configured; no control over email format |
| Redis-backed rate limiting | Adds infrastructure dependency; in-memory is fine for single-server deployment |

---

## Risks and Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| SMTP credentials leaked | Low | Stored only in `.env`, excluded from git via `.gitignore` |
| Spam / abuse via share endpoint | Medium | IP rate limit + max 5 recipients per request |
| Email deliverability (spam folder) | Medium | Proper From header, SPF/DKIM on sending domain (ops concern) |
| Memory leak in rate limiter | Low | Periodic cleanup of expired entries on each check |
