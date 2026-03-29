"""ChromaDB embedding storage for newsletter section summaries."""

import logging

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from chatbot.config.settings import settings

logger = logging.getLogger(__name__)

_vector_store: Chroma | None = None


def get_vector_store() -> Chroma:
    """Return the ChromaDB vector store singleton, creating it if needed."""
    global _vector_store
    if _vector_store is None:
        embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)
        _vector_store = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=embeddings,
            persist_directory=settings.chroma_persist_dir,
        )
        logger.info("ChromaDB initialized at %s", settings.chroma_persist_dir)
    return _vector_store


def get_ingested_edition_numbers() -> set[int]:
    """Return the set of edition numbers already stored in ChromaDB."""
    store = get_vector_store()
    collection = store._collection
    result = collection.get(include=["metadatas"])
    if not result["metadatas"]:
        return set()
    return {m["edition_number"] for m in result["metadatas"] if "edition_number" in m}


def store_section_summaries(
    summaries: list[dict],
) -> int:
    """Store section summaries as documents in ChromaDB.

    Each item in summaries should have:
        - text: str (the summary)
        - metadata: dict with edition_number, section_type, section_title,
                     edition_headline, published_at, year, month

    Returns the number of documents stored.
    """
    if not summaries:
        return 0

    store = get_vector_store()

    documents = []
    for s in summaries:
        doc = Document(
            page_content=s["text"],
            metadata=s["metadata"],
        )
        documents.append(doc)

    store.add_documents(documents)
    logger.info("Stored %d section summaries in ChromaDB", len(documents))
    return len(documents)
