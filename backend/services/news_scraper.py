"""Web scraper for fetching real AI news from RSS feeds organized by section."""

import logging
from dataclasses import dataclass
from typing import Dict, List

import feedparser
import httpx

from backend.models.newsletter import SectionType

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


# Section-specific RSS feed pools — each section draws from its own set of feeds
SECTION_FEED_POOLS: Dict[SectionType, List[tuple]] = {
    SectionType.TRENDING_TOPICS: [
        ("https://techcrunch.com/category/artificial-intelligence/feed/", "TechCrunch"),
        ("https://www.theverge.com/rss/index.xml", "The Verge"),
        ("https://www.wired.com/feed/tag/ai/latest/rss", "WIRED"),
        ("https://the-decoder.com/feed/", "The Decoder"),
        ("https://www.zdnet.com/topic/artificial-intelligence/rss.xml", "ZDNet"),
    ],
    SectionType.TOP_DEVELOPMENTS: [
        ("https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/anthropic-news.xml", "Anthropic"),
        ("https://blog.google/technology/ai/rss/", "Google AI Blog"),
        ("https://huggingface.co/blog/feed.xml", "Hugging Face"),
        ("https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/cohere-blog.xml", "Cohere"),
        ("https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/mistral-news.xml", "Mistral"),
        ("https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/claude-blog.xml", "Claude Blog"),
    ],
    SectionType.CORPORATE_TOOLS: [
        ("https://thenewstack.io/category/ai/feed/", "The New Stack"),
        ("https://www.marktechpost.com/feed/", "MarkTechPost"),
        ("https://feeds.arstechnica.com/arstechnica/technology-lab", "Ars Technica"),
    ],
    SectionType.FUTURE_REQUIREMENTS: [
        ("https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss", "IEEE Spectrum"),
        ("https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/aisi-blog.xml", "AISI"),
        ("https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/the-batch.xml", "The Batch"),
        ("https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/tldr-ai.xml", "TLDR AI"),
        ("https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/anthropic-research.xml", "Anthropic Research"),
        ("https://raw.githubusercontent.com/alan-turing-institute/ai-rss-feeds/refs/heads/main/feeds/allenai-news.xml", "Ai2"),
    ],
}


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
        for entry in feed.entries:
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


async def scrape_ai_news_by_section() -> Dict[SectionType, List[ScrapedArticle]]:
    """Scrape AI news from RSS feeds, grouped by newsletter section.

    Each section has its own pool of feeds. No article appears in more than one section.

    Returns:
        Dict mapping SectionType to list of ScrapedArticles for that section.
    """
    results: Dict[SectionType, List[ScrapedArticle]] = {}

    for section_type, feeds in SECTION_FEED_POOLS.items():
        section_articles: List[ScrapedArticle] = []
        for url, source_name in feeds:
            articles = await _fetch_feed(url, source_name)
            section_articles.extend(articles)
            if articles:
                logger.info("        %s [%s]: %d articles", source_name, section_type.value, len(articles))

        results[section_type] = section_articles
        logger.info("        Section %s: %d total articles", section_type.value, len(section_articles))

    total = sum(len(arts) for arts in results.values())
    logger.info("        Total articles scraped across all sections: %d", total)
    return results


def format_articles_for_prompt(articles: List[ScrapedArticle]) -> str:
    """Format scraped articles into a text block for LLM prompt context."""
    lines = []
    for i, article in enumerate(articles, 1):
        lines.append(
            f"{i}. [{article.source_name}] {article.title}\n"
            f"   URL: {article.url}\n"
            f"   Date: {article.published}\n"
            f"   Summary: {article.summary}\n"
        )
    return "\n".join(lines)
