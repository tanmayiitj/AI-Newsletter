"""One-time setup script to create MongoDB Atlas Vector Search and Full-Text indexes."""

import logging
import time

import certifi
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel

from chatbot.config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def create_indexes() -> None:
    """Create the vector search and full-text search indexes on the article_chunks collection.

    Safe to run multiple times — skips indexes that already exist.
    """
    client = MongoClient(settings.mongodb_uri, tlsCAFile=certifi.where())
    db = client[settings.mongodb_db_name]

    # Ensure the collection exists (MongoDB requires it before creating search indexes)
    if settings.mongodb_vector_collection not in db.list_collection_names():
        db.create_collection(settings.mongodb_vector_collection)
        logger.info("Created collection '%s'", settings.mongodb_vector_collection)

    collection = db[settings.mongodb_vector_collection]

    # Check existing indexes
    existing = {idx["name"] for idx in collection.list_search_indexes()}
    logger.info("Existing search indexes: %s", existing)

    # 1. Vector Search Index
    if settings.vector_index_name not in existing:
        logger.info("Creating vector search index '%s'...", settings.vector_index_name)
        vector_index = SearchIndexModel(
            definition={
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": 1536,
                        "similarity": "cosine",
                    },
                    {
                        "type": "filter",
                        "path": "year",
                    },
                    {
                        "type": "filter",
                        "path": "month",
                    },
                    {
                        "type": "filter",
                        "path": "section_type",
                    },
                    {
                        "type": "filter",
                        "path": "edition_number",
                    },
                ]
            },
            name=settings.vector_index_name,
            type="vectorSearch",
        )
        collection.create_search_index(model=vector_index)
        logger.info("Vector search index created. Waiting for it to become queryable...")
        _wait_for_index(collection, settings.vector_index_name)
    else:
        logger.info("Vector search index '%s' already exists, skipping", settings.vector_index_name)

    # 2. Full-Text Search Index (for hybrid search keyword component)
    if settings.fulltext_index_name not in existing:
        logger.info("Creating full-text search index '%s'...", settings.fulltext_index_name)
        text_index = SearchIndexModel(
            definition={
                "mappings": {
                    "dynamic": False,
                    "fields": {
                        "text": {
                            "type": "string",
                            "analyzer": "lucene.standard",
                        },
                    },
                },
            },
            name=settings.fulltext_index_name,
            type="search",
        )
        collection.create_search_index(model=text_index)
        logger.info("Full-text search index created. Waiting for it to become queryable...")
        _wait_for_index(collection, settings.fulltext_index_name)
    else:
        logger.info("Full-text search index '%s' already exists, skipping", settings.fulltext_index_name)

    client.close()
    logger.info("Index setup complete.")


def _wait_for_index(collection, index_name: str, timeout: int = 120) -> None:
    """Poll until an index becomes queryable."""
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        for idx in collection.list_search_indexes():
            if idx["name"] == index_name and idx.get("queryable"):
                logger.info("Index '%s' is ready.", index_name)
                return
        time.sleep(5)
    logger.warning("Index '%s' did not become ready within %ds", index_name, timeout)


if __name__ == "__main__":
    create_indexes()
