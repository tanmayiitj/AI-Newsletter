"""Content generator service — orchestrates section-by-section LLM generation."""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from backend.config.settings import settings
from backend.models.newsletter import (
    ContentItem,
    EditionStatus,
    NewsletterEdition,
    NewsletterSection,
    SectionType,
)
from backend.services.llm_client import LLMServiceError, generate_structured
from backend.services.jobs_service import generate_job_listings
from backend.services.news_scraper import (
    scrape_ai_news_by_section,
    format_articles_for_prompt,
    ScrapedArticle,
)

logger = logging.getLogger(__name__)

FULL_TEXT_MAX_CHARS = 15000


# Pydantic models for LLM structured output responses
class LLMContentItems(BaseModel):
    """LLM response model for a list of content items."""

    description: str = Field(
        default="",
        max_length=200,
        description="A 1-2 sentence summary of this section for preview display.",
    )
    items: list[ContentItem] = Field(default_factory=list)


class LLMHeadline(BaseModel):
    """LLM response model for edition headline and summary."""

    headline: str = Field(..., min_length=1, max_length=300)
    executive_summary: str = Field(..., min_length=1, max_length=2000)


# Section generation prompt templates (use {news_context} placeholder)
SECTION_PROMPTS: dict[SectionType, str] = {
    SectionType.TRENDING_TOPICS: (
        "Based on the REAL recent AI news articles below, select and summarize 4-5 "
        "trending AI topics that corporate professionals should know about this week. "
        "Use the ACTUAL titles, URLs, source names, and dates from the articles below. "
        "Do NOT invent or fabricate any URLs or sources. "
        "For each item, provide a title, 2-3 sentence summary, the real source_url "
        "from the article, source_name, relevance score (0.0-1.0), and source_date.\n"
        "Also provide a 'description' field: a single compelling sentence (max 150 chars) "
        "summarizing what this section covers — this is shown as a preview.\n\n"
        "REAL NEWS ARTICLES:\n{news_context}"
    ),
    SectionType.TOP_DEVELOPMENTS: (
        "Based on the REAL recent AI news articles below, identify 4-5 top AI industry "
        "developments. Focus on breakthroughs, product launches, partnerships, and "
        "policy changes. Use the ACTUAL titles, URLs, source names, and dates from "
        "the articles. Do NOT invent or fabricate any URLs or sources.\n"
        "Also provide a 'description' field: a single compelling sentence (max 150 chars) "
        "summarizing what this section covers — this is shown as a preview.\n\n"
        "REAL NEWS ARTICLES:\n{news_context}"
    ),
    SectionType.CORPORATE_TOOLS: (
        "Based on the REAL recent AI news articles below, identify 3-4 AI tools and "
        "platforms relevant to corporate users. Focus on productivity tools, enterprise "
        "platforms, developer tools, and analytics solutions. Use the ACTUAL URLs and "
        "source names from the articles. Do NOT fabricate URLs.\n"
        "Also provide a 'description' field: a single compelling sentence (max 150 chars) "
        "summarizing what this section covers — this is shown as a preview.\n\n"
        "REAL NEWS ARTICLES:\n{news_context}"
    ),
    SectionType.FUTURE_REQUIREMENTS: (
        "Based on the REAL recent AI news articles below, identify 3-4 emerging AI "
        "trends and future skills/requirements that professionals should prepare for. "
        "Cover regulations, skill demands, technology shifts. Use the ACTUAL URLs and "
        "source names from the articles. Do NOT fabricate URLs.\n"
        "Also provide a 'description' field: a single compelling sentence (max 150 chars) "
        "summarizing what this section covers — this is shown as a preview.\n\n"
        "REAL NEWS ARTICLES:\n{news_context}"
    ),
}

SECTION_TITLES: dict[SectionType, str] = {
    SectionType.TRENDING_TOPICS: "Trending AI Topics",
    SectionType.TOP_DEVELOPMENTS: "Top Developments",
    SectionType.CORPORATE_TOOLS: "Corporate AI Tools",
    SectionType.FUTURE_REQUIREMENTS: "Future Requirements & Trends",
    SectionType.JOBS_BOARD: "AI Jobs Board",
}

SECTION_ORDER: list[SectionType] = [
    SectionType.TRENDING_TOPICS,
    SectionType.TOP_DEVELOPMENTS,
    SectionType.CORPORATE_TOOLS,
    SectionType.FUTURE_REQUIREMENTS,
    SectionType.JOBS_BOARD,
]

PLACEHOLDER_DESCRIPTION = "Content is being curated. Check back soon for updates."


