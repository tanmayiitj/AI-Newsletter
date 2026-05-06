"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.database.connection import db_lifespan
from backend.routers import auth, health, newsletter, pages, share
from chatbot.ingestion.embedder import get_vector_store
from chatbot.ingestion.ingest import run_ingestion
from chatbot.routers import chat as chatbot_chat

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "frontend" / "static"


@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    """Combined lifespan: MongoDB + vector store init + auto-ingest."""
    async with db_lifespan(app):
        try:
            get_vector_store()
            logger.info("MongoDB Atlas Vector Search ready")
            result = await run_ingestion(full_reindex=False)
            logger.info("Auto-ingest complete: %s", result)
        except Exception as e:
            logger.error("Vector store/ingest init failed: %s", e)
            logger.warning("Chatbot queries may fail until data is ingested")
        yield


app = FastAPI(
    title="AI Pulse Newsletter",
    description="AI-powered newsletter curating the latest AI industry content",
    version="1.0.0",
    lifespan=combined_lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(newsletter.router)
app.include_router(share.router)
app.include_router(chatbot_chat.router)
app.include_router(pages.router)
