"""Web scraper for fetching real AI job listings."""

import logging
import re
from dataclasses import dataclass
from typing import List

import httpx

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 15
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

AI_TITLE_KEYWORDS = {
    "ai ", "ai/", " ai", "artificial intelligence", "machine learning",
    "ml engineer", "deep learning", "data scientist", "data science",
    "nlp", "computer vision", "llm", "generative ai", "neural network",
    "pytorch", "tensorflow", "mlops", "ai engineer", "ml ops",
    "prompt engineer", "ai research", "ml research",
}

AI_TAG_KEYWORDS = {
    "machine-learning", "deep-learning", "artificial-intelligence",
    "nlp", "computer-vision", "data-science", "pytorch", "tensorflow",
}


@dataclass
class ScrapedJob:
    """A single scraped job listing."""

    title: str
    company: str
    location: str
    url: str
    source: str


def _clean_html(text: str) -> str:
    """Strip HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _is_ai_related(title: str, tags: list) -> bool:
    """Check if a job is AI/ML related by keyword matching.

    Requires either a title keyword match or at least one AI-specific tag.
    """
    title_lower = title.lower()
    if any(kw in title_lower for kw in AI_TITLE_KEYWORDS):
        return True
    # Check tags list for exact AI tag matches
    tag_set = {t.lower() for t in tags}
    return bool(tag_set & AI_TAG_KEYWORDS)


async def _fetch_remoteok_jobs() -> List[ScrapedJob]:
    """Fetch jobs from RemoteOK API, filtered locally for AI relevance."""
    jobs: List[ScrapedJob] = []
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            resp = await client.get(
                "https://remoteok.com/api",
                headers={"User-Agent": BROWSER_UA},
                follow_redirects=True,
            )
            resp.raise_for_status()

        data = resp.json()
        for item in data[1:]:  # First item is metadata
            tags_list = item.get("tags", [])
            position = item.get("position", "")
            if not _is_ai_related(position, tags_list):
                continue
            jobs.append(ScrapedJob(
                title=position,
                company=item.get("company", "Unknown"),
                location=item.get("location", "Remote"),
                url=item.get("url", item.get("apply_url", "")),
                source="RemoteOK",
            ))
    except Exception as e:
        logger.warning("Failed to fetch RemoteOK jobs: %s", str(e))
    return jobs


async def _fetch_arbeitnow_jobs() -> List[ScrapedJob]:
    """Fetch jobs from Arbeitnow API, filtered locally for AI relevance."""
    jobs: List[ScrapedJob] = []
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            resp = await client.get(
                "https://www.arbeitnow.com/api/job-board-api",
                headers={"User-Agent": BROWSER_UA},
                follow_redirects=True,
            )
            resp.raise_for_status()

        data = resp.json()
        for item in data.get("data", []):
            title = item.get("title", "")
            desc = item.get("description", "")[:200]
            tags_list = item.get("tags", [])
            # Include description words as pseudo-tags for matching
            desc_words = desc.lower().split()
            combined_tags = tags_list + [w for w in desc_words if len(w) > 2]
            if not _is_ai_related(title, combined_tags):
                continue
            location = item.get("location", "")
            if item.get("remote"):
                location = "Remote" + (f" / {location}" if location else "")
            jobs.append(ScrapedJob(
                title=_clean_html(title),
                company=item.get("company_name", "Unknown"),
                location=location or "Not specified",
                url=item.get("url", ""),
                source="Arbeitnow",
            ))
    except Exception as e:
        logger.warning("Failed to fetch Arbeitnow jobs: %s", str(e))
    return jobs


async def scrape_ai_jobs() -> List[ScrapedJob]:
    """Scrape real AI job listings from multiple sources.

    Returns:
        List of scraped job listings filtered for AI/ML relevance.
    """
    logger.info("        Scraping AI jobs from RemoteOK + Arbeitnow ...")
    all_jobs: List[ScrapedJob] = []

    for name, fetcher in [("RemoteOK", _fetch_remoteok_jobs), ("Arbeitnow", _fetch_arbeitnow_jobs)]:
        jobs = await fetcher()
        all_jobs.extend(jobs)
        logger.info("        %s: %d AI jobs found", name, len(jobs))

    # Deduplicate by title+company
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (job.title.lower(), job.company.lower())
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    logger.info("        Total unique AI jobs: %d", len(unique_jobs))
    return unique_jobs


def format_jobs_for_prompt(jobs: List[ScrapedJob], max_jobs: int = 15) -> str:
    """Format scraped jobs into a text block for LLM prompt context."""
    lines = []
    for i, job in enumerate(jobs[:max_jobs], 1):
        lines.append(
            f"{i}. {job.title} at {job.company}\n"
            f"   Location: {job.location}\n"
            f"   Apply: {job.url}\n"
        )
    return "\n".join(lines)
