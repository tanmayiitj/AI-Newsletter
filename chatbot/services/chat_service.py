"""Chat service: session management and orchestration."""

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from chatbot.config.settings import settings
from chatbot.models.schemas import ChatResponse, SourceReference
from chatbot.retrieval.chain import ask_question
from chatbot.ingestion.embedder import get_ingested_edition_numbers

logger = logging.getLogger(__name__)

# In-memory session store: session_id -> {"history": [...], "last_active": datetime}
_sessions: dict[str, dict[str, Any]] = {}


def _cleanup_expired_sessions() -> None:
    """Remove sessions that have been inactive beyond the TTL."""
    now = datetime.now(timezone.utc)
    ttl_seconds = settings.session_ttl_minutes * 60
    expired = [
        sid for sid, data in _sessions.items()
        if (now - data["last_active"]).total_seconds() > ttl_seconds
    ]
    for sid in expired:
        del _sessions[sid]
    if expired:
        logger.info("Cleaned up %d expired sessions", len(expired))


def get_or_create_session(session_id: str | None) -> tuple[str, list[tuple[str, str]]]:
    """Get existing session history or create a new one.

    Returns (session_id, chat_history) where chat_history is list of (human, ai) tuples.
    """
    _cleanup_expired_sessions()

    # Validate session_id format (UUID only)
    if session_id and not re.match(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        session_id,
        re.IGNORECASE,
    ):
        session_id = None

    if session_id and session_id in _sessions:
        session = _sessions[session_id]
        session["last_active"] = datetime.now(timezone.utc)
        return session_id, session["history"]

    new_id = session_id or str(uuid.uuid4())
    _sessions[new_id] = {
        "history": [],
        "last_active": datetime.now(timezone.utc),
    }
    return new_id, []


def _update_session(session_id: str, human_msg: str, ai_msg: str) -> None:
    """Append a conversation turn to the session history (bounded by window size)."""
    if session_id not in _sessions:
        return
    history = _sessions[session_id]["history"]
    history.append((human_msg, ai_msg))
    max_turns = settings.conversation_window_size
    if len(history) > max_turns:
        _sessions[session_id]["history"] = history[-max_turns:]
    _sessions[session_id]["last_active"] = datetime.now(timezone.utc)


async def handle_chat(message: str, session_id: str | None) -> ChatResponse:
    """Process a chat message end-to-end.

    1. Get or create session
    2. Run RAG chain (no preprocessing — query goes directly to vector search)
    3. Update session history
    4. Return structured response
    """
    sid, chat_history = get_or_create_session(session_id)

    # Check if vector store has any data
    if not get_ingested_edition_numbers():
        return ChatResponse(
            answer="No newsletter data has been ingested yet. Please ask an admin to run the ingestion pipeline first.",
            sources=[],
            session_id=sid,
        )

    logger.info("Query: '%s'", message)

    try:
        result = await ask_question(
            question=message,
            chat_history=chat_history,
        )
    except Exception as e:
        logger.error("RAG chain error: %s", e)
        return ChatResponse(
            answer="Sorry, I encountered an error processing your question. Please try again.",
            sources=[],
            session_id=sid,
        )

    answer = result["answer"]
    source_docs = result.get("source_documents", [])

    # Deduplicate sources by unique edition_number
    seen_editions: set[int] = set()
    sources = []
    for doc in source_docs:
        edition_num = doc.metadata.get("edition_number", 0)
        if edition_num not in seen_editions:
            seen_editions.add(edition_num)
            sources.append(SourceReference(edition_number=edition_num))

    _update_session(sid, message, answer)

    return ChatResponse(
        answer=answer,
        sources=sources,
        session_id=sid,
    )
