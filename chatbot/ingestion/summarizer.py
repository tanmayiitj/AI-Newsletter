"""Summarize newsletter sections using OpenAI for vector embedding."""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError, APITimeoutError

from chatbot.config.settings import settings

logger = logging.getLogger(__name__)

NEWS_SUMMARY_PROMPT = """Summarize the following AI newsletter section in 300-500 words.
Capture: core events, technologies and companies mentioned, and key takeaways.
Be factual and concise. Do not add opinions or speculation.

Section: {section_title}
Edition: #{edition_number}
Published: {published_at}

Content:
{content_text}"""

JOBS_SUMMARY_PROMPT = """Summarize the following AI job listings section.
Include: total number of roles, companies hiring, role types (e.g. Senior AI Engineer),
experience levels, location breakdown (remote/hybrid/onsite).
Be factual and structured.

Edition: #{edition_number}
Published: {published_at}

Listings:
{content_text}"""


def _format_content_items(section: dict) -> str:
    """Format content items from a section into readable text."""
    items = section.get("content_items", [])
    parts = []
    for i, item in enumerate(items, 1):
        title = item.get("title", "Untitled")
        summary = item.get("summary", "")
        source = item.get("source_name", "")
        parts.append(f"{i}. [{source}] {title}\n   {summary}")
    return "\n\n".join(parts) if parts else "No content items."


def _format_job_listings(section: dict) -> str:
    """Format job listings from the jobs board section into readable text."""
    jobs = section.get("job_listings", [])
    parts = []
    for i, job in enumerate(jobs, 1):
        role = job.get("role_title", "")
        company = job.get("company_name", "")
        location = job.get("location_type", "")
        exp = job.get("experience_tier", "")
        desc = job.get("description", "")
        parts.append(f"{i}. {role} at {company} ({location}, {exp})\n   {desc}")
    return "\n\n".join(parts) if parts else "No job listings."


@retry(
    retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(4),
    before_sleep=lambda rs: logger.warning(
        "OpenAI call failed (attempt %d), retrying in %ds...",
        rs.attempt_number, rs.next_action.sleep,
    ),
)
async def summarize_section(
    section: dict,
    edition_number: int,
    published_at: str,
) -> str:
    """Generate a summary of a single newsletter section using OpenAI.

    Returns the summary text string.
    """
    section_type = section.get("section_type", "")
    section_title = section.get("title", section_type)
    is_jobs = section_type == "jobs_board"

    if is_jobs:
        content_text = _format_job_listings(section)
        prompt = JOBS_SUMMARY_PROMPT.format(
            edition_number=edition_number,
            published_at=published_at,
            content_text=content_text,
        )
    else:
        content_text = _format_content_items(section)
        prompt = NEWS_SUMMARY_PROMPT.format(
            section_title=section_title,
            edition_number=edition_number,
            published_at=published_at,
            content_text=content_text,
        )

    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=0.3,
        max_tokens=800,
    )

    messages = [
        SystemMessage(content="You are a precise summarizer for an AI industry newsletter."),
        HumanMessage(content=prompt),
    ]

    response = await llm.ainvoke(messages)
    summary = response.content.strip()
    logger.info(
        "Summarized section '%s' for edition #%d (%d chars)",
        section_title,
        edition_number,
        len(summary),
    )
    return summary
