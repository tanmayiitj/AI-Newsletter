"""LLM client service for Hugging Face Inference API calls."""

import json
import logging
import re
from typing import TypeVar

from huggingface_hub import AsyncInferenceClient
from pydantic import BaseModel

from backend.config.settings import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

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
    """Extract JSON from LLM response, stripping reasoning/think tags and markdown fences."""
    # Remove <think>...</think> blocks (DeepSeek-R1 reasoning)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Remove markdown code fences
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.strip()
    # Find the first { and last } to extract JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text


async def generate_structured(
    prompt: str,
    response_model: type[T],
    system_prompt: str = "You are an expert AI industry analyst and newsletter editor.",
) -> T:
    """Call the Hugging Face Inference API and return a parsed Pydantic model.

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
    full_system_prompt = f"{system_prompt}\n\n{schema_instruction}"

    client = AsyncInferenceClient(
        model=settings.hf_model,
        provider=settings.hf_provider,
        token=settings.hf_api_token,
        timeout=TIMEOUT_SECONDS,
    )

    try:
        response = await client.chat_completion(
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=4096,
        )
    except Exception as e:
        logger.error("Hugging Face API error: %s", str(e))
        raise LLMServiceError(f"Hugging Face API call failed: {e}") from e

    content = response.choices[0].message.content
    if not content:
        raise LLMServiceError("Hugging Face API returned empty content")

    cleaned = _extract_json(content)
    try:
        return response_model.model_validate_json(cleaned)
    except Exception as e:
        logger.error("Failed to parse LLM response: %s\nRaw content: %s", str(e), content[:500])
        raise LLMServiceError(f"Failed to parse LLM response: {e}") from e


class LLMServiceError(Exception):
    """Raised when the LLM service call fails."""
