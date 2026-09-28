from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import Stage


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