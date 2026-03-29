"""Chat service: session management, temporal preprocessing, and orchestration."""

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from chatbot.config.settings import settings
from chatbot.models.schemas import ChatResponse, SourceReference
from chatbot.retrieval.chain import ask_question

logger = logging.getLogger(__name__)

# In-memory session store: session_id -> {"history": [...], "last_active": datetime}
_sessions: dict[str, dict[str, Any]] = {}

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
    "oct": 10, "nov": 11, "dec": 12,
}

# Patterns to detect temporal references in user queries
_MONTH_PATTERN = re.compile(
    r"\b(" + "|".join(MONTH_MAP.keys()) + r")\b",
    re.IGNORECASE,
)
_YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")
_RELATIVE_PATTERNS = {
    re.compile(r"\blast\s+month\b", re.IGNORECASE): -1,
    re.compile(r"\bthis\s+month\b", re.IGNORECASE): 0,
}


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
    # Keep only the last N turns
    max_turns = settings.conversation_window_size
    if len(history) > max_turns:
        _sessions[session_id]["history"] = history[-max_turns:]
    _sessions[session_id]["last_active"] = datetime.now(timezone.utc)


def preprocess_query(raw_query: str) -> tuple[str, dict | None]:
    """Extract temporal filters from the query.

    Returns:
        (cleaned_query, metadata_filter) where metadata_filter is a ChromaDB
        where-clause dict or None if no filter needed.
    """
    now = datetime.now(timezone.utc)
    year: int | None = None
    month: int | None = None
    cleaned = raw_query

    # Check relative patterns (this month, last month)
    for pattern, offset in _RELATIVE_PATTERNS.items():
        match = pattern.search(raw_query)
        if match:
            target_month = now.month + offset
            target_year = now.year
            if target_month <= 0:
                target_month += 12
                target_year -= 1
            year = target_year
            month = target_month
            cleaned = pattern.sub("", cleaned).strip()
            break

    # Check explicit month name
    if month is None:
        month_match = _MONTH_PATTERN.search(raw_query)
        if month_match:
            month = MONTH_MAP[month_match.group(1).lower()]
            cleaned = _MONTH_PATTERN.sub("", cleaned).strip()

    # Check explicit year
    year_match = _YEAR_PATTERN.search(raw_query)
    if year_match:
        year = int(year_match.group(1))
        cleaned = _YEAR_PATTERN.sub("", cleaned).strip()

    # Default: if no temporal reference at all, use current month
    if month is None and year is None:
        year = now.year
        month = now.month

    # Build ChromaDB filter
    filter_dict: dict | None = None
    if year is not None or month is not None:
        conditions = []
        if year is not None:
            conditions.append({"year": {"$eq": year}})
        if month is not None:
            conditions.append({"month": {"$eq": month}})

        if len(conditions) == 1:
            filter_dict = conditions[0]
        else:
            filter_dict = {"$and": conditions}

    # Clean up extra whitespace
    cleaned = " ".join(cleaned.split())

    return cleaned, filter_dict


async def handle_chat(message: str, session_id: str | None) -> ChatResponse:
    """Process a chat message end-to-end.

    1. Get or create session
    2. Preprocess query for temporal filters
    3. Run RAG chain
    4. Update session history
    5. Return structured response
    """
    sid, chat_history = get_or_create_session(session_id)

    cleaned_query, filter_metadata = preprocess_query(message)
    logger.info(
        "Query: '%s' -> cleaned: '%s', filter: %s",
        message, cleaned_query, filter_metadata,
    )

    try:
        result = await ask_question(
            question=cleaned_query,
            chat_history=chat_history,
            filter_metadata=filter_metadata,
        )
    except Exception as e:
        logger.error("RAG chain error: %s", e)
        # If filtered query fails (no data for that month), try without filter
        if filter_metadata:
            logger.info("Retrying without temporal filter")
            try:
                result = await ask_question(
                    question=cleaned_query,
                    chat_history=chat_history,
                    filter_metadata=None,
                )
            except Exception as e2:
                logger.error("RAG chain retry error: %s", e2)
                return ChatResponse(
                    answer="Sorry, I encountered an error processing your question. Please try again.",
                    sources=[],
                    session_id=sid,
                )
        else:
            return ChatResponse(
                answer="Sorry, I encountered an error processing your question. Please try again.",
                sources=[],
                session_id=sid,
            )

    answer = result["answer"]
    source_docs = result.get("source_documents", [])

    # Deduplicate sources by edition_number + section_type
    seen = set()
    sources = []
    for doc in source_docs:
        meta = doc.metadata
        key = (meta.get("edition_number"), meta.get("section_type"))
        if key not in seen:
            seen.add(key)
            sources.append(SourceReference(
                edition_number=meta.get("edition_number", 0),
                section_type=meta.get("section_type", ""),
                section_title=meta.get("section_title", ""),
                published_at=meta.get("published_at", ""),
            ))

    _update_session(sid, message, answer)

    return ChatResponse(
        answer=answer,
        sources=sources,
        session_id=sid,
    )
