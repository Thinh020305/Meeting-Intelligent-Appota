from app.schemas.meeting_output import CandidateEvent, MeetingOutput, RelationshipOutput, TranscriptSegment
from app.services.llm_client import LLMClient


async def resolve_final_state(segments: list[TranscriptSegment], events: list[CandidateEvent],
                              relationships: RelationshipOutput, client: LLMClient) -> MeetingOutput:
    return await client.generate(
        "final_state_prompt.txt",
        {"transcript_segments": [s.model_dump() for s in segments],
         "candidate_events": [e.model_dump() for e in events],
         "event_threads": [t.model_dump() for t in relationships.threads],
         "relationships": [r.model_dump() for r in relationships.relationships]},
        MeetingOutput, context={"segment_ids": {s.segment_id for s in segments}},
    )
