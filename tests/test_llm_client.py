import asyncio
import json

import httpx
import pytest

from app.schemas.meeting_output import ExtractionOutput
from app.services.llm_client import GeminiClient, LLMProviderError, LLMResponseError


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "models/test-model")


@pytest.mark.parametrize("body", [
    {}, {"candidates": []}, {"candidates": [123]}, {"candidates": "invalid"},
    {"candidates": [{"finishReason": "SAFETY", "content": {"parts": []}}]},
    {"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "{"}]}}]},
    {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "not JSON"}]}}]},
    {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": '{"candidate_events":[],"extra":1}'}]}}]},
])
def test_invalid_provider_body(configured, body):
    client = GeminiClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body)))
    with pytest.raises(LLMResponseError):
        asyncio.run(client.generate("extraction_prompt.txt", {"transcript_segments": []},
                                    ExtractionOutput, context={"segment_ids": set()}))


def test_retry_transient_errors(configured):
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) < 3:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, json={"candidates": [{"finishReason": "STOP", "content": {"parts": [
            {"text": "private reasoning", "thought": True},
            {"text": json.dumps({"candidate_events": []})},
        ]}}]})

    client = GeminiClient(transport=httpx.MockTransport(handler))
    result = asyncio.run(client.generate("extraction_prompt.txt", {}, ExtractionOutput, context={}))
    assert result.candidate_events == []
    assert len(calls) == 3


def test_timeout_is_safe(configured):
    def handler(request):
        raise httpx.ReadTimeout("private data", request=request)

    client = GeminiClient(transport=httpx.MockTransport(handler))
    with pytest.raises(LLMProviderError, match="timed out"):
        asyncio.run(client.generate("extraction_prompt.txt", {}, ExtractionOutput, context={}))
