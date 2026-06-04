"""Pydantic schemas for the chatbot API."""

import re

from pydantic import BaseModel, Field, field_validator

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


class ChatRequest(BaseModel):
    """Incoming chat message from the user."""

    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str | None) -> str | None:
        """Reject session IDs that aren't valid UUIDs."""
        if v is not None and not _UUID_RE.match(v):
            return None
        return v


class SourceReference(BaseModel):
    """A reference to the newsletter source that was used to answer."""

    edition_number: int


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
