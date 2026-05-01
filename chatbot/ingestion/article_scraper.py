"""Scrape full article content from source URLs for RAG ingestion."""

import asyncio
import logging
import random

import httpx
import trafilatura
from bs4 import BeautifulSoup

from chatbot.config.settings import settings

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

TIMEOUT_SECONDS = 15


async def _fetch_html(url: str) -> str | None:
    """Fetch raw HTML from a URL."""
    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT_SECONDS,
            headers=_HEADERS,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None


def _extract_with_trafilatura(html: str) -> str | None:
    """Extract main article text using trafilatura."""
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        no_fallback=False,
    )
    if text and len(text.strip()) > 100:
        return text.strip()
    return None


def _extract_with_beautifulsoup(html: str) -> str | None:
    """Fallback: extract text from <article> tag or main content."""
    soup = BeautifulSoup(html, "html.parser")

    # Try <article> tag first
    article = soup.find("article")
    if article:
        text = article.get_text(separator="\n", strip=True)
        if len(text) > 100:
            return text

    # Try <main> tag
    main = soup.find("main")
    if main:
        text = main.get_text(separator="\n", strip=True)
        if len(text) > 100:
            return text

    return None


async def scrape_article(url: str) -> str | None:
    """Scrape full article content from a URL.

    Uses trafilatura as primary extractor with BeautifulSoup fallback.
    Returns extracted text capped at article_max_chars, or None on failure.
    """
    if not url or not url.startswith("http"):
        return None

    html = await _fetch_html(url)
    if not html:
        return None

    # Try trafilatura first (best quality)
    text = _extract_with_trafilatura(html)

    # Fallback to BeautifulSoup
    if not text:
        text = _extract_with_beautifulsoup(html)

    if not text:
        logger.warning("No content extracted from %s", url)
        return None

    # Cap at max chars
    max_chars = settings.article_max_chars
    if len(text) > max_chars:
        text = text[:max_chars]

    logger.debug("Extracted %d chars from %s", len(text), url)
    return text


async def scrape_articles_batch(
    items: list[dict],
) -> dict[str, str]:
    """Scrape multiple articles with polite delays between requests.

    Args:
        items: List of content item dicts with 'source_url' keys.

    Returns:
        Dict mapping source_url -> extracted text (only successful extractions).
    """
    results: dict[str, str] = {}
    delay = settings.scrape_delay_seconds

    for i, item in enumerate(items):
        url = item.get("source_url", "")
        if not url:
            continue

        text = await scrape_article(url)
        if text:
            results[url] = text

        # Polite delay between requests (with jitter to look natural)
        if i < len(items) - 1:
            jitter = random.uniform(0.5, 1.5)
            await asyncio.sleep(delay * jitter)

    logger.info(
        "Scraped %d/%d articles successfully",
        len(results), len(items),
    )
    return results
