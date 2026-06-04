"""Ingestion pipeline: MongoDB editions -> create documents -> embed in MongoDB Atlas."""

import asyncio
import logging
from datetime import datetime

import certifi
from pymongo import AsyncMongoClient, MongoClient

from chatbot.config.settings import settings
from chatbot.ingestion.chunker import create_article_document, create_job_document
from chatbot.ingestion.embedder import (
    get_ingested_edition_numbers,
    store_documents,
    get_collection,
    get_vector_store,
)

logger = logging.getLogger(__name__)

MIN_EDITION_NUMBER = 7  # Skip editions 1-6 (hallucinated/fake URLs)


async def _fetch_published_editions(client: AsyncMongoClient) -> list[dict]:
    """Fetch all published editions from MongoDB."""
    db = client[settings.mongodb_db_name]
    editions_col = db["editions"]
    cursor = editions_col.find(
        {"status": "published"},
        sort=[("created_at", -1)],
    )
    return await cursor.to_list()


async def _ingest_edition(edition: dict) -> tuple[int, list[str]]:
    """Ingest a single edition: create documents from stored content and embed.

    Returns (num_documents_stored, list_of_errors).
    """
    edition_number = edition.get("edition_number", 0)
    published_at = edition.get("published_at") or edition.get("created_at")

    sections = edition.get("sections", [])
    all_documents = []
    errors = []

    for section in sections:
        section_type = section.get("section_type", "unknown")

        # Handle jobs board
        if section_type == "jobs_board":
            jobs = section.get("job_listings", [])
            for job in jobs:
                try:
                    doc = create_job_document(job, edition_number, published_at)
                    all_documents.append(doc)
                except Exception as e:
                    errors.append(f"Edition #{edition_number}, job '{job.get('role_title', '')}': {e}")
            continue

        # For content sections: use stored full_text or fallback to summary
        content_items = section.get("content_items", [])
        for item in content_items:
            article_title = item.get("title", "Untitled")
            source_name = item.get("source_name", "Unknown")

            # Use full_text if available, otherwise fall back to summary
            text = item.get("full_text") or item.get("summary", "")
            if not text:
                continue

            try:
                docs = create_article_document(
                    title=article_title,
                    source_name=source_name,
                    edition_number=edition_number,
                    published_at=published_at,
                    text=text,
                )
                all_documents.extend(docs)
            except Exception as e:
                errors.append(
                    f"Edition #{edition_number}, article '{article_title}': {e}"
                )

    # Store all documents for this edition
    if all_documents:
        store_documents(all_documents)

    return len(all_documents), errors


def _drop_and_recreate_collection() -> None:
    """Drop the vector store collection and recreate the vector search index."""
    logger.info("Dropping collection '%s' for full reindex ...", settings.mongodb_vector_collection)
    collection = get_collection()
    collection.drop()
    logger.info("Collection dropped. Recreating vector search index ...")

    store = get_vector_store()
    try:
        store.create_vector_search_index(dimensions=1536, wait_until_complete=60)
        logger.info("Vector search index recreated.")
    except Exception as e:
        logger.warning("Could not auto-create vector index (may need manual creation): %s", e)


async def run_ingestion(full_reindex: bool = False) -> dict:
    """Run the full ingestion pipeline.

    1. Connect to MongoDB and fetch published editions
    2. Skip editions < 7 and already ingested (unless full_reindex)
    3. For each edition: create documents from stored content -> embed
    4. Store in MongoDB Atlas Vector Search

    Returns: {"ingested": int, "skipped": int, "errors": list[str]}
    """
    logger.info("Starting ingestion pipeline (full_reindex=%s)", full_reindex)

    if full_reindex:
        _drop_and_recreate_collection()

    client = AsyncMongoClient(settings.mongodb_uri, tlsCAFile=certifi.where())
    try:
        await client.admin.command("ping")
        editions = await _fetch_published_editions(client)
    finally:
        await client.aclose()

    if not editions:
        logger.info("No published editions found")
        return {"ingested": 0, "skipped": 0, "errors": []}

    # Filter to editions >= MIN_EDITION_NUMBER
    eligible = [e for e in editions if e.get("edition_number", 0) >= MIN_EDITION_NUMBER]
    skipped_old = len(editions) - len(eligible)
    if skipped_old:
        logger.info("Skipped %d editions below #%d", skipped_old, MIN_EDITION_NUMBER)

    already_ingested = set() if full_reindex else get_ingested_edition_numbers()
    to_ingest = [e for e in eligible if e.get("edition_number", 0) not in already_ingested]
    total_to_ingest = len(to_ingest)
    total_skipped = len(eligible) - total_to_ingest + skipped_old

    logger.info(
        "Found %d editions: %d to ingest, %d skipped",
        len(editions), total_to_ingest, total_skipped,
    )

    ingested = 0
    skipped = total_skipped
    errors = []

    for idx, edition in enumerate(to_ingest, 1):
        edition_number = edition.get("edition_number", 0)

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
