"""Deterministic segmentation; never invent speaker, timestamp or source text."""

import re

from app.schemas.meeting_output import TranscriptSegment

LABEL = re.compile(r"^\s*(seg_\d+)\s*:?[ \t]*(.*)$")
TIME = re.compile(r"^\s*(?:\[(\d{1,2}:\d{2}(?::\d{2})?)\]|(\d{1,2}:\d{2}(?::\d{2})?))\s*")
SPEAKER = re.compile(r"^([^:\[\]\n]{1,80}):\s*(.*)$")


def preprocess(transcript: str) -> list[TranscriptSegment]:
    if not transcript.strip():
        raise ValueError("Transcript must not be blank")
    # The specification uses arrows between labelled segments in its test table.
    lines = re.split(r"\r?\n|\s*→\s*(?=seg_\d+)", transcript)
    pending_id = None
    parsed = []
    for line in lines:
        text = line.strip()
        if not text:
            continue
        label = LABEL.match(text)
        explicit_id = pending_id
        if label:
            if pending_id is not None:
                raise ValueError("Segment label has no content")
            explicit_id, text = label.groups()
        if not text:
            pending_id = explicit_id
            continue
        pending_id = None
        timestamp = speaker = None
        time = TIME.match(text)
        if time:
            timestamp = time.group(1) or time.group(2)
            text = text[time.end():]
        person = SPEAKER.match(text)
        if person:
            speaker, text = person.groups()
            # Also support Nam: [00:01:20] statement.
            time = TIME.match(text)
            if time:
                if timestamp is not None:
                    raise ValueError("Multiple timestamps in one segment")
                timestamp = time.group(1) or time.group(2)
                text = text[time.end():]
        if not text.strip():
            raise ValueError("Segment must contain speech text")
        parsed.append((explicit_id, speaker, timestamp, text))
    if pending_id is not None:
        raise ValueError("Segment label has no content")
    explicit_ids = [row[0] for row in parsed if row[0] is not None]
    if len(set(explicit_ids)) != len(explicit_ids):
        raise ValueError("Duplicate segment IDs")
    reserved = set(explicit_ids)
    counter = 1
    segments = []
    for segment_id, speaker, timestamp, text in parsed:
        if segment_id is None:
            while f"seg_{counter:03d}" in reserved:
                counter += 1
            segment_id = f"seg_{counter:03d}"
            reserved.add(segment_id)
            counter += 1
        segments.append(TranscriptSegment(
            segment_id=segment_id, speaker=speaker, timestamp=timestamp, text=text,
        ))
    return segments
