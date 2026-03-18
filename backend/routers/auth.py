"""Google OAuth 2.0 authentication router with signed session cookies."""

import json
import logging
import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from itsdangerous import BadSignature, TimestampSigner

from backend.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

SESSION_COOKIE = "aipulse_session"

_signer = TimestampSigner(settings.session_secret_key)

# In-memory state store for CSRF protection (short-lived)
_oauth_states: set[str] = set()


def _set_session(response: Response, user_data: dict) -> None:
    """Sign and store user data in a session cookie.

    Args:
        response: FastAPI response to attach the cookie to.
        user_data: Dict with email, name, picture keys.
    """
    payload = json.dumps(user_data)
    signed = _signer.sign(payload).decode("utf-8")
    response.set_cookie(
        key=SESSION_COOKIE,
        value=signed,
        max_age=settings.session_max_age,
        httponly=True,
        samesite="lax",
        secure=settings.app_env == "production",
    )


def get_current_user(request: Request) -> Optional[dict]:
    """Extract user data from the signed session cookie.

    Args:
        request: Incoming FastAPI request.

    Returns:
        Dict with user info or None if no valid session.
    """
    cookie = request.cookies.get(SESSION_COOKIE)
    if not cookie:
        return None
    try:
        unsigned = _signer.unsign(
            cookie.encode("utf-8"),
            max_age=settings.session_max_age,
        )
        return json.loads(unsigned)
    except (BadSignature, json.JSONDecodeError):
        return None


@router.get("/login")
async def login(request: Request) -> Response:
    """Redirect the user to Google's OAuth consent screen.

    Returns:
        302 redirect to Google OAuth URL.
    """
    state = secrets.token_urlsafe(32)
    _oauth_states.add(state)

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile https://www.googleapis.com/auth/gmail.send",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return Response(status_code=302, headers={"Location": url})


@router.get("/callback")
async def callback(request: Request) -> Response:
    """Handle the Google OAuth callback, exchange code for user info.

    Args:
        request: Incoming request with code and state query params.

    Returns:
        302 redirect to homepage with session cookie set.

    Raises:
        HTTPException: 400 if state or code exchange fails.
    """
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code or not state or state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Google login failed. Please try again.")
    _oauth_states.discard(state)

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            logger.error("Google token exchange failed: %s", token_resp.text)
            raise HTTPException(status_code=400, detail="Google login failed. Please try again.")

        tokens = token_resp.json()
        access_token = tokens.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Google login failed. Please try again.")

        # Fetch user info
        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Google login failed. Please try again.")

        userinfo = userinfo_resp.json()

    user_data = {
        "email": userinfo.get("email", ""),
        "name": userinfo.get("name", ""),
        "picture": userinfo.get("picture", ""),
        "access_token": access_token,
    }

    # Redirect to the page user came from, default to homepage
    redirect_to = request.query_params.get("redirect", "/")
    response = Response(status_code=302, headers={"Location": redirect_to})
    _set_session(response, user_data)
    logger.info("User logged in: %s", user_data["email"])
    return response


@router.post("/logout")
async def logout() -> Response:
    """Clear the session cookie and return success.

    Returns:
        JSON response confirming logout.
    """
    response = Response(
        content='{"success": true, "message": "Logged out"}',
        media_type="application/json",
    )
    response.delete_cookie(SESSION_COOKIE, samesite="lax")
    return response


@router.get("/me")
async def me(request: Request) -> dict:
    """Return the current user's profile or 401 if not logged in.

    Args:
        request: Incoming request with session cookie.

    Returns:
        Dict with email, name, picture.

    Raises:
        HTTPException: 401 if no valid session.
    """
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    # Don't expose access_token to frontend
    return {
        "email": user.get("email", ""),
        "name": user.get("name", ""),
        "picture": user.get("picture", ""),
    }
