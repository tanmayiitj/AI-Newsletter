"""Web scraper for fetching real AI news from RSS feeds."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List

import feedparser
import httpx

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 15


@dataclass
class ScrapedArticle:
    """A single scraped news article."""

    title: str
    summary: str
    url: str
    source_name: str
    published: str


# RSS feeds for AI/tech news
AI_NEWS_FEEDS = [
    ("https://techcrunch.com/category/artificial-intelligence/feed/", "TechCrunch"),
    ("https://www.theverge.com/rss/index.xml", "The Verge"),
    ("https://venturebeat.com/category/ai/feed/", "VentureBeat"),
    ("https://feeds.arstechnica.com/arstechnica/technology-lab", "Ars Technica"),
    ("https://www.wired.com/feed/tag/ai/latest/rss", "WIRED"),
    ("https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml", "MIT News"),
    ("https://blog.google/technology/ai/rss/", "Google AI Blog"),
]


def _clean_html(text: str) -> str:
    """Strip HTML tags from text."""
    import re
    clean = re.sub(r"<[^>]+>", "", text or "")
    clean = clean.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    clean = clean.replace("&quot;", '"').replace("&#39;", "'")
    return clean.strip()


async def _fetch_feed(url: str, source_name: str) -> List[ScrapedArticle]:
    """Fetch and parse a single RSS feed."""
    articles = []
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()

        feed = feedparser.parse(resp.text)
        for entry in feed.entries[:5]:
            summary = _clean_html(
                entry.get("summary", entry.get("description", ""))
            )
            if len(summary) > 300:
                summary = summary[:297] + "..."

            published = ""
            if hasattr(entry, "published"):
                published = entry.published
            elif hasattr(entry, "updated"):
                published = entry.updated

            articles.append(ScrapedArticle(
                title=_clean_html(entry.get("title", "Untitled")),
                summary=summary,
                url=entry.get("link", ""),
                source_name=source_name,
                published=published,
            ))
    except Exception as e:
        logger.warning("Failed to fetch feed %s: %s", source_name, str(e))

    return articles


async def scrape_ai_news() -> List[ScrapedArticle]:
    """Scrape recent AI news from multiple RSS feeds.

    Returns:
        List of scraped articles sorted by recency.
    """
    logger.info("        Scraping AI news from %d RSS feeds ...", len(AI_NEWS_FEEDS))
    all_articles: List[ScrapedArticle] = []

    for url, source_name in AI_NEWS_FEEDS:
        articles = await _fetch_feed(url, source_name)
        all_articles.extend(articles)
        if articles:
            logger.info("        %s: %d articles fetched", source_name, len(articles))

    logger.info("        Total articles scraped: %d", len(all_articles))
    return all_articles


def format_articles_for_prompt(articles: List[ScrapedArticle], max_articles: int = 20) -> str:
    """Format scraped articles into a text block for LLM prompt context."""
    lines = []
    for i, article in enumerate(articles[:max_articles], 1):
        lines.append(
            f"{i}. [{article.source_name}] {article.title}\n"
            f"   URL: {article.url}\n"
            f"   Date: {article.published}\n"
            f"   Summary: {article.summary}\n"
        )
    return "\n".join(lines)
