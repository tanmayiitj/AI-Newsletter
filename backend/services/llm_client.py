"""LLM client service for OpenAI API calls."""

import json
import logging
import re
from typing import TypeVar

import httpx
from pydantic import BaseModel

from backend.config.settings import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
TIMEOUT_SECONDS = 300


def _build_schema_instruction(response_model: type[BaseModel]) -> str:
    """Build a JSON schema instruction string to embed in the prompt."""
    schema = response_model.model_json_schema()
    return (
        "You MUST respond with valid JSON that conforms to this schema:\n"
        f"```json\n{json.dumps(schema, indent=2)}\n```\n"
        "Return ONLY the JSON object, no additional text."
    )


def _extract_json(text: str) -> str:
    """Extract JSON from LLM response, stripping markdown fences and extras."""
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return text


async def generate_structured(
    prompt: str,
    response_model: type[T],
    system_prompt: str = "You are an expert AI industry analyst and newsletter editor.",
) -> T:
    """Call the OpenAI API and return a parsed Pydantic model.

    Args:
        prompt: The user prompt for content generation.
        response_model: Pydantic model class for structured output parsing.
        system_prompt: System prompt setting the assistant's role.

    Returns:
        Parsed Pydantic model instance.

    Raises:
        LLMServiceError: If the API call fails or response cannot be parsed.
    """
    schema_instruction = _build_schema_instruction(response_model)
    full_system = f"{system_prompt}\n\n{schema_instruction}"

    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": full_system},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        try:
            resp = await client.post(OPENAI_API_URL, headers=headers, json=payload)
        except Exception as e:
            logger.error("OpenAI API request error: %s", str(e))
            raise LLMServiceError(f"OpenAI API request failed: {e}") from e

    if resp.status_code != 200:
        logger.error("OpenAI API HTTP %d: %s", resp.status_code, resp.text[:500])
        raise LLMServiceError(
            f"OpenAI API returned HTTP {resp.status_code}: {resp.text[:200]}"
        )

    data = resp.json()

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        logger.error("Unexpected OpenAI response: %s", json.dumps(data)[:500])
        raise LLMServiceError(f"Unexpected OpenAI response: {e}") from e

    if not content:
        raise LLMServiceError("OpenAI API returned empty content")

    cleaned = _extract_json(content)
    try:
        return response_model.model_validate_json(cleaned)
    except Exception as e:
        logger.error("Failed to parse LLM response: %s\nRaw: %s", str(e), content[:500])
        raise LLMServiceError(f"Failed to parse LLM response: {e}") from e


class LLMServiceError(Exception):
    """Raised when the LLM service fails."""
