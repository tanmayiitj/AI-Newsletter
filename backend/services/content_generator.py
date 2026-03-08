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

logger = logging.getLogger(__name__)


# Pydantic models for LLM structured output responses
class LLMContentItems(BaseModel):
    """LLM response model for a list of content items."""

    items: list[ContentItem] = Field(default_factory=list)


class LLMHeadline(BaseModel):
    """LLM response model for edition headline and summary."""

    headline: str = Field(..., min_length=1, max_length=300)
    executive_summary: str = Field(..., min_length=1, max_length=2000)


# Section generation prompts
SECTION_PROMPTS: dict[SectionType, str] = {
    SectionType.TRENDING_TOPICS: (
        "Generate 4-5 trending AI topics that corporate professionals should know about "
        "this week. For each item, provide a title, 2-3 sentence summary, a plausible "
        "source URL and source name, a relevance score (0.0-1.0), and source date. "
        "Focus on enterprise AI, LLMs, automation, and AI governance."
    ),
    SectionType.TOP_DEVELOPMENTS: (
        "Generate 4-5 top AI industry developments from the past week. Include "
        "breakthroughs in research, major product launches, significant partnerships, "
        "and policy changes. For each, provide title, summary, source URL, source name, "
        "relevance score, and source date."
    ),
    SectionType.CORPORATE_TOOLS: (
        "Generate 3-4 AI tools and platforms relevant to corporate users. Include "
        "productivity tools, enterprise AI platforms, developer tools, and analytics "
        "solutions. For each, provide title, summary, source URL, source name, "
        "relevance score, and source date."
    ),
    SectionType.FUTURE_REQUIREMENTS: (
        "Generate 3-4 emerging AI trends and future skills/requirements that "
        "professionals should prepare for. Cover upcoming regulations, skill demands, "
        "technology shifts, and industry transformations. For each, provide title, "
        "summary, source URL, source name, relevance score, and source date."
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


async def generate_section(
    section_type: SectionType,
    display_order: int,
) -> NewsletterSection:
    """Generate a single newsletter section via LLM.

    Returns a section with content items, or a placeholder section on failure.
    """
    title = SECTION_TITLES[section_type]

    if section_type == SectionType.JOBS_BOARD:
        return await _generate_jobs_section(display_order, title)

    prompt = SECTION_PROMPTS[section_type]
    start_time = time.monotonic()

    try:
        logger.info("        Calling DeepSeek-R1 ... (this may take 30-60s)")
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
            description=None,
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
        logger.info("        Calling DeepSeek-R1 ... (this may take 30-60s)")
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
            description=None,
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
    logger.info("Model: %s (provider: %s)", settings.hf_model, settings.hf_provider)
    logger.info("Sections to generate: %d", total_sections)
    logger.info("-"*60)

    # Generate all sections sequentially (to stay within rate limits)
    sections: list[NewsletterSection] = []
    for i, section_type in enumerate(SECTION_ORDER, start=1):
        logger.info("[%d/%d] Generating section: %s ...", i, total_sections, SECTION_TITLES[section_type])
        section = await generate_section(section_type, i)
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
