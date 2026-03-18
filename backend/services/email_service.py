"""Email service for sending full newsletter editions via Gmail API."""

import base64
import logging
from email.message import EmailMessage

import httpx

from backend.models.newsletter import NewsletterEdition, SectionType

logger = logging.getLogger(__name__)

GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

# Section accent colors + icons matching the website theme
_SECTION_STYLES = {
    SectionType.TRENDING_TOPICS: {"color": "#f59e0b", "bg": "#fffbeb", "icon": "🔥"},
    SectionType.TOP_DEVELOPMENTS: {"color": "#6366f1", "bg": "#eef2ff", "icon": "🚀"},
    SectionType.CORPORATE_TOOLS: {"color": "#10b981", "bg": "#ecfdf5", "icon": "🛠️"},
    SectionType.FUTURE_REQUIREMENTS: {"color": "#8b5cf6", "bg": "#f5f3ff", "icon": "🔮"},
    SectionType.JOBS_BOARD: {"color": "#f97316", "bg": "#fff7ed", "icon": "💼"},
}


class EmailServiceError(Exception):
    """Raised when an email fails to send."""


def _build_plain_text(edition: NewsletterEdition, edition_url: str) -> str:
    """Build a plain-text rendering of the full newsletter.

    Args:
        edition: The newsletter edition to render.
        edition_url: URL to the online edition.

    Returns:
        Plain-text email body.
    """
    parts = [
        f"AI Pulse Newsletter — Edition #{edition.edition_number}",
        f"{edition.headline}",
        "",
        edition.executive_summary,
        "",
    ]
    for section in edition.sections:
        parts.append(f"═══ {section.title} ═══")
        if section.description:
            parts.append(section.description)
        if section.content_items:
            for item in section.content_items:
                parts.append(f"\n• {item.title}")
                parts.append(f"  {item.summary}")
                parts.append(f"  Source: {item.source_name} — {item.source_url}")
        if section.job_listings:
            for job in section.job_listings:
                parts.append(f"\n• {job.role_title} @ {job.company_name}")
                parts.append(f"  {job.location_type.value} · {job.experience_tier.value}")
                parts.append(f"  Apply: {job.apply_url}")
        parts.append("")
    parts += [
        f"Read online: {edition_url}",
        "",
        "---",
        "AI Pulse Newsletter",
    ]
    return "\n".join(parts)


