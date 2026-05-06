"""Cron worker: generate a new newsletter edition and ingest it into the RAG chatbot.

Designed to be run as a Render Cron Job (or any scheduled task runner).
Calls the backend API to generate, then runs ingestion directly.

Usage:
    python -m cron_worker

Environment variables required (same .env as the main app):
    ADMIN_API_KEY, MONGODB_URI, MONGODB_DB_NAME, OPENAI_API_KEY
"""

import asyncio
import logging
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("cron_worker")

# The backend URL — defaults to localhost for dev, set BACKEND_URL env var for production
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
TIMEOUT_SECONDS = 600  # newsletter generation can take a few minutes


async def generate_newsletter() -> dict | None:
    """Call the newsletter generation API endpoint."""
    url = f"{BACKEND_URL}/api/v1/newsletter/generate"
    headers = {"X-API-Key": ADMIN_API_KEY}

    logger.info("Triggering newsletter generation at %s", url)

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        try:
            resp = await client.post(url, headers=headers)
            if resp.status_code == 201:
                data = resp.json()
                logger.info(
                    "Newsletter edition #%d generated successfully",
                    data.get("edition_number", "?"),
                )
                return data
            elif resp.status_code == 409:
                logger.warning("Generation already in progress, skipping")
                return None
            else:
                logger.error(
                    "Generation failed: HTTP %d — %s",
                    resp.status_code,
                    resp.text[:500],
                )
                return None
        except Exception as e:
            logger.error("Failed to call generation API: %s", e)
            return None


async def run_ingestion() -> dict | None:
    """Run the chatbot ingestion pipeline to index the new edition."""
    try:
        from chatbot.ingestion.ingest import run_ingestion as _ingest
        result = await _ingest(full_reindex=False)
        logger.info("Ingestion complete: %s", result)
        return result
    except Exception as e:
        logger.error("Ingestion failed: %s", e)
        return None


async def main() -> None:
    """Generate a newsletter and ingest it into the RAG chatbot."""
    logger.info("=" * 60)
    logger.info("CRON WORKER STARTED")
    logger.info("=" * 60)

    if not ADMIN_API_KEY:
        logger.error("ADMIN_API_KEY not set — cannot generate newsletter")
        sys.exit(1)

    # Step 1: Generate newsletter
    edition = await generate_newsletter()
    if edition is None:
        logger.warning("No new edition generated — skipping ingestion")
        sys.exit(0)

    # Step 2: Ingest into RAG chatbot
    logger.info("Starting RAG ingestion for new edition...")
    await run_ingestion()

    logger.info("=" * 60)
    logger.info("CRON WORKER FINISHED")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
