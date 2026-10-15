import copy
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.analyze import get_llm_client
from app.main import app
from app.services.llm_client import GeminiClient
from tests.sample_transcripts.cases import CASES


@pytest.fixture(params=CASES, ids=lambda c: f"spec_{c['id']}")
def spec_case(request):
    return copy.deepcopy(request.param)


@pytest.fixture
def mocked_api(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    calls = []
    responses = []

    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        assert request.headers["x-goog-api-key"] == "test-key"
        assert request.url.path.endswith("/test-model:generateContent")
        result = responses.pop(0)
        if isinstance(result, httpx.Response):
            return result
        return httpx.Response(200, json={"candidates": [{
            "finishReason": "STOP", "content": {"parts": [{"text": json.dumps(result, ensure_ascii=False)}]},
        }]})

    app.dependency_overrides[get_llm_client] = lambda: GeminiClient(
        transport=httpx.MockTransport(handler), max_retries=0,
    )
    with TestClient(app) as client:
        yield client, calls, responses
    app.dependency_overrides.clear()
