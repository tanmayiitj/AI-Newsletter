"""MongoDB async database connection with FastAPI lifespan."""

import logging
from contextlib import asynccontextmanager
from typing import Optional

import certifi
from pymongo import AsyncMongoClient

from backend.config.settings import settings

logger = logging.getLogger(__name__)

db_client: Optional[AsyncMongoClient] = None


def get_database():
    """Return the MongoDB database instance."""
    if db_client is None:
        raise RuntimeError("Database client not initialized")
    return db_client[settings.mongodb_db_name]


def get_collection(name: str):
    """Return a MongoDB collection by name."""
    return get_database()[name]


@asynccontextmanager
async def db_lifespan(app):
    """FastAPI lifespan context manager for database connection."""
    global db_client
    logger.info("Connecting to MongoDB at %s", settings.mongodb_uri)
    db_client = AsyncMongoClient(settings.mongodb_uri, tlsCAFile=certifi.where())
    # Verify connectivity
    await db_client.admin.command("ping")
    logger.info("MongoDB connection established")

    # Create indexes for the editions collection
    editions = db_client[settings.mongodb_db_name]["editions"]
    await editions.create_index("edition_number", unique=True)
    await editions.create_index([("status", 1), ("created_at", -1)])
    await editions.create_index([("created_at", -1)])
    logger.info("MongoDB indexes ensured")

    yield

    db_client.close()
    db_client = None
    logger.info("MongoDB connection closed")
