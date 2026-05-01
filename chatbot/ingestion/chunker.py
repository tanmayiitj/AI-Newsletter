"""Chunk article text into LangChain Documents for vector embedding."""

import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from chatbot.config.settings import settings

logger = logging.getLogger(__name__)


def _get_splitter() -> RecursiveCharacterTextSplitter:
    """Return a text splitter configured from settings."""
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
    )


def chunk_article(
    text: str,
    metadata: dict,
) -> list[Document]:
    """Split article text into chunks and attach metadata to each.

    Args:
        text: Full article text.
        metadata: Base metadata dict (edition_number, section_type, etc.).
                  Will be copied and augmented with chunk_index and total_chunks.

    Returns:
        List of LangChain Document objects.
    """
    if not text or not text.strip():
        return []

    splitter = _get_splitter()
    chunks = splitter.split_text(text)

    documents = []
    for i, chunk in enumerate(chunks):
        doc_metadata = {
            **metadata,
            "chunk_index": i,
            "total_chunks": len(chunks),
        }
        documents.append(Document(page_content=chunk, metadata=doc_metadata))

    return documents


def create_job_document(
    job: dict,
    metadata: dict,
) -> Document:
    """Create a single Document from a job listing (no chunking needed).

    Args:
        job: Job listing dict with role_title, company_name, etc.
        metadata: Base metadata dict from the edition/section.

    Returns:
        A single LangChain Document.
    """
    role = job.get("role_title", "")
    company = job.get("company_name", "")
    location = job.get("location_type", "")
    exp = job.get("experience_tier", "")
    desc = job.get("description", "")
    url = job.get("apply_url", "")

    text = (
        f"Job: {role} at {company}\n"
        f"Location: {location}\n"
        f"Experience: {exp}\n"
        f"Description: {desc}"
    )
    if url:
        text += f"\nApply: {url}"

    job_metadata = {
        **metadata,
        "role_title": role,
        "company_name": company,
        "location_type": location,
        "experience_tier": exp,
        "chunk_index": 0,
        "total_chunks": 1,
    }

    return Document(page_content=text, metadata=job_metadata)
