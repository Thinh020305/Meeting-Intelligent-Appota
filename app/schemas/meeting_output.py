"""Formal Pydantic v2 contracts. Missing fields and extra fields are errors."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationInfo, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
SegmentId = Annotated[str, StringConstraints(pattern=r"^seg_\d+$")]
Evidence = Annotated[list[SegmentId], Field(min_length=1)]
EventType = Literal[
    "DECISION_PROPOSAL", "DECISION_ACCEPTANCE", "DECISION_REJECTION",
    "TASK_CREATED", "TASK_UPDATED", "TASK_COMPLETED", "PROBLEM_RAISED",
    "PROBLEM_RESOLVED", "REQUEST", "OBSTACLE_RAISED", "OBSTACLE_CLEARED",
    "FEEDBACK", "RISK_RAISED", "UNFINALIZED_CANDIDATE",
]
RelationType = Literal[
    "SAME_TOPIC", "REFERS_TO", "UPDATES", "CONTRADICTS", "ACCEPTS",
    "REJECTS", "SUPERSEDES", "BLOCKS", "RESOLVES", "DEPENDS_ON",
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    @model_validator(mode="after")
    def reject_placeholders(self):
        for name in ("actor", "owner", "deadline", "requester", "target"):
            value = getattr(self, name, None)
            if isinstance(value, str) and value.casefold() in {"unknown", "n/a"}:
                raise ValueError(f"{name} must be null when missing")
        return self


class AnalyzeRequest(Contract):
    transcript: Text


class TranscriptSegment(Contract):
    segment_id: SegmentId
    speaker: Text | None
    timestamp: Text | None
    text: Text


class EvidenceRecord(Contract):
    content: Text
    evidence_segment_ids: Evidence

    @model_validator(mode="after")
    def valid_evidence(self, info: ValidationInfo):
        ids = self.evidence_segment_ids
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate evidence segment IDs")
        known = (info.context or {}).get("segment_ids")
        if known is not None and not set(ids) <= set(known):
            raise ValueError("Evidence references a nonexistent transcript segment")
        return self


class CandidateEvent(EvidenceRecord):
    event_id: Text
    event_type: EventType
    subject: Text
    actor: Text | None
    target: Text | None
    owner: Text | None
    deadline: Text | None
    order: Annotated[int, Field(ge=1)]


class ExtractionOutput(Contract):
    candidate_events: list[CandidateEvent]

    @model_validator(mode="after")
    def valid_chronology(self, info: ValidationInfo):
        events = self.candidate_events
        if len({e.event_id for e in events}) != len(events):
            raise ValueError("event_id must be unique")
        orders = [e.order for e in events]
        if orders != sorted(set(orders)):
            raise ValueError("Events must have unique increasing orders")
        positions = (info.context or {}).get("segment_positions")
        if positions:
            chronology = [max(positions[s] for s in e.evidence_segment_ids) for e in events]
            if chronology != sorted(chronology):
                raise ValueError("Event order contradicts transcript chronology")
        return self


class EventThread(Contract):
    thread_id: Text
    topic: Text
    event_ids: Annotated[list[Text], Field(min_length=1)]


class Relationship(Contract):
    from_event: Text
    to_event: Text
    relation: RelationType
    reason: Text


class RelationshipOutput(Contract):
    threads: list[EventThread]
    relationships: list[Relationship]

    @model_validator(mode="after")
    def valid_references(self, info: ValidationInfo):
        if len({t.thread_id for t in self.threads}) != len(self.threads):
            raise ValueError("thread_id must be unique")
        seen = []
        for thread in self.threads:
            if len(set(thread.event_ids)) != len(thread.event_ids):
                raise ValueError("Duplicate event in a thread")
            seen.extend(thread.event_ids)
        events = (info.context or {}).get("candidate_events")
        if events is None:
            return self
        orders = {e.event_id: e.order for e in events}
        # Each event is retained exactly once, including singleton topics.
        if set(seen) != set(orders) or len(seen) != len(orders):
            raise ValueError("Threads must retain every candidate event exactly once")
        for thread in self.threads:
            values = [orders[e] for e in thread.event_ids]
            if values != sorted(values):
                raise ValueError("Thread events must follow chronology")
        relationships = set()
        for relation in self.relationships:
            if relation.from_event not in orders or relation.to_event not in orders:
                raise ValueError("Relationship references a nonexistent event")
            if relation.from_event == relation.to_event:
                raise ValueError("Self relationship is invalid")
            key = (relation.from_event, relation.to_event, relation.relation)
            if key in relationships:
                raise ValueError("Duplicate relationship")
            relationships.add(key)
        return self


class TaskRecord(EvidenceRecord):
    owner: Text | None
    deadline: Text | None


class RequestRecord(EvidenceRecord):
    requester: Text | None
    target: Text | None


class MeetingOutput(Contract):
    decisions: list[EvidenceRecord]
    tasks: list[TaskRecord]
    problems: list[EvidenceRecord]
    requests: list[RequestRecord]
    obstacles: list[EvidenceRecord]
    feedback: list[EvidenceRecord]
    unfinalized_content: list[EvidenceRecord]
    risks: list[EvidenceRecord]
