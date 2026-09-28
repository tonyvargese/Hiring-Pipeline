from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import Stage

from enum import Enum


class CandidateCreate(BaseModel):
    full_name: str = Field(
        min_length=1,
        max_length=150,
        examples=["Priya Sharma"],
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        cleaned_name = " ".join(value.split())

        if not cleaned_name:
            raise ValueError("Candidate name cannot be blank.")

        return cleaned_name


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    current_stage: Stage
    current_stage_entered_at: datetime
    created_at: datetime



class PipelineCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    current_stage: Stage
    current_stage_entered_at: datetime


class PipelineStageResponse(BaseModel):
    stage: Stage
    candidates: list[PipelineCandidateResponse]


class PipelineResponse(BaseModel):
    stages: list[PipelineStageResponse]


class CandidateTransitionRequest(BaseModel):
    from_stage: Stage
    to_stage: Stage


class StageEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_stage: Stage | None
    to_stage: Stage
    occurred_at: datetime


class CandidateTransitionResponse(BaseModel):
    candidate: CandidateResponse
    event: StageEventResponse


class CandidateHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_stage: Stage | None
    to_stage: Stage
    occurred_at: datetime


class CandidateDetailResponse(BaseModel):
    id: int
    full_name: str
    current_stage: Stage
    current_stage_entered_at: datetime
    current_stage_duration_seconds: int
    created_at: datetime
    allowed_next_stages: list[Stage]
    history: list[CandidateHistoryResponse]


class ComparisonOperator(str, Enum):
    GREATER_THAN = "GT"
    GREATER_THAN_OR_EQUAL = "GTE"
    LESS_THAN = "LT"
    LESS_THAN_OR_EQUAL = "LTE"


class NameSearchCondition(BaseModel):
    text: str
    fuzzy: bool = True


class CurrentStageCondition(BaseModel):
    include: list[Stage] = Field(default_factory=list)
    exclude: list[Stage] = Field(default_factory=list)


class StageAgeCondition(BaseModel):
    operator: ComparisonOperator
    seconds: int = Field(gt=0)


class HistoryPredicate(BaseModel):
    stage: Stage
    since: datetime | None = None
    until: datetime | None = None


class SearchPlan(BaseModel):
    name: NameSearchCondition | None = None

    current_stage: CurrentStageCondition = Field(
        default_factory=CurrentStageCondition
    )

    current_stage_age: StageAgeCondition | None = None

    history_predicates: list[HistoryPredicate] = Field(
        default_factory=list
    )

    history_exclusions: list[Stage] = Field(
        default_factory=list
    )


class SearchInterpretation(BaseModel):
    summary: str
    corrections: list[str] = Field(default_factory=list)