async def _get_used_urls() -> set[str]:
    """Fetch all source_url values from previously published editions."""
    from backend.database.connection import get_collection
    collection = get_collection("editions")
    cursor = collection.find(
        {"status": "published"},
        projection={"sections.content_items.source_url": 1},
    )
    used_urls: set[str] = set()
    async for edition in cursor:
        for section in edition.get("sections", []):
            for item in section.get("content_items", []):
                url = item.get("source_url", "")
                if url:
                    used_urls.add(url)
    return used_urls


def _filter_articles(
    articles: list[ScrapedArticle],
    used_urls: set[str],
) -> list[ScrapedArticle]:
    """Remove articles whose URLs were used in previous editions."""
    return [a for a in articles if a.url and a.url not in used_urls]


async def _scrape_full_text(url: str) -> str | None:
    """Scrape full article text from a URL using trafilatura + BeautifulSoup fallback."""
    import httpx
    import trafilatura
    from bs4 import BeautifulSoup

    if not url or not url.startswith("http"):
        return None

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None

    text = trafilatura.extract(html, include_comments=False, include_tables=False, no_fallback=False)
    if text and len(text.strip()) > 100:
        return text.strip()[:FULL_TEXT_MAX_CHARS]

    soup = BeautifulSoup(html, "html.parser")
    for tag in ["article", "main"]:
        el = soup.find(tag)
        if el:
            t = el.get_text(separator="\n", strip=True)
            if len(t) > 100:
                return t[:FULL_TEXT_MAX_CHARS]

    return None


async def _populate_full_text(section: NewsletterSection) -> None:
    """Scrape full text for each content item in a section."""
    for item in section.content_items:
        text = await _scrape_full_text(item.source_url)
        if text:
            item.full_text = text
            logger.info("        Scraped %d chars for '%s'", len(text), item.title[:50])
        else:
            item.full_text = item.summary
            logger.warning("        Scrape failed for '%s', using summary", item.title[:50])


async def generate_section(
    section_type: SectionType,
    display_order: int,
    news_context: str = "",
) -> NewsletterSection:
    """Generate a single newsletter section via LLM.

    Returns a section with content items, or a placeholder section on failure.
    """
    title = SECTION_TITLES[section_type]

    if section_type == SectionType.JOBS_BOARD:
        return await _generate_jobs_section(display_order, title)

    prompt = SECTION_PROMPTS[section_type].format(news_context=news_context)
    start_time = time.monotonic()

    try:
        logger.info("        Calling %s ...", settings.openai_model)
        result = await generate_structured(prompt, LLMContentItems)
        duration = time.monotonic() - start_time
        logger.info(
            "        Done in %.1fs | %d items generated",
            duration, len(result.items),
        )
        return NewsletterSection(
            section_type=section_type,
            display_order=display_order,
            title=title,
            description=result.description or None,
            content_items=result.items,
        )
    except (LLMServiceError, Exception) as e:
        duration = time.monotonic() - start_time
        logger.error(
            "        FAILED after %.1fs | %s",
            duration, str(e),
        )
        logger.warning("        Using placeholder content for this section")
        return NewsletterSection(
            section_type=section_type,
            display_order=display_order,
            title=title,
            description=PLACEHOLDER_DESCRIPTION,
            content_items=[],
        )


async def _generate_jobs_section(
    display_order: int,
    title: str,
) -> NewsletterSection:
    """Generate the jobs board section."""
    start_time = time.monotonic()
    try:
        logger.info("        Calling %s ...", settings.openai_model)
        job_listings = await generate_job_listings()
        duration = time.monotonic() - start_time
        logger.info(
            "        Done in %.1fs | %d job listings generated",
            duration, len(job_listings),
        )
        return NewsletterSection(
            section_type=SectionType.JOBS_BOARD,
            display_order=display_order,
            title=title,
            description=f"{len(job_listings)} curated AI & ML positions from across the industry." if job_listings else None,
            content_items=[],
            job_listings=job_listings,
        )
    except (LLMServiceError, Exception) as e:
        duration = time.monotonic() - start_time
        logger.error(
            "        FAILED after %.1fs | %s",
            duration, str(e),
        )
        logger.warning("        Using placeholder content for this section")
        return NewsletterSection(
            section_type=SectionType.JOBS_BOARD,
            display_order=display_order,
            title=title,
            description=PLACEHOLDER_DESCRIPTION,
            content_items=[],
            job_listings=[],
        )


