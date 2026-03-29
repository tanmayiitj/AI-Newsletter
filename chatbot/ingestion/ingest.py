"""Ingestion pipeline: MongoDB editions -> summarize -> embed in ChromaDB."""

import asyncio
import logging
from datetime import datetime

import certifi
from pymongo import AsyncMongoClient

from chatbot.config.settings import settings
from chatbot.ingestion.summarizer import summarize_section
from chatbot.ingestion.embedder import get_ingested_edition_numbers, store_section_summaries

logger = logging.getLogger(__name__)


async def _fetch_published_editions(client: AsyncMongoClient) -> list[dict]:
    """Fetch all published editions from MongoDB."""
    db = client[settings.mongodb_db_name]
    editions_col = db["editions"]
    cursor = editions_col.find(
        {"status": "published"},
        sort=[("created_at", -1)],
    )
    return await cursor.to_list()


async def run_ingestion(full_reindex: bool = False) -> dict:
    """Run the full ingestion pipeline.

    1. Connect to MongoDB and fetch published editions
    2. Skip editions already in ChromaDB (unless full_reindex)
    3. Summarize each section per edition
    4. Embed and store summaries in ChromaDB

    Returns: {"ingested": int, "skipped": int, "errors": list[str]}
    """
    logger.info("Starting ingestion pipeline (full_reindex=%s)", full_reindex)

    client = AsyncMongoClient(settings.mongodb_uri, tlsCAFile=certifi.where())
    try:
        await client.admin.command("ping")
        editions = await _fetch_published_editions(client)
    finally:
        client.close()

    if not editions:
        logger.info("No published editions found")
        return {"ingested": 0, "skipped": 0, "errors": []}

    already_ingested = set() if full_reindex else get_ingested_edition_numbers()

    ingested = 0
    skipped = 0
    errors = []

    for edition in editions:
        edition_number = edition.get("edition_number", 0)
        if edition_number in already_ingested:
            skipped += 1
            continue

        headline = edition.get("headline", "")
        published_at = edition.get("published_at") or edition.get("created_at")
        if isinstance(published_at, datetime):
            year = published_at.year
            month = published_at.month
            published_at_str = published_at.isoformat()
        else:
            year = 0
            month = 0
            published_at_str = str(published_at) if published_at else ""

        sections = edition.get("sections", [])
        summaries = []

        for section in sections:
            section_type = section.get("section_type", "unknown")
            section_title = section.get("title", section_type)
            try:
                summary_text = await summarize_section(
                    section=section,
                    edition_number=edition_number,
                    published_at=published_at_str,
                )
                summaries.append({
                    "text": summary_text,
                    "metadata": {
                        "edition_number": edition_number,
                        "edition_headline": headline,
                        "section_type": section_type,
                        "section_title": section_title,
                        "published_at": published_at_str,
                        "year": year,
                        "month": month,
                    },
                })
            except Exception as e:
                error_msg = f"Edition #{edition_number}, section '{section_title}': {e}"
                logger.error("Summarization failed — %s", error_msg)
                errors.append(error_msg)

        if summaries:
            store_section_summaries(summaries)
            ingested += 1
            logger.info("Ingested edition #%d (%d sections)", edition_number, len(summaries))

    result = {"ingested": ingested, "skipped": skipped, "errors": errors}
    logger.info("Ingestion complete: %s", result)
    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    asyncio.run(run_ingestion())
