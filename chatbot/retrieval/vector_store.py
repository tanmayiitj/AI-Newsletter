"""Vector store abstraction over ChromaDB.

Designed so the implementation can be swapped to MongoDB Atlas Vector Search
in the future without changing the retrieval chain.
"""

import logging

from langchain_core.vectorstores import VectorStoreRetriever

from chatbot.ingestion.embedder import get_vector_store

logger = logging.getLogger(__name__)


def get_retriever(
    filter_metadata: dict | None = None,
    k: int = 5,
) -> VectorStoreRetriever:
    """Return a LangChain retriever backed by ChromaDB.

    Args:
        filter_metadata: Optional ChromaDB where-clause dict for filtering
                         by year, month, section_type, etc.
        k: Number of documents to retrieve.
    """
    store = get_vector_store()

    search_kwargs: dict = {"k": k}
    if filter_metadata:
        search_kwargs["filter"] = filter_metadata

    return store.as_retriever(search_kwargs=search_kwargs)
