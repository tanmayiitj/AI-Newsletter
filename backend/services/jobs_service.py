"""Job listing generation with experience tier segmentation."""

import logging

from pydantic import BaseModel, Field

from backend.models.job import JobListing
from backend.services.llm_client import generate_structured

logger = logging.getLogger(__name__)


class LLMJobListings(BaseModel):
    """LLM response model for job listings."""

    listings: list[JobListing] = Field(default_factory=list)


JOBS_PROMPT = (
    "Generate 6-8 realistic AI job listings for a newsletter jobs board. "
    "Include a mix of experience tiers: some for '1-2yr' experience and some for "
    "'2-4yr' experience. Include a variety of location types: remote, hybrid, onsite. "
    "Cover roles like ML Engineer, Data Scientist, AI Product Manager, NLP Engineer, "
    "Computer Vision Engineer, AI Ethics Researcher, and MLOps Engineer. "
    "For each listing provide: role_title, company_name, location_type (remote/hybrid/onsite), "
    "experience_tier (1-2yr or 2-4yr), description (1-2 sentences), and apply_url "
    "(use realistic-looking URLs like https://careers.company.com/role-id)."
)


async def generate_job_listings() -> list[JobListing]:
    """Generate job listings via LLM with experience tier segmentation."""
    result = await generate_structured(JOBS_PROMPT, LLMJobListings)
    logger.info("Generated %d job listings", len(result.listings))
    return result.listings
