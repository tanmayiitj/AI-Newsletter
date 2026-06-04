"""MongoDB Atlas Vector Search storage for newsletter article chunks."""

import logging

import certifi
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from chatbot.config.settings import settings

logger = logging.getLogger(__name__)

_vector_store: MongoDBAtlasVectorSearch | None = None
_mongo_client: MongoClient | None = None


def _get_mongo_client() -> MongoClient:
    """Return a cached synchronous MongoClient."""
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(
            settings.mongodb_uri, tlsCAFile=certifi.where()
        )
    return _mongo_client


def get_vector_store() -> MongoDBAtlasVectorSearch:
    """Return the MongoDB Atlas Vector Search store singleton."""
    global _vector_store
    if _vector_store is None:
        client = _get_mongo_client()
        collection = client[settings.mongodb_db_name][settings.mongodb_vector_collection]
        embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model=settings.embedding_model,
        )
        _vector_store = MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=embeddings,
            index_name=settings.vector_index_name,
        )
        logger.info(
            "MongoDB Atlas Vector Search initialized (db=%s, collection=%s)",
            settings.mongodb_db_name,
            settings.mongodb_vector_collection,
        )
    return _vector_store


def get_collection():
    """Return the raw MongoDB collection for direct queries."""
    client = _get_mongo_client()
    return client[settings.mongodb_db_name][settings.mongodb_vector_collection]


def get_ingested_edition_numbers() -> set[int]:
    """Return the set of edition numbers already stored in the vector collection."""
    collection = get_collection()
    edition_numbers = collection.distinct("edition_number")
    return set(edition_numbers)


def store_documents(documents: list[Document]) -> int:
    """Store chunked documents with embeddings in MongoDB Atlas.

    Args:
        documents: List of LangChain Documents with page_content and metadata.

    Returns:
        Number of documents stored.
    """
    if not documents:
        return 0

    store = get_vector_store()
    store.add_documents(documents)
    logger.info("Stored %d documents in MongoDB Atlas Vector Search", len(documents))
    return len(documents)


def delete_edition_documents(edition_number: int) -> int:
    """Delete all documents for a specific edition (for re-ingestion).

    Returns the number of documents deleted.
    """
    collection = get_collection()
    result = collection.delete_many({"edition_number": edition_number})
    logger.info(
        "Deleted %d documents for edition #%d",
        result.deleted_count, edition_number,
    )
    return result.deleted_count
