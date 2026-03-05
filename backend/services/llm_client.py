"""LLM client service for OpenAI-compatible API calls."""

import logging
from typing import TypeVar

import httpx
from pydantic import BaseModel

from backend.config.settings import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

API_BASE_URL = "https://api.openai.com/v1"
TIMEOUT_SECONDS = 120


async def generate_structured(
    prompt: str,
    response_model: type[T],
    system_prompt: str = "You are an expert AI industry analyst and newsletter editor.",
) -> T:
    """Call the OpenAI API with structured output and return a parsed Pydantic model.

    Args:
        prompt: The user prompt for content generation.
        response_model: Pydantic model class for structured output parsing.
        system_prompt: System prompt setting the assistant's role.

    Returns:
        Parsed Pydantic model instance.

    Raises:
        LLMServiceError: If the API call fails or response cannot be parsed.
    """
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    schema = response_model.model_json_schema()
    # Wrap schema for OpenAI structured output format
    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "strict": True,
                "schema": schema,
            },
        },
    }

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.post(
            f"{API_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            error_detail = response.text[:500]
            logger.error("LLM API error %d: %s", response.status_code, error_detail)
            raise LLMServiceError(
                f"LLM API returned status {response.status_code}"
            )

        data = response.json()

        # Check for refusal
        message = data["choices"][0]["message"]
        if message.get("refusal"):
            logger.warning("LLM refused request: %s", message["refusal"])
            raise LLMServiceError(f"LLM refused: {message['refusal']}")

        content = message["content"]
        return response_model.model_validate_json(content)


class LLMServiceError(Exception):
    """Raised when the LLM service call fails."""
