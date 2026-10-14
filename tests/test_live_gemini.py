"""Opt-in semantic acceptance tests; unlike transport fixtures these exercise Gemini."""

import os

import pytest
from fastapi.testclient import TestClient

from app.api.analyze import get_llm_client
from app.main import app
from app.services.llm_client import GeminiClient
from tests.sample_transcripts.cases import GROUPS

pytestmark = [pytest.mark.live, pytest.mark.skipif(
    os.getenv("RUN_LIVE_GEMINI") != "1", reason="Set RUN_LIVE_GEMINI=1 to evaluate real Gemini",
)]


class TracingClient:
    def __init__(self):
        self.client = GeminiClient()
        self.results = []

    async def generate(self, *args, **kwargs):
        result = await self.client.generate(*args, **kwargs)
        self.results.append(result)
        return result


def test_live_specification(spec_case):
    assert os.getenv("GEMINI_API_KEY") and os.getenv("LLM_MODEL"), "Configure Gemini first"
    trace = TracingClient()
    app.dependency_overrides[get_llm_client] = lambda: trace
    try:
        with TestClient(app) as client:
            response = client.post("/analyze", json={"transcript": spec_case["transcript"]})
        assert response.status_code == 200, response.text
        result = response.json()
        assert set(result) == set(GROUPS)
        # Wording may vary; category counts, grounded attributes and state must not.
        for group in GROUPS:
            assert len(result[group]) == len(spec_case["final"][group]), (group, result)
        case_id = spec_case["id"]
        if case_id == "01":
            assert "A" in result["decisions"][0]["content"]
        if case_id == "02":
            assert "payos" in result["decisions"][0]["content"].lower()
            assert "stripe" not in result["decisions"][0]["content"].lower()
            proposals = [e for e in trace.results[0].candidate_events if e.event_type == "DECISION_PROPOSAL"]
            assert any("stripe" in e.content.lower() for e in proposals)
            assert any("payos" in e.content.lower() for e in proposals)
            assert any(r.relation == "ACCEPTS" for r in trace.results[1].relationships)
            assert "seg_003" in result["decisions"][0]["evidence_segment_ids"]
        if case_id == "03":
            text = result["unfinalized_content"][0]["content"].lower()
            assert "stripe" in text and "payos" in text
        if case_id == "04":
            assert result["tasks"][0]["owner"] == "Nam"
            assert "thứ sáu" in result["tasks"][0]["deadline"].lower()
        if case_id == "05":
            assert result["tasks"][0]["owner"] is None
            assert result["tasks"][0]["deadline"] is None
        if case_id == "06":
            assert "login" in result["problems"][0]["content"].lower()
        if case_id == "07":
            assert result["tasks"][0]["owner"] == "Nam"
            assert "deploy" in result["tasks"][0]["content"].lower()
            assert any(r.relation == "BLOCKS" for r in trace.results[1].relationships)
        if case_id == "08":
            assert result["requests"][0]["requester"].lower() == "khách hàng"
            assert result["requests"][0]["target"] is None
        if case_id == "09":
            assert "server" in result["risks"][0]["content"].lower()
        if case_id == "10":
            types = {e.event_type for e in trace.results[0].candidate_events}
            assert {"PROBLEM_RAISED", "PROBLEM_RESOLVED"} <= types
            assert any(r.relation == "RESOLVES" for r in trace.results[1].relationships)
    finally:
        app.dependency_overrides.clear()
