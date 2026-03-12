"""Job listing generation using real scraped data + LLM formatting."""

import logging

from pydantic import BaseModel, Field

from backend.models.job import JobListing
from backend.services.llm_client import generate_structured, LLMServiceError
from backend.services.jobs_scraper import scrape_ai_jobs, format_jobs_for_prompt

logger = logging.getLogger(__name__)


class LLMJobListings(BaseModel):
    """LLM response model for job listings."""

    listings: list[JobListing] = Field(default_factory=list)


JOBS_PROMPT_TEMPLATE = (
    "Based on the REAL job listings below, create 6-8 newsletter-ready job entries. "
    "Use the ACTUAL job titles, company names, and apply URLs from the listings. "
    "Do NOT invent or fabricate any URLs — use ONLY the real apply URLs provided. "
    "For each listing provide: role_title, company_name, "
    "location_type (remote/hybrid/onsite — infer from the location field), "
    "experience_tier (1-2yr or 2-4yr — infer from the role level), "
    "description (1-2 sentence summary of the role), "
    "and apply_url (use the EXACT URL from the listing).\n\n"
    "REAL JOB LISTINGS:\n{jobs_context}"
)


async def generate_job_listings() -> list[JobListing]:
    """Scrape real jobs, then format them via LLM."""
    logger.info("        Scraping real AI job listings ...")
    scraped_jobs = await scrape_ai_jobs()

    if not scraped_jobs:
        logger.warning("        No jobs scraped — using LLM fallback")
        return await _fallback_generate()

    jobs_context = format_jobs_for_prompt(scraped_jobs)
    prompt = JOBS_PROMPT_TEMPLATE.format(jobs_context=jobs_context)

    result = await generate_structured(prompt, LLMJobListings)
    logger.info("Generated %d job listings from real data", len(result.listings))
    return result.listings


async def _fallback_generate() -> list[JobListing]:
    """Fallback: ask LLM to generate jobs if scraping fails."""
    prompt = (
        "Generate 6-8 AI job listings for a newsletter. Include a mix of "
        "experience tiers (1-2yr and 2-4yr) and location types (remote/hybrid/onsite). "
        "For apply_url, use the format https://jobs.example.com/role-name."
    )
    result = await generate_structured(prompt, LLMJobListings)
    return result.listings