def _build_html(edition: NewsletterEdition, edition_url: str) -> str:
    """Build a professional HTML email rendering of the full newsletter.

    Uses table-based layout for email client compatibility, with section
    accent colors and icons matching the website theme.

    Args:
        edition: The newsletter edition to render.
        edition_url: URL to the online edition.

    Returns:
        HTML email body string.
    """
    sections_html = ""
    for section in edition.sections:
        style = _SECTION_STYLES.get(
            section.section_type,
            {"color": "#6366f1", "bg": "#eef2ff", "icon": "📌"},
        )
        accent = style["color"]
        bg = style["bg"]
        icon = style["icon"]

        # Build content items
        items_html = ""
        if section.content_items:
            for item in section.content_items:
                items_html += (
                    '<tr><td style="padding:8px 0;">'
                    '<table width="100%" cellpadding="0" cellspacing="0" border="0">'
                    "<tr><td style=\"background:#ffffff;border-radius:8px;"
                    "padding:14px 16px;border:1px solid #e2e8f0;\">"
                    f"<a href=\"{item.source_url}\" style=\"color:#1a1a2e;"
                    f"font-weight:600;font-size:15px;text-decoration:none;"
                    f"line-height:1.4;\">{item.title}</a>"
                    f"<p style=\"color:#64748b;font-size:13px;line-height:1.5;"
                    f"margin:6px 0 8px;\">{item.summary}</p>"
                    f"<span style=\"display:inline-block;background:{bg};"
                    f"color:{accent};font-size:11px;font-weight:600;"
                    f"padding:3px 8px;border-radius:4px;\">{item.source_name}</span>"
                    "</td></tr></table></td></tr>"
                )

        if section.job_listings:
            for job in section.job_listings:
                items_html += (
                    '<tr><td style="padding:8px 0;">'
                    '<table width="100%" cellpadding="0" cellspacing="0" border="0">'
                    "<tr><td style=\"background:#ffffff;border-radius:8px;"
                    "padding:14px 16px;border:1px solid #e2e8f0;\">"
                    f"<span style=\"color:#1a1a2e;font-weight:600;"
                    f"font-size:15px;\">{job.role_title}</span>"
                    f"<span style=\"color:#64748b;font-size:13px;\">"
                    f" @ {job.company_name}</span>"
                    f"<p style=\"color:#64748b;font-size:12px;margin:6px 0 8px;\">"
                    f"{job.location_type.value} · {job.experience_tier.value}</p>"
                    f"<a href=\"{job.apply_url}\" style=\"display:inline-block;"
                    f"background:{accent};color:#ffffff;font-size:12px;"
                    f"font-weight:600;padding:6px 14px;border-radius:5px;"
                    f"text-decoration:none;\">Apply →</a>"
                    "</td></tr></table></td></tr>"
                )

        desc_html = ""
        if section.description:
            desc_html = (
                f"<tr><td style=\"color:#64748b;font-size:13px;"
                f"line-height:1.5;padding:0 0 4px;\">"
                f"{section.description}</td></tr>"
            )

        sections_html += (
            '<table width="100%" cellpadding="0" cellspacing="0" border="0"'
            ' style="margin-bottom:28px;"><tr><td>'
            # Section header pill
            f"<table cellpadding=\"0\" cellspacing=\"0\" border=\"0\""
            f" style=\"margin-bottom:12px;\"><tr>"
            f"<td style=\"background:{accent};width:4px;"
            f"border-radius:4px;\"></td>"
            f"<td style=\"padding:10px 14px;background:{bg};"
            f"border-radius:0 8px 8px 0;\">"
            f"<span style=\"font-size:16px;\">{icon}</span>"
            f"&nbsp;<span style=\"font-weight:700;font-size:16px;"
            f"color:#1a1a2e;\">{section.title}</span>"
            f"</td></tr></table>"
            # Description + items
            '<table width="100%" cellpadding="0" cellspacing="0" border="0">'
            f"{desc_html}{items_html}</table>"
            "</td></tr></table>"
        )

    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        "</head><body style=\"margin:0;padding:0;background:#f1f5f9;"
        "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',"
        "Roboto,Helvetica,Arial,sans-serif;\">"
        # Outer wrapper
        '<table width="100%" cellpadding="0" cellspacing="0" border="0"'
        ' style="background:#f1f5f9;"><tr>'
        '<td align="center" style="padding:24px 16px;">'
        # Inner card
        '<table width="100%" cellpadding="0" cellspacing="0" border="0"'
        ' style="max-width:600px;background:#ffffff;border-radius:16px;'
        'overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.06);">'
        # Header gradient bar
        "<tr><td style=\"background:linear-gradient(135deg,#6366f1,#8b5cf6);"
        "padding:32px 28px;text-align:center;\">"
        "<h1 style=\"margin:0;font-size:13px;font-weight:600;"
        "color:rgba(255,255,255,0.75);letter-spacing:0.08em;"
        "text-transform:uppercase;\">⚡ AI Pulse Newsletter</h1>"
        f"<p style=\"margin:4px 0 0;font-size:11px;"
        f"color:rgba(255,255,255,0.55);\">Edition #{edition.edition_number}"
        f" · {edition.created_at.strftime('%B %d, %Y')}</p>"
        "</td></tr>"
        # Headline + summary
        "<tr><td style=\"padding:28px 28px 0;\">"
        f"<h2 style=\"margin:0 0 12px;font-size:24px;line-height:1.3;"
        f"color:#1a1a2e;font-weight:700;\">{edition.headline}</h2>"
        f"<p style=\"margin:0 0 24px;font-size:15px;line-height:1.6;"
        f"color:#64748b;font-style:italic;border-left:3px solid #e2e8f0;"
        f"padding-left:14px;\">{edition.executive_summary}</p>"
        "</td></tr>"
        # Sections
        f"<tr><td style=\"padding:0 28px;\">{sections_html}</td></tr>"
        # CTA button
        "<tr><td style=\"padding:8px 28px 28px;text-align:center;\">"
        f"<a href=\"{edition_url}\" style=\"display:inline-block;"
        f"padding:14px 32px;background:linear-gradient(135deg,#6366f1,#8b5cf6);"
        f"color:#ffffff;font-size:15px;font-weight:600;"
        f"text-decoration:none;border-radius:10px;"
        f"letter-spacing:0.02em;\">Read Full Edition Online</a>"
        "</td></tr>"
        # Footer
        "<tr><td style=\"background:#f8fafc;padding:20px 28px;"
        "border-top:1px solid #e2e8f0;text-align:center;\">"
        "<p style=\"margin:0;font-size:11px;color:#94a3b8;"
        "line-height:1.5;\">⚡ AI Pulse Newsletter<br>"
        "Curated AI industry news, tools &amp; opportunities</p>"
        "</td></tr>"
        "</table></td></tr></table></body></html>"
    )


async def send_newsletter_email(
    recipient: str,
    edition: NewsletterEdition,
    edition_url: str,
    access_token: str,
) -> None:
    """Build and send the full newsletter via the Gmail API.

    Uses the user's own Google OAuth access token to send the email
    through their Gmail account.

    Args:
        recipient: Email address to send to (the user themselves).
        edition: Full newsletter edition with all sections.
        edition_url: Direct link to the edition page.
        access_token: Google OAuth access token with gmail.send scope.

    Raises:
        EmailServiceError: If the Gmail API call fails.
    """
    subject = f"[AI Pulse] Edition #{edition.edition_number} \u2014 {edition.headline}"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = recipient
    msg["To"] = recipient
    msg.set_content(_build_plain_text(edition, edition_url))
    msg.add_alternative(_build_html(edition, edition_url), subtype="html")

    # Gmail API expects base64url-encoded RFC 2822 message
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GMAIL_SEND_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                json={"raw": raw},
                timeout=30.0,
            )
            if resp.status_code != 200:
                logger.error("Gmail API error %s: %s", resp.status_code, resp.text)
                raise EmailServiceError(f"Gmail API returned {resp.status_code}")
        logger.info("Newsletter email sent to %s via Gmail API", recipient)
    except EmailServiceError:
        raise
    except Exception as exc:
        logger.error("Error sending via Gmail API: %s", exc)
        raise EmailServiceError(str(exc)) from exc
