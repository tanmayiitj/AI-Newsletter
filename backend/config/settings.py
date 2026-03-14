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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
