"""Health check endpoint."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.database.connection import get_database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check():
    """Return application health status including database connectivity."""
    try:
        db = get_database()
        await db.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error("Health check failed: %s", e)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
