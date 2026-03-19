"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from .env file."""

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "ai_pulse"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    admin_api_key: str = ""
    app_env: str = "development"
    app_port: int = 8000

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/callback"

    # Session
    session_secret_key: str = "change-me-in-production"
    session_max_age: int = 86400

    # Rate limiting for share endpoint
    rate_limit_max_requests: int = 3
    rate_limit_window_seconds: int = 600

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
