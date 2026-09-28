from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CandidateCreate, CandidateResponse
from app.services.candidates import create_candidate


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