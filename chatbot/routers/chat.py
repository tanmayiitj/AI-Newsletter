"""Chat and ingestion API routes."""

import logging

from fastapi import APIRouter, Header, HTTPException

from chatbot.config.settings import settings
from chatbot.models.schemas import ChatRequest, ChatResponse, IngestionResult
from chatbot.services.chat_service import handle_chat
from chatbot.ingestion.ingest import run_ingestion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Handle a chat message and return an AI-generated answer."""
    return await handle_chat(
        message=request.message,
        session_id=request.session_id,
    )


@router.post("/ingest", response_model=IngestionResult)
async def ingest(
    x_api_key: str = Header(..., alias="X-API-Key"),
    full_reindex: bool = False,
) -> IngestionResult:
    """Trigger newsletter ingestion into the vector store (admin only)."""
    if x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")

    result = await run_ingestion(full_reindex=full_reindex)
    return IngestionResult(**result)
