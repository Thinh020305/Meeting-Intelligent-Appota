from fastapi import APIRouter, Depends, HTTPException

from app.schemas.meeting_output import AnalyzeRequest, MeetingOutput
from app.services.extraction import extract
from app.services.final_state_resolution import resolve_final_state
from app.services.llm_client import (
    GeminiClient, LLMClient, LLMConfigurationError, LLMProviderError, LLMResponseError,
)
from app.services.preprocessing import preprocess
from app.services.relationship_resolution import resolve_relationships

router = APIRouter()


def get_llm_client() -> LLMClient:
    return GeminiClient()


@router.post("/analyze", response_model=MeetingOutput)
async def analyze(request: AnalyzeRequest, client: LLMClient = Depends(get_llm_client)) -> MeetingOutput:
    try:
        segments = preprocess(request.transcript)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    try:
        extraction = await extract(segments, client)
        relationships = await resolve_relationships(segments, extraction.candidate_events, client)
        return await resolve_final_state(segments, extraction.candidate_events, relationships, client)
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except (LLMProviderError, LLMResponseError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None
