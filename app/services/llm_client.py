"""The sole LLM gateway: provider transport, prompts, JSON and contract validation."""

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


class LLMError(Exception):
    """Safe public message; never contains provider body, transcript or API key."""


class LLMConfigurationError(LLMError):
    pass


class LLMResponseError(LLMError):
    pass


class LLMProviderError(LLMError):
    pass


class LLMClient(Protocol):
    async def generate(self, prompt_file: str, payload: dict[str, Any],
                       output_model: type[T], *, context: dict[str, Any]) -> T: ...


class GeminiClient:
    def __init__(self, *, transport: httpx.AsyncBaseTransport | None = None,
                 timeout: float = 90.0, max_retries: int = 2):
        self.transport = transport
        self.timeout = timeout
        self.max_retries = max_retries

    async def generate(self, prompt_file: str, payload: dict[str, Any],
                       output_model: type[T], *, context: dict[str, Any]) -> T:
        key = os.environ.get("GEMINI_API_KEY", "").strip()
        model = os.environ.get("LLM_MODEL", "").strip().removeprefix("models/")
        if not key or not model:
            raise LLMConfigurationError("Set GEMINI_API_KEY and LLM_MODEL before analyzing")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
            raise LLMConfigurationError("LLM_MODEL must be a Gemini model name")
        try:
            prompt = (PROMPT_DIR / prompt_file).read_text(encoding="utf-8")
        except OSError:
            raise LLMConfigurationError("Required prompt file is unavailable") from None
        body = {
            "systemInstruction": {"parts": [{"text": prompt}]},
            "contents": [{"role": "user", "parts": [{
                "text": json.dumps(payload, ensure_ascii=False),
            }]}],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
                "responseJsonSchema": output_model.model_json_schema(),
            },
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    response = await client.post(url, headers={"x-goog-api-key": key}, json=body)
                except httpx.TimeoutException:
                    raise LLMProviderError("Gemini request timed out; retry the analysis") from None
                except httpx.RequestError:
                    raise LLMProviderError("Cannot connect to Gemini") from None
                if response.status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                    try:
                        delay = float(response.headers.get("retry-after", 2 ** attempt))
                    except ValueError:
                        delay = float(2 ** attempt)
                    await asyncio.sleep(min(max(delay, 0), 10))
                    continue
                if response.is_error:
                    if response.status_code == 429:
                        raise LLMProviderError("Gemini quota exceeded; retry later")
                    if response.status_code in {401, 403}:
                        raise LLMProviderError("Gemini rejected the API credentials")
                    raise LLMProviderError(f"Gemini request failed (HTTP {response.status_code})")
                break
        try:
            data = response.json()
            candidate = data["candidates"][0]
            if candidate.get("finishReason") != "STOP":
                raise LLMResponseError("Gemini did not return a complete result")
            result = "".join(part["text"] for part in candidate["content"]["parts"]
                             if "text" in part and not part.get("thought"))
            return output_model.model_validate_json(result, context=context)
        except (KeyError, IndexError, TypeError, AttributeError, ValueError, ValidationError):
            raise LLMResponseError(f"Invalid Gemini output for {output_model.__name__}") from None
