"""Newsletter models and related enumerations."""

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field

from backend.models.job import JobListing

PyObjectId = Annotated[str, BeforeValidator(str)]


class SectionType(str, Enum):
    """Newsletter section types in display order."""

    TRENDING_TOPICS = "trending_topics"
    TOP_DEVELOPMENTS = "top_developments"
    CORPORATE_TOOLS = "corporate_tools"
    FUTURE_REQUIREMENTS = "future_requirements"
    JOBS_BOARD = "jobs_board"


class EditionStatus(str, Enum):
    """Newsletter edition publication status."""

    DRAFT = "draft"
    PUBLISHED = "published"


class ContentItem(BaseModel):
    """An individual article or news item within a newsletter section."""

    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1, max_length=1000)
    source_url: str = Field(..., min_length=1)
    source_name: str = Field(..., min_length=1)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    source_date: Optional[datetime] = None


class NewsletterSection(BaseModel):
    """A thematic block within a newsletter edition."""

    section_type: SectionType
    display_order: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    content_items: list[ContentItem] = Field(default_factory=list)
    job_listings: Optional[list[JobListing]] = None


class NewsletterEdition(BaseModel):
    """A single newsletter issue — top-level document stored in MongoDB."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    edition_number: int = Field(..., ge=1)
    headline: str = Field(..., min_length=1, max_length=300)
    executive_summary: str = Field(..., min_length=1, max_length=2000)
    status: EditionStatus = EditionStatus.DRAFT
    sections: list[NewsletterSection] = Field(..., min_length=5, max_length=5)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None

    model_config = {"populate_by_name": True}


class ArchiveEditionSummary(BaseModel):
    """Lightweight edition projection for archive listing."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    edition_number: int
    headline: str
    executive_summary: str
    created_at: datetime

    model_config = {"populate_by_name": True}


class ArchiveResponse(BaseModel):
    """Paginated archive response."""

    editions: list[ArchiveEditionSummary]
    total: int
    page: int
    per_page: int
    total_pages: int
