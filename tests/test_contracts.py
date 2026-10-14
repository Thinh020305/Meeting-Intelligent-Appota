import copy

import pytest
from pydantic import ValidationError

from app.schemas.meeting_output import MeetingOutput
from tests.sample_transcripts.cases import CASES


@pytest.mark.parametrize("value", ["", " ", "unknown", "N/A", 3])
@pytest.mark.parametrize("field", ["owner", "deadline"])
def test_missing_task_metadata_must_be_null(field, value):
    data = copy.deepcopy(CASES[4]["final"])
    data["tasks"][0][field] = value
    with pytest.raises(ValidationError):
        MeetingOutput.model_validate(data)


@pytest.mark.parametrize("field", ["requester", "target"])
def test_request_nullable_fields_are_required(field):
    data = copy.deepcopy(CASES[7]["final"])
    del data["requests"][0][field]
    with pytest.raises(ValidationError):
        MeetingOutput.model_validate(data)


@pytest.mark.parametrize("ids", [[], ["seg_001", "seg_001"], ["not-a-segment"]])
def test_evidence_is_nonempty_unique_and_formatted(ids):
    data = copy.deepcopy(CASES[0]["final"])
    data["decisions"][0]["evidence_segment_ids"] = ids
    with pytest.raises(ValidationError):
        MeetingOutput.model_validate(data)
