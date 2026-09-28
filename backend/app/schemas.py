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