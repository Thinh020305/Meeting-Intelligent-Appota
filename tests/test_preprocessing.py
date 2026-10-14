import pytest

from app.services.preprocessing import preprocess


def test_speaker_timestamps_and_original_text():
    segments = preprocess("[00:01:20] Nam: API  login đang lỗi.\nLan: [00:02:30] Đã fix xong.\nKhông có metadata.")
    assert [s.segment_id for s in segments] == ["seg_001", "seg_002", "seg_003"]
    assert segments[0].speaker == "Nam"
    assert segments[0].timestamp == "00:01:20"
    assert segments[0].text == "API  login đang lỗi."
    assert segments[1].timestamp == "00:02:30"
    assert segments[2].speaker is None and segments[2].timestamp is None


def test_labelled_segments_and_arrows():
    segments = preprocess("seg_010:\nNam: Đề xuất A. → seg_020 PM: Chốt B.")
    assert [s.segment_id for s in segments] == ["seg_010", "seg_020"]
    assert [s.speaker for s in segments] == ["Nam", "PM"]


def test_auto_ids_do_not_collide_with_explicit_ids():
    segments = preprocess("Nội dung đầu.\nseg_001 Nam: Nội dung sau.")
    assert [s.segment_id for s in segments] == ["seg_002", "seg_001"]


@pytest.mark.parametrize("text", ["", " \n ", "seg_001:", "Nam:",
                                  "seg_001 Nam: A\nseg_001 Lan: B", "seg_001:\nseg_002: B"])
def test_invalid_transcript(text):
    with pytest.raises(ValueError):
        preprocess(text)
