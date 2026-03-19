# Spec 002 — Share Newsletter via Email (Google Login)

> **Status:** Revised | **Author:** @tanmayiitj | **Date:** 2026-03-18

---

## Overview

Allow any visitor to log in with their Google account and send the full newsletter edition to their own email with one click. The header shows a "Login with Google" button; after login it shows the user's circular profile picture with a logout dropdown. A "Send to My Email" button appears in the edition header so the user can receive the newsletter in their inbox.

---

## Motivation

Users want a personal copy of the newsletter in their inbox to read later or search for in Gmail. Google OAuth is the natural auth mechanism since the newsletter is sent via Gmail SMTP and every target user already has a Google account. A single "send to self" flow is simpler and more useful than multi-recipient sharing.

---

## Goals

- **G1** — Visitor can sign in with Google via OAuth 2.0 (one-click login button in site header).
- **G2** — After login, the header shows the user's circular Google profile picture; clicking it reveals a dropdown with email and logout option.
- **G3** — A "📧 Send to My Email" button in the edition header sends the full newsletter to the logged-in user's Google email.
- **G4** — The email contains the full newsletter: headline, summary, every section with its items.
- **G5** — Rate limiting prevents abuse: max 3 send-to-self emails per user per 10 minutes.
- **G6** — Session persists until the user logs out or the session expires (24 hours).
- **G7** — Works across all three themes (Light, Dark, Warm).
- **G8** — Per-section clipboard share buttons are preserved as-is.

---

## Non-Goals

- **NG1** — No multi-recipient sharing (user can only send to themselves).
- **NG2** — No email subscription management or mailing lists.
- **NG3** — No tracking pixels or open-rate analytics.
- **NG4** — No profile page or user database — session-only identity.
- **NG5** — No SMS or social-media sharing in this spec.

---

## User Flow

```
Visitor arrives at site
  └─► Sees "Login with Google" button in header
        └─► Clicks → redirected to Google consent screen
              └─► Grants access → redirected back with auth code
                    └─► Backend exchanges code for tokens
                          └─► Session cookie set (httponly, 24h)
                          └─► Header now shows circular profile pic + name

Logged-in user on edition page
  └─► Sees "📧 Send to My Email" button below edition headline
        └─► Clicks "Send"
              ├─ [Frontend] POST /api/v1/share/send-to-self (cookie auth)
              └─ [Backend]
                    ├─ Validates session
                    ├─ Checks rate limit (user email, 3/10min)
                    ├─ Fetches full edition from DB
                    ├─ Builds rich email with all sections
                    ├─ Sends via Gmail API (user's access token)
                    └─ Returns 200 OK / error
                          └─ [Frontend] shows success or error toast

Profile picture dropdown
  └─► Click profile pic
        └─► Dropdown: user email + "Logout" button
              └─► Logout → clears session cookie → header reverts to login button
```

---

## Detailed Design

### Backend

#### New settings (`backend/config/settings.py`)
- `google_client_id` — Google OAuth client ID
- `google_client_secret` — Google OAuth client secret
- `google_redirect_uri` — OAuth callback URL
- `session_secret_key` — Secret for signing session cookies
- `session_max_age` — Session TTL in seconds (default 86400 = 24h)

#### New router: `backend/routers/auth.py`
- `GET /auth/login` — Redirects to Google OAuth consent URL
- `GET /auth/callback` — Exchanges code for tokens, fetches user info, sets session cookie
- `POST /auth/logout` — Clears session cookie
- `GET /auth/me` — Returns current user info or 401

#### Updated router: `backend/routers/share.py`
- `POST /api/v1/share/send-to-self` — Requires valid session
- Remove old multi-recipient endpoint

#### Updated service: `backend/services/email_service.py`
- `send_newsletter_email(recipient, edition, edition_url, access_token)` — sends via Gmail API
- Uses user's own OAuth access token — no SMTP config needed

#### Updated model: `backend/models/share.py`
- `SendToSelfRequest(BaseModel)` — `edition_id: str`
- Keep `ShareEmailResponse`

### Frontend

#### Header (`frontend/templates/partials/header.html`)
- "Login with Google" button (hidden when logged in)
- Circular profile picture + dropdown (hidden when logged out)

#### JS: `frontend/static/js/auth.js`
- On page load: `GET /auth/me` to check login state
- Toggle login/profile UI, handle logout, handle send-to-self

#### CSS: `frontend/static/css/auth.css`
- Profile avatar, dropdown, send button, toast styles

---

## Error Handling

| Scenario | HTTP Status | User message |
|---|---|---|
| Not logged in | 401 | "Please log in with Google first." |
| Rate limit exceeded | 429 | "Too many emails recently. Try again in a few minutes." |
| Edition not found | 404 | "This edition no longer exists." |
| SMTP failure | 502 | "Email could not be sent. Please try again later." |
| Google OAuth error | 400 | "Google login failed. Please try again." |

---

## Security Considerations

- **Session cookie**: `httponly`, `samesite=lax`, `secure` in production
- **OAuth state parameter**: Random state token prevents CSRF
- **Rate limiting**: Per-user-email sliding window
- **SMTP credentials**: Not needed — email sent via user's own Gmail API token.
- **No user database**: Session-only identity, minimal data footprint
- **Google client secret**: `.env` only
