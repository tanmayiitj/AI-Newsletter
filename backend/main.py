"""FastAPI application entrypoint."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.database.connection import db_lifespan
from backend.routers import auth, health, newsletter, pages, share

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "frontend" / "static"

app = FastAPI(
    title="AI Pulse Newsletter",
    description="AI-powered newsletter curating the latest AI industry content",
    version="1.0.0",
    lifespan=db_lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(newsletter.router)
app.include_router(share.router)
app.include_router(pages.router)
