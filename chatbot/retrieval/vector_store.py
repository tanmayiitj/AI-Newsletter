"""Vector store retrieval using MongoDB Atlas hybrid search.

Combines vector (semantic) search with full-text (keyword) search
using Reciprocal Rank Fusion for best recall and precision.
"""

import logging

from langchain_core.documents import Document

from chatbot.ingestion.embedder import get_vector_store, get_collection
from chatbot.config.settings import settings

logger = logging.getLogger(__name__)


def get_hybrid_retriever(
    filter_metadata: dict | None = None,
    k: int = 5,
):
    """Return a MongoDB Atlas hybrid search retriever.

    Combines $vectorSearch (semantic) with $search (keyword) via RRF.

    Args:
        filter_metadata: Optional MongoDB filter dict for year, month, etc.
        k: Number of documents to retrieve.
    """
    from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

    store = get_vector_store()

    retriever = MongoDBAtlasHybridSearchRetriever(
        vectorstore=store,
        search_index_name=settings.fulltext_index_name,
        top_k=k,
        fulltext_penalty=50,
        vector_penalty=50,
        pre_filter=filter_metadata,
    )
    return retriever


def get_vector_retriever(
    filter_metadata: dict | None = None,
    k: int = 5,
):
    """Fallback: pure vector similarity retriever (no full-text index needed).

    Args:
        filter_metadata: Optional MongoDB pre_filter dict.
        k: Number of documents to retrieve.
    """
    store = get_vector_store()

    search_kwargs: dict = {"k": k}
    if filter_metadata:
        search_kwargs["pre_filter"] = filter_metadata

    return store.as_retriever(search_kwargs=search_kwargs)
