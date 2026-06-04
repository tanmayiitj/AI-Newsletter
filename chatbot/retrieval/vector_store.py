"""Vector store retrieval using MongoDB Atlas with MMR for diversity."""

import logging

from chatbot.ingestion.embedder import get_vector_store

logger = logging.getLogger(__name__)


def get_vector_retriever(k: int = 5, fetch_k: int = 20, lambda_mult: float = 0.7):
    """Return a MongoDB Atlas MMR retriever for diverse, relevant results.

    Args:
        k: Number of documents to return.
        fetch_k: Number of candidates to consider for MMR reranking.
        lambda_mult: Balance between relevance (1.0) and diversity (0.0).
    """
    store = get_vector_store()

    return store.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": k,
            "fetch_k": fetch_k,
            "lambda_mult": lambda_mult,
        },
    )
