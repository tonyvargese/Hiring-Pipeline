from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CandidateCreate,
    CandidateResponse,
    CandidateTransitionRequest,
    CandidateTransitionResponse,
    StageEventResponse,
)
from app.services.candidates import create_candidate
from app.services.transitions import (
    CandidateNotFoundError,
    InvalidStageTransitionError,
    StaleStageTransitionError,
    transition_candidate,
)


router = APIRouter(
    prefix="/api/candidates",
    tags=["Candidates"],
)


@router.post(
    "",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_candidate(
    candidate_data: CandidateCreate,
    database: Annotated[Session, Depends(get_db)],
) -> CandidateResponse:
    candidate = create_candidate(
        database=database,
        full_name=candidate_data.full_name,
    )

    return CandidateResponse.model_validate(candidate)


@router.post(
    "/{candidate_id}/transitions",
    response_model=CandidateTransitionResponse,
    status_code=status.HTTP_201_CREATED,
)
def move_candidate(
    candidate_id: int,
    transition_data: CandidateTransitionRequest,
    database: Annotated[Session, Depends(get_db)],
) -> CandidateTransitionResponse:
    try:
        candidate, stage_event = transition_candidate(
            database=database,
            candidate_id=candidate_id,
            from_stage=transition_data.from_stage,
            to_stage=transition_data.to_stage,
        )

    except CandidateNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CANDIDATE_NOT_FOUND",
                "message": (
                    f"Candidate {error.candidate_id} was not found."
                ),
                "hints": [],
            },
        ) from error

    except InvalidStageTransitionError as error:
        allowed_stages = sorted(
            stage.value for stage in error.allowed_stages
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "INVALID_STAGE_TRANSITION",
                "message": (
                    f"A candidate in {error.current_stage.value} cannot "
                    f"move to {error.requested_stage.value}."
                ),
                "hints": [
                    (
                        "Allowed stages: "
                        + ", ".join(allowed_stages)
                        if allowed_stages
                        else "This is a terminal stage."
                    )
                ],
            },
        ) from error

    except StaleStageTransitionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "STALE_STAGE_TRANSITION",
                "message": (
                    "The candidate's stage changed before this request "
                    "was completed."
                ),
                "hints": [
                    (
                        f"Refresh the pipeline. The expected stage was "
                        f"{error.expected_stage.value}."
                    )
                ],
            },
        ) from error

    return CandidateTransitionResponse(
        candidate=CandidateResponse.model_validate(candidate),
        event=StageEventResponse.model_validate(stage_event),
    )