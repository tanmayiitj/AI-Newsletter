"""Content generator service — orchestrates section-by-section LLM generation."""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

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
        result = await generate_structured(prompt, LLMContentItems)
        duration = time.monotonic() - start_time
        logger.info(
            "Section '%s' generated successfully | items=%d | duration=%.2fs",
            section_type.value, len(result.items), duration,
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
            "Section '%s' generation failed | duration=%.2fs | error=%s",
            section_type.value, duration, str(e),
        )
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
        job_listings = await generate_job_listings()
        duration = time.monotonic() - start_time
        logger.info(
            "Section 'jobs_board' generated successfully | listings=%d | duration=%.2fs",
            len(job_listings), duration,
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
            "Section 'jobs_board' generation failed | duration=%.2fs | error=%s",
            duration, str(e),
        )
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
    logger.info("Starting newsletter generation | edition=%d", edition_number)

    # Generate all sections sequentially (to stay within rate limits)
    sections: list[NewsletterSection] = []
    for i, section_type in enumerate(SECTION_ORDER, start=1):
        section = await generate_section(section_type, i)
        sections.append(section)

    # Generate headline based on generated content
    headline_data = await generate_headline(sections)

    edition = NewsletterEdition(
        edition_number=edition_number,
        headline=headline_data.headline,
        executive_summary=headline_data.executive_summary,
        status=EditionStatus.PUBLISHED,
        sections=sections,
        published_at=datetime.now(timezone.utc),
    )

    total_duration = time.monotonic() - generation_start
    logger.info(
        "Newsletter generation complete | edition=%d | duration=%.2fs",
        edition_number, total_duration,
    )

    return edition
