from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    PipelineCandidateResponse,
    PipelineResponse,
    PipelineStageResponse,
)
from app.services.candidates import get_pipeline


router = APIRouter(
    prefix="/api/pipeline",
    tags=["Pipeline"],
)


@router.get(
    "",
    response_model=PipelineResponse,
)
def read_pipeline(
    database: Annotated[Session, Depends(get_db)],
) -> PipelineResponse:
    grouped_candidates = get_pipeline(database)

    return PipelineResponse(
        stages=[
            PipelineStageResponse(
                stage=stage,
                candidates=[
                    PipelineCandidateResponse.model_validate(candidate)
                    for candidate in candidates
                ],
            )
            for stage, candidates in grouped_candidates.items()
        ]
    )