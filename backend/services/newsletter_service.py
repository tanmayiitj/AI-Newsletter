"""MongoDB CRUD operations for newsletter editions."""

import math
import re
from datetime import datetime, timezone
from typing import Optional

from backend.database.connection import get_collection
from backend.models.newsletter import (
    ArchiveEditionSummary,
    ArchiveResponse,
    NewsletterEdition,
)


COLLECTION_NAME = "editions"


async def create_edition(edition: NewsletterEdition) -> NewsletterEdition:
    """Insert a new newsletter edition into MongoDB."""
    collection = get_collection(COLLECTION_NAME)
    doc = edition.model_dump(by_alias=True, exclude={"id"})
    result = await collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return NewsletterEdition.model_validate(doc)


async def get_latest() -> Optional[NewsletterEdition]:
    """Return the most recently published edition, or None."""
    collection = get_collection(COLLECTION_NAME)
    doc = await collection.find_one(
        {"status": "published"},
        sort=[("created_at", -1)],
    )
    if doc is None:
        return None
    return NewsletterEdition.model_validate(doc)


async def get_by_id(edition_id: str) -> Optional[NewsletterEdition]:
    """Return a specific edition by its MongoDB ObjectId string."""
    from bson import ObjectId

    collection = get_collection(COLLECTION_NAME)
    doc = await collection.find_one({"_id": ObjectId(edition_id)})
    if doc is None:
        return None
    return NewsletterEdition.model_validate(doc)


async def list_paginated(page: int = 1, per_page: int = 10) -> ArchiveResponse:
    """Return a paginated list of published editions (newest first)."""
    collection = get_collection(COLLECTION_NAME)
    query = {"status": "published"}

    total = await collection.count_documents(query)
    total_pages = max(1, math.ceil(total / per_page))
    skip = (page - 1) * per_page

    cursor = collection.find(
        query,
        projection={
            "_id": 1,
            "edition_number": 1,
            "headline": 1,
            "executive_summary": 1,
            "created_at": 1,
        },
    ).sort("created_at", -1).skip(skip).limit(per_page)

    editions = [ArchiveEditionSummary.model_validate(doc) async for doc in cursor]

    return ArchiveResponse(
        editions=editions,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


async def search_editions(
    query: str = "",
    year: str = "",
    month: str = "",
    limit: int = 10,
) -> list[ArchiveEditionSummary]:
    """Search editions by keyword and/or year/month filter.

    Args:
        query: Text to search in headline, summary, and section content.
        year: Year filter (e.g. '2026').
        month: Month filter (e.g. '03' for March).
        limit: Maximum results to return.

    Returns:
        List of matching edition summaries, newest first.
    """
    collection = get_collection(COLLECTION_NAME)
    filters: dict = {"status": "published"}

    # Year + optional month filter
    if year and re.match(r"^\d{4}$", year):
        year_int = int(year)
        if month and re.match(r"^\d{2}$", month):
            mon_int = int(month)
            start = datetime(year_int, mon_int, 1, tzinfo=timezone.utc)
            if mon_int == 12:
                end = datetime(year_int + 1, 1, 1, tzinfo=timezone.utc)
            else:
                end = datetime(year_int, mon_int + 1, 1, tzinfo=timezone.utc)
        else:
            start = datetime(year_int, 1, 1, tzinfo=timezone.utc)
            end = datetime(year_int + 1, 1, 1, tzinfo=timezone.utc)
        filters["created_at"] = {"$gte": start, "$lt": end}
    elif month and re.match(r"^\d{2}$", month):
        # Month only — match that month across all years
        mon_int = int(month)
        filters["$expr"] = {"$eq": [{"$month": "$created_at"}, mon_int]}

    # Text search — regex across headline, summary, and nested content
    if query.strip():
        safe_q = re.escape(query.strip())
        text_regex = {"$regex": safe_q, "$options": "i"}
        filters["$or"] = [
            {"headline": text_regex},
            {"executive_summary": text_regex},
            {"sections.content_items.title": text_regex},
            {"sections.content_items.summary": text_regex},
        ]

    cursor = collection.find(
        filters,
        projection={
            "_id": 1,
            "edition_number": 1,
            "headline": 1,
            "executive_summary": 1,
            "created_at": 1,
        },
    ).sort("created_at", -1).limit(limit)

    return [ArchiveEditionSummary.model_validate(doc) async for doc in cursor]


async def get_available_years() -> list[int]:
    """Return list of years that have published editions, newest first."""
    collection = get_collection(COLLECTION_NAME)
    pipeline = [
        {"$match": {"status": "published"}},
        {"$group": {"_id": {"$year": "$created_at"}}},
        {"$sort": {"_id": -1}},
    ]
    cursor = await collection.aggregate(pipeline)
    results = await cursor.to_list()
    return [doc["_id"] for doc in results]


async def get_next_edition_number() -> int:
    """Return the next sequential edition number."""
    collection = get_collection(COLLECTION_NAME)
    doc = await collection.find_one(
        sort=[("edition_number", -1)],
        projection={"edition_number": 1},
    )
    if doc is None:
        return 1
    return doc["edition_number"] + 1


async def publish_edition(edition_id: str) -> Optional[NewsletterEdition]:
    """Set an edition's status to published with current timestamp."""
    from bson import ObjectId

    collection = get_collection(COLLECTION_NAME)
    result = await collection.find_one_and_update(
        {"_id": ObjectId(edition_id)},
        {"$set": {
            "status": "published",
            "published_at": datetime.now(timezone.utc),
        }},
        return_document=True,
    )
    if result is None:
        return None
    return NewsletterEdition.model_validate(result)
