from app.schemas.meeting_output import ExtractionOutput, TranscriptSegment
from app.services.llm_client import LLMClient


async def extract(segments: list[TranscriptSegment], client: LLMClient) -> ExtractionOutput:
    return await client.generate(
        "extraction_prompt.txt",
        {"transcript_segments": [s.model_dump() for s in segments]},
        ExtractionOutput,
        context={"segment_ids": {s.segment_id for s in segments},
                 "segment_positions": {s.segment_id: i for i, s in enumerate(segments)}},
    )
