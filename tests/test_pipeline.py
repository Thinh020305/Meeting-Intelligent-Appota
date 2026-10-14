import copy
import json
import httpx
import pytest

from app.services.llm_client import PROMPT_DIR
from app.services.preprocessing import preprocess
from tests.sample_transcripts.cases import CASES, GROUPS


def test_specification_end_to_end(spec_case, mocked_api):
    client, calls, responses = mocked_api
    responses.extend(spec_case[stage] for stage in ("extraction", "relationship", "final"))
    response = client.post("/analyze", json={"transcript": spec_case["transcript"]})
    assert response.status_code == 200, response.text
    assert response.json() == spec_case["final"]
    assert set(response.json()) == set(GROUPS)
    assert len(calls) == 3
    expected_segments = [s.model_dump() for s in preprocess(spec_case["transcript"])]
    for body, prompt in zip(calls, ("extraction_prompt.txt", "relationship_prompt.txt", "final_state_prompt.txt")):
        assert body["systemInstruction"]["parts"][0]["text"] == (PROMPT_DIR / prompt).read_text(encoding="utf-8")
        assert body["generationConfig"]["responseMimeType"] == "application/json"
        assert json.loads(body["contents"][0]["parts"][0]["text"])["transcript_segments"] == expected_segments
    middle = json.loads(calls[1]["contents"][0]["parts"][0]["text"])
    final = json.loads(calls[2]["contents"][0]["parts"][0]["text"])
    assert middle["candidate_events"] == spec_case["extraction"]["candidate_events"]
    assert final["candidate_events"] == middle["candidate_events"]
    assert final["event_threads"] == spec_case["relationship"]["threads"]
    assert final["relationships"] == spec_case["relationship"]["relationships"]
    assert set(calls[2]["generationConfig"]["responseJsonSchema"]["required"]) == set(GROUPS)


@pytest.mark.parametrize("payload", [{}, {"transcript": "  \n "}, {"transcript": 123},
                                    {"transcript": "PM: Hi", "extra": True}])
def test_invalid_request_never_calls_llm(payload, mocked_api):
    client, calls, _ = mocked_api
    assert client.post("/analyze", json=payload).status_code == 422
    assert calls == []


def test_missing_configuration(monkeypatch, mocked_api):
    client, calls, _ = mocked_api
    monkeypatch.delenv("GEMINI_API_KEY")
    assert client.post("/analyze", json={"transcript": "PM: Chốt A."}).status_code == 503
    assert calls == []


@pytest.mark.parametrize("stage,mutation", [
    (0, "unknown_evidence"), (0, "duplicate_event"), (0, "reverse_events"),
    (1, "missing_reason"), (1, "unknown_event"), (1, "lost_event"),
    (1, "reverse_thread"), (2, "unknown_evidence"), (2, "missing_group"),
    (2, "extra_field"), (2, "empty_content"),
])
def test_invalid_model_output_stops_pipeline(stage, mutation, mocked_api):
    client, calls, responses = mocked_api
    data = copy.deepcopy(CASES[1])
    outputs = [data[k] for k in ("extraction", "relationship", "final")]
    bad = outputs[stage]
    if mutation == "unknown_evidence":
        records = bad["candidate_events"] if stage == 0 else bad["decisions"]
        records[0]["evidence_segment_ids"] = ["seg_999"]
    elif mutation == "duplicate_event":
        bad["candidate_events"][1]["event_id"] = "evt_001"
    elif mutation == "reverse_events":
        bad["candidate_events"].reverse()
    elif mutation == "missing_reason":
        del bad["relationships"][0]["reason"]
    elif mutation == "unknown_event":
        bad["relationships"][0]["to_event"] = "evt_999"
    elif mutation == "lost_event":
        bad["threads"][0]["event_ids"].pop()
    elif mutation == "reverse_thread":
        bad["threads"][0]["event_ids"].reverse()
    elif mutation == "missing_group":
        del bad["risks"]
    elif mutation == "extra_field":
        bad["decisions"][0]["status"] = "final"
    elif mutation == "empty_content":
        bad["decisions"][0]["content"] = " "
    responses.extend(outputs)
    result = client.post("/analyze", json={"transcript": data["transcript"]})
    assert result.status_code == 502
    assert len(calls) == stage + 1


@pytest.mark.parametrize("status", [403, 429, 500])
def test_provider_errors_are_safe(status, mocked_api):
    client, calls, responses = mocked_api
    responses.append(httpx.Response(status, text="secret API key and private transcript"))
    response = client.post("/analyze", json={"transcript": "PM: Chốt A."})
    assert response.status_code == 502
    assert "secret" not in response.text
    assert len(calls) == 1


def test_empty_extraction_still_runs_all_stages(mocked_api):
    client, calls, responses = mocked_api
    responses.extend([{"candidate_events": []}, {"threads": [], "relationships": []},
                      {group: [] for group in GROUPS}])
    result = client.post("/analyze", json={"transcript": "Xin chào mọi người."})
    assert result.status_code == 200
    assert result.json() == {group: [] for group in GROUPS}
    assert len(calls) == 3
