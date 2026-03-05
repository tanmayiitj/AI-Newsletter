"""MongoDB CRUD operations for newsletter editions."""

import math
from datetime import datetime, timezone

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


async def get_latest() -> NewsletterEdition | None:
    """Return the most recently published edition, or None."""
    collection = get_collection(COLLECTION_NAME)
    doc = await collection.find_one(
        {"status": "published"},
        sort=[("created_at", -1)],
    )
    if doc is None:
        return None
    return NewsletterEdition.model_validate(doc)


async def get_by_id(edition_id: str) -> NewsletterEdition | None:
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


async def publish_edition(edition_id: str) -> NewsletterEdition | None:
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
