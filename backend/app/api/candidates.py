from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CandidateCreate,
    CandidateDetailResponse,
    CandidateHistoryResponse,
    CandidateResponse,
    CandidateTransitionRequest,
    CandidateTransitionResponse,
    StageEventResponse,
)
from app.services.candidates import (
    calculate_duration_seconds,
    create_candidate,
    get_candidate_details,
)
from app.services.transitions import (
    CandidateNotFoundError,
    InvalidStageTransitionError,
    StaleStageTransitionError,
    transition_candidate,
)

from app.services.transitions import (
    ALLOWED_TRANSITIONS,
    InvalidStageTransitionError,
    StaleStageTransitionError,
)
from app.errors import CandidateNotFoundError


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


@router.get(
    "/{candidate_id}",
    response_model=CandidateDetailResponse,
)
def read_candidate(
    candidate_id: int,
    database: Annotated[Session, Depends(get_db)],
) -> CandidateDetailResponse:
    try:
        candidate = get_candidate_details(
            database=database,
            candidate_id=candidate_id,
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

    allowed_next_stages = sorted(
        ALLOWED_TRANSITIONS[candidate.current_stage],
        key=lambda stage: stage.value,
    )

    return CandidateDetailResponse(
        id=candidate.id,
        full_name=candidate.full_name,
        current_stage=candidate.current_stage,
        current_stage_entered_at=candidate.current_stage_entered_at,
        current_stage_duration_seconds=calculate_duration_seconds(
            candidate.current_stage_entered_at
        ),
        created_at=candidate.created_at,
        allowed_next_stages=allowed_next_stages,
        history=[
            CandidateHistoryResponse.model_validate(event)
            for event in candidate.stage_events
        ],)
 