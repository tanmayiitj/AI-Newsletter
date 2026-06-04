"""Create vector store documents from newsletter articles."""

import calendar
import logging
from datetime import datetime

from langchain_core.documents import Document

from chatbot.config.settings import settings

logger = logging.getLogger(__name__)


def _build_header(title: str, source_name: str, edition_number: int, published_at: datetime | None) -> str:
    """Build the contextual header prepended to every document."""
    if isinstance(published_at, datetime):
        month_name = calendar.month_abbr[published_at.month]
        year = published_at.year
    else:
        month_name = "Unknown"
        year = ""
    return f"Article: {title} | Source: {source_name}\nEdition #{edition_number} ({month_name} {year})\n\n"


def create_article_document(
    title: str,
    source_name: str,
    edition_number: int,
    published_at: datetime | None,
    text: str,
) -> list[Document]:
    """Create one or more Documents from an article.

    If header + text ≤ max_doc_chars, returns 1 Document.
    If longer, splits at exact max_doc_chars boundaries with header on each.

    Args:
        title: Article title.
        source_name: Publisher name (e.g., "TechCrunch").
        edition_number: Newsletter edition number.
        published_at: Edition publication date.
        text: Full article text (or summary fallback).

    Returns:
        List of LangChain Documents with edition_number as only metadata.
    """
    if not text or not text.strip():
        return []

    header = _build_header(title, source_name, edition_number, published_at)
    max_chars = settings.max_doc_chars
    metadata = {"edition_number": edition_number}

    full_content = header + text
    if len(full_content) <= max_chars:
        return [Document(page_content=full_content, metadata=metadata)]

    # Split at exact max_chars boundaries, prepend header to each part
    documents = []
    content_per_part = max_chars - len(header)
    for i in range(0, len(text), content_per_part):
        part = text[i : i + content_per_part]
        documents.append(Document(page_content=header + part, metadata=metadata.copy()))

    return documents


def create_job_document(
    job: dict,
    edition_number: int,
    published_at: datetime | None,
) -> Document:
    """Create a single Document from a job listing.

    Uses the same header format as articles for uniform vector store documents.

    Args:
        job: Job listing dict with role_title, company_name, etc.
        edition_number: Newsletter edition number.
        published_at: Edition publication date.

    Returns:
        A single LangChain Document.
    """
    role = job.get("role_title", "")
    company = job.get("company_name", "")
    location = job.get("location_type", "")
    exp = job.get("experience_tier", "")
    desc = job.get("description", "")
    url = job.get("apply_url", "")

    if isinstance(published_at, datetime):
        month_name = calendar.month_abbr[published_at.month]
        year = published_at.year
    else:
        month_name = "Unknown"
        year = ""

    header = f"Job: {role} at {company} | Edition #{edition_number} ({month_name} {year})\n\n"
    body = f"Location: {location}\nExperience: {exp}\nDescription: {desc}"
    if url:
        body += f"\nApply: {url}"

    return Document(
        page_content=header + body,
        metadata={"edition_number": edition_number},
    )