async def generate_headline(sections: list[NewsletterSection]) -> LLMHeadline:
    """Generate an edition headline and executive summary based on section content."""
    # Build a summary of what was generated for context
    section_summaries = []
    for section in sections:
        if section.content_items:
            titles = [item.title for item in section.content_items[:3]]
            section_summaries.append(
                f"{section.title}: {', '.join(titles)}"
            )
        elif section.job_listings:
            section_summaries.append(
                f"{section.title}: {len(section.job_listings)} job listings"
            )

    context = "\n".join(section_summaries) if section_summaries else "General AI news"

    prompt = (
        f"Based on the following newsletter sections, generate a compelling headline "
        f"(max 300 chars) and executive summary (2-4 sentences, max 2000 chars) for "
        f"this AI newsletter edition:\n\n{context}"
    )

    try:
        return await generate_structured(prompt, LLMHeadline)
    except LLMServiceError:
        logger.warning("Headline generation failed, using fallback")
        return LLMHeadline(
            headline="This Week in AI",
            executive_summary="Your weekly roundup of the most important AI industry news, tools, and opportunities.",
        )


async def generate_full_edition(edition_number: int) -> NewsletterEdition:
    """Generate a complete newsletter edition with all sections.

    Args:
        edition_number: Sequential number for this edition.

    Returns:
        A complete NewsletterEdition ready for storage.

    Raises:
        LLMServiceError: If critical generation steps fail entirely.
    """
    generation_start = time.monotonic()
    total_sections = len(SECTION_ORDER)
    logger.info("="*60)
    logger.info("NEWSLETTER GENERATION STARTED | Edition #%d", edition_number)
    logger.info("="*60)
    logger.info("Model: %s", settings.openai_model)
    logger.info("Sections to generate: %d", total_sections)
    logger.info("-"*60)

    # Step 1: Fetch previously used URLs for dedup
    logger.info("[DEDUP] Fetching previously used URLs ...")
    used_urls = await _get_used_urls()
    logger.info("[DEDUP] Found %d previously used URLs", len(used_urls))

    # Step 2: Scrape news from section-specific RSS feed pools
    logger.info("[SCRAPE] Fetching AI news from section-specific feed pools ...")
    articles_by_section = await scrape_ai_news_by_section()
    logger.info("-"*60)

    # Step 3: Generate all sections sequentially (to stay within rate limits)
    sections: list[NewsletterSection] = []
    for i, section_type in enumerate(SECTION_ORDER, start=1):
        logger.info("[%d/%d] Generating section: %s ...", i, total_sections, SECTION_TITLES[section_type])

        if section_type == SectionType.JOBS_BOARD:
            section = await _generate_jobs_section(i, SECTION_TITLES[section_type])
        else:
            # Get this section's articles, filter out previously used URLs
            section_articles = articles_by_section.get(section_type, [])
            filtered_articles = _filter_articles(section_articles, used_urls)
            logger.info("        %d articles available, %d after dedup",
                        len(section_articles), len(filtered_articles))

            news_context = format_articles_for_prompt(filtered_articles)
            section = await generate_section(section_type, i, news_context=news_context)

            # Scrape full text for selected articles
            if section.content_items:
                logger.info("        Scraping full text for %d articles ...", len(section.content_items))
                await _populate_full_text(section)

                # Add newly used URLs to the exclusion set to prevent reuse in later sections
                for item in section.content_items:
                    used_urls.add(item.source_url)

        sections.append(section)

    logger.info("-"*60)
    logger.info("[%d/%d] Generating headline & executive summary ...", total_sections + 1, total_sections + 1)
    # Generate headline based on generated content
    headline_data = await generate_headline(sections)
    logger.info("Headline: %s", headline_data.headline[:100])

    edition = NewsletterEdition(
        edition_number=edition_number,
        headline=headline_data.headline,
        executive_summary=headline_data.executive_summary,
        status=EditionStatus.PUBLISHED,
        sections=sections,
        published_at=datetime.now(timezone.utc),
    )

    total_duration = time.monotonic() - generation_start
    content_sections = sum(1 for s in sections if s.content_items or s.job_listings)
    placeholder_sections = len(sections) - content_sections
    logger.info("="*60)
    logger.info("NEWSLETTER GENERATION COMPLETE")
    logger.info("  Edition:      #%d", edition_number)
    logger.info("  Duration:     %.1f seconds", total_duration)
    logger.info("  Sections OK:  %d/%d", content_sections, len(sections))
    if placeholder_sections:
        logger.info("  Placeholders: %d (LLM failed for these)", placeholder_sections)
    logger.info("  Saving to database ...")
    logger.info("="*60)

    return edition
