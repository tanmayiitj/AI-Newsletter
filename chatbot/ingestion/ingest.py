"""Ingestion pipeline: MongoDB editions -> scrape articles -> chunk -> embed in MongoDB Atlas."""

import asyncio
import logging
from datetime import datetime

import certifi
from pymongo import AsyncMongoClient

from chatbot.config.settings import settings
from chatbot.ingestion.article_scraper import scrape_articles_batch
from chatbot.ingestion.chunker import chunk_article, create_job_document
from chatbot.ingestion.embedder import (
    get_ingested_edition_numbers,
    store_documents,
    delete_edition_documents,
)

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


def _build_base_metadata(edition: dict, published_at: datetime | None) -> dict:
    """Build base metadata dict from an edition document."""
    if isinstance(published_at, datetime):
        year = published_at.year
        month = published_at.month
        published_at_str = published_at.isoformat()
    else:
        year = 0
        month = 0
        published_at_str = str(published_at) if published_at else ""

    return {
        "edition_id": str(edition.get("_id", "")),
        "edition_number": edition.get("edition_number", 0),
        "edition_headline": edition.get("headline", ""),
        "published_at": published_at_str,
        "year": year,
        "month": month,
    }


async def _ingest_edition(edition: dict) -> tuple[int, list[str]]:
    """Ingest a single edition: scrape articles, chunk, and embed.

    Returns (num_documents_stored, list_of_errors).
    """
    edition_number = edition.get("edition_number", 0)
    published_at = edition.get("published_at") or edition.get("created_at")
    base_metadata = _build_base_metadata(edition, published_at)

    sections = edition.get("sections", [])
    all_documents = []
    errors = []

    for section in sections:
        section_type = section.get("section_type", "unknown")
        section_title = section.get("title", section_type)
        section_metadata = {
            **base_metadata,
            "section_type": section_type,
            "section_title": section_title,
        }

        # Handle jobs board separately
        if section_type == "jobs_board":
            jobs = section.get("job_listings", [])
            for job in jobs:
                try:
                    doc = create_job_document(job, section_metadata)
                    all_documents.append(doc)
                except Exception as e:
                    errors.append(f"Edition #{edition_number}, job '{job.get('role_title', '')}': {e}")
            continue

        # For content sections: scrape full articles then chunk
        content_items = section.get("content_items", [])
        if not content_items:
            continue

        # Scrape all articles in this section (with polite delays)
        scraped = await scrape_articles_batch(content_items)

        for item in content_items:
            source_url = item.get("source_url", "")
            article_title = item.get("title", "Untitled")

            # Use scraped full text, or fall back to existing summary
            full_text = scraped.get(source_url)
            if full_text:
                # Prepend title for better semantic context
                text_to_chunk = f"{article_title}\n\n{full_text}"
            else:
                # Fallback: use the summary from MongoDB (at least we have something)
                summary = item.get("summary", "")
                if not summary:
                    continue
                text_to_chunk = f"{article_title}\n\n{summary}"
                logger.debug(
                    "Using fallback summary for '%s' (scrape failed)",
                    article_title,
                )

            article_metadata = {
                **section_metadata,
                "article_title": article_title,
                "source_name": item.get("source_name", ""),
                "source_url": source_url,
                "source_date": str(item.get("source_date", "")),
            }

            try:
                chunks = chunk_article(text_to_chunk, article_metadata)
                all_documents.extend(chunks)
            except Exception as e:
                errors.append(
                    f"Edition #{edition_number}, article '{article_title}': {e}"
                )

    # Store all documents for this edition
    if all_documents:
        store_documents(all_documents)

    return len(all_documents), errors


async def run_ingestion(full_reindex: bool = False) -> dict:
    """Run the full ingestion pipeline.

    1. Connect to MongoDB and fetch published editions
    2. Skip editions already ingested (unless full_reindex)
    3. For each edition: scrape articles -> chunk -> embed
    4. Store in MongoDB Atlas Vector Search

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
    to_ingest = [e for e in editions if e.get("edition_number", 0) not in already_ingested]
    total_to_ingest = len(to_ingest)
    total_skipped = len(editions) - total_to_ingest

    logger.info(
        "Found %d editions: %d to ingest, %d already ingested",
        len(editions), total_to_ingest, total_skipped,
    )

    ingested = 0
    skipped = total_skipped
    errors = []

    for idx, edition in enumerate(to_ingest, 1):
        edition_number = edition.get("edition_number", 0)

        # For full reindex, delete existing docs first
        if full_reindex:
            delete_edition_documents(edition_number)

        try:
            num_docs, edition_errors = await _ingest_edition(edition)
            errors.extend(edition_errors)

            if num_docs > 0:
                ingested += 1
                logger.info(
                    "[%d/%d] Ingested edition #%d (%d documents)",
                    idx, total_to_ingest, edition_number, num_docs,
                )
            else:
                logger.warning(
                    "[%d/%d] Edition #%d produced 0 documents",
                    idx, total_to_ingest, edition_number,
                )
        except Exception as e:
            error_msg = f"Edition #{edition_number}: {e}"
            logger.error("Ingestion failed — %s", error_msg)
            errors.append(error_msg)

    result = {"ingested": ingested, "skipped": skipped, "errors": errors}
    logger.info("Ingestion complete: %s", result)
    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    asyncio.run(run_ingestion())
