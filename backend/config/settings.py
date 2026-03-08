"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from .env file."""

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "ai_pulse"
    hf_api_token: str = ""
    hf_model: str = "deepseek-ai/DeepSeek-R1"
    hf_provider: str = "novita"
    admin_api_key: str = ""
    app_env: str = "development"
    app_port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
