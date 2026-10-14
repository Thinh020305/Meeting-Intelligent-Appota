from app.schemas.meeting_output import CandidateEvent, RelationshipOutput, TranscriptSegment
from app.services.llm_client import LLMClient


async def resolve_relationships(segments: list[TranscriptSegment],
                                events: list[CandidateEvent], client: LLMClient) -> RelationshipOutput:
    return await client.generate(
        "relationship_prompt.txt",
        {"transcript_segments": [s.model_dump() for s in segments],
         "candidate_events": [e.model_dump() for e in events]},
        RelationshipOutput, context={"candidate_events": events},
    )
