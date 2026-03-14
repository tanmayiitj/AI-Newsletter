"""Newsletter REST API endpoints."""

import asyncio
import logging
import secrets
from typing import Optional

from fastapi import APIRouter, HTTPException, Security
from fastapi.security import APIKeyHeader

from backend.config.settings import settings
from backend.models.newsletter import ArchiveResponse, NewsletterEdition
from backend.services import newsletter_service
from backend.services.content_generator import generate_full_edition
from backend.services.llm_client import LLMServiceError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/newsletter", tags=["newsletter"])

# API key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Concurrency guard for newsletter generation
generation_lock = asyncio.Lock()


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> str:
    """Validate the API key from the X-API-Key header."""
    if api_key is None or not secrets.compare_digest(
        api_key, settings.admin_api_key
    ):
        raise HTTPException(
            status_code=401, detail="Invalid or missing API key"
        )
    return api_key


@router.post("/generate", response_model=NewsletterEdition, status_code=201)
async def generate_newsletter(
    _api_key: str = Security(verify_api_key),
):
    """Trigger generation of a new newsletter edition via LLM."""
    if generation_lock.locked():
        raise HTTPException(
            status_code=409,
            detail="Newsletter generation is already in progress",
        )

    async with generation_lock:
        try:
            edition_number = await newsletter_service.get_next_edition_number()
            logger.info("Received generate request for edition #%d", edition_number)

            edition = await generate_full_edition(edition_number)
            saved = await newsletter_service.create_edition(edition)

            logger.info("Edition #%d saved & published! View at http://localhost:8000", edition_number)
            return saved
        except LLMServiceError as e:
            logger.error("LLM service error during generation: %s", e)
            raise HTTPException(
                status_code=502,
                detail=f"LLM service error: {e}",
            )


@router.get("/latest", response_model=NewsletterEdition)
async def get_latest_edition():
    """Return the most recently published newsletter edition."""
    edition = await newsletter_service.get_latest()
    if edition is None:
        raise HTTPException(status_code=404, detail="No newsletter editions found")
    return edition


@router.get("/archive", response_model=ArchiveResponse)
async def get_archive(page: int = 1, per_page: int = 10):
    """Return a paginated list of published editions for the archive."""
    return await newsletter_service.list_paginated(page=page, per_page=per_page)


@router.get("/search")
async def search_newsletters(
    q: str = "", year: str = "", month: str = "", limit: int = 10,
):
    """Search newsletters by keyword and/or year/month filter.

    Args:
        q: Search query text (searches headlines, summaries, article titles).
        year: Year filter (e.g. 2026).
        month: Month filter (e.g. 03 for March).
        limit: Maximum results (default 10).
    """
    results = await newsletter_service.search_editions(
        query=q, year=year, month=month, limit=min(limit, 50),
    )
    return {"results": [r.model_dump() for r in results], "total": len(results)}


@router.get("/months")
async def get_months():
    """Return available months that have published editions."""
    years = await newsletter_service.get_available_years()
    return {"years": years}


@router.get("/{edition_id}", response_model=NewsletterEdition)
async def get_edition(edition_id: str):
    """Return a specific newsletter edition by its MongoDB ID."""
    edition = await newsletter_service.get_by_id(edition_id)
    if edition is None:
        raise HTTPException(status_code=404, detail="Edition not found")
    return edition
