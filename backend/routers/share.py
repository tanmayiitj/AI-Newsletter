"""Router for sending newsletter editions to the logged-in user's email."""

import logging

from fastapi import APIRouter, HTTPException, Request

from backend.models.share import SendToSelfRequest, ShareEmailResponse
from backend.routers.auth import get_current_user
from backend.services import email_service, newsletter_service, rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/share", tags=["share"])


@router.post("/send-to-self", response_model=ShareEmailResponse)
async def send_to_self(
    body: SendToSelfRequest,
    request: Request,
) -> ShareEmailResponse:
    """Send the full newsletter edition to the logged-in user's email.

    Args:
        body: Request with the edition_id to send.
        request: FastAPI request (session cookie + base URL).

    Returns:
        ShareEmailResponse indicating success or failure.

    Raises:
        HTTPException: 401 if not logged in, 429 if rate-limited,
            404 if edition not found, 502 if Gmail API fails.
    """
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Please log in with Google first.")

    user_email = user["email"]
    access_token = user.get("access_token", "")

    # Rate-limit check (keyed by user email)
    allowed = await rate_limiter.check_rate_limit(user_email)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="You've sent too many emails recently. Try again in a few minutes.",
        )

    # Fetch edition
    edition = await newsletter_service.get_by_id(body.edition_id)
    if edition is None:
        raise HTTPException(status_code=404, detail="This edition no longer exists.")

    # Build edition URL
    base = str(request.base_url).rstrip("/")
    edition_url = f"{base}/edition/{body.edition_id}"

    # Send email
    try:
        await email_service.send_newsletter_email(
            recipient=user_email,
            edition=edition,
            edition_url=edition_url,
            access_token=access_token,
        )
    except email_service.EmailServiceError as exc:
        logger.error("Send-to-self email failed for %s: %s", user_email, exc)
        raise HTTPException(
            status_code=502,
            detail="Email could not be sent. Please try again later.",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error sending email for %s: %s", user_email, exc)
        raise HTTPException(
            status_code=502,
            detail="Email could not be sent. Please try again later.",
        ) from exc

    return ShareEmailResponse(success=True, message="Newsletter sent to your email!")
