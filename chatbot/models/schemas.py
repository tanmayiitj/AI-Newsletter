"""Pydantic schemas for the chatbot API."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat message from the user."""

    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None


class SourceReference(BaseModel):
    """A reference to the newsletter source that was used to answer."""

    edition_number: int
    section_type: str
    section_title: str
    published_at: str


class ChatResponse(BaseModel):
    """Chat response returned to the user."""

    answer: str
    sources: list[SourceReference] = Field(default_factory=list)
    session_id: str


class IngestionResult(BaseModel):
    """Result of a batch ingestion run."""

    ingested: int
    skipped: int
    errors: list[str] = Field(default_factory=list)
