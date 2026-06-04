"""Chatbot configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class ChatbotSettings(BaseSettings):
    """Configuration for the RAG chatbot microservice."""

    # Shared with main app
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "ai_pulse"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    admin_api_key: str = ""

    # Chatbot-specific
    chatbot_port: int = 8001
    ingestion_batch_size: int = 10

    # MongoDB Atlas Vector Search
    mongodb_vector_collection: str = "article_chunks"
    vector_index_name: str = "vector_index"

    # Embedding
    embedding_model: str = "text-embedding-3-small"

    # Document creation
    max_doc_chars: int = 7000

    # Session
    session_ttl_minutes: int = 30
    conversation_window_size: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = ChatbotSettings()
