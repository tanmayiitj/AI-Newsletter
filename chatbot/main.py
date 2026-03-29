"""FastAPI chatbot microservice entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chatbot.config.settings import settings
from chatbot.ingestion.embedder import get_vector_store
from chatbot.routers import chat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize ChromaDB on startup."""
    logger.info("Initializing chatbot service...")
    get_vector_store()
    logger.info("ChromaDB vector store ready")
    yield
    logger.info("Chatbot service shutting down")


app = FastAPI(
    title="AI Pulse Chatbot",
    description="RAG chatbot for the AI Pulse Newsletter",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the main app to call this service
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        f"http://localhost:{settings.chatbot_port}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "chatbot"}
