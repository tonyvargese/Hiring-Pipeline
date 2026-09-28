from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Candidate, CandidateStageEvent, Stage, utc_now


ALLOWED_TRANSITIONS: dict[Stage, set[Stage]] = {
    Stage.APPLIED: {
        Stage.SCREENING,
        Stage.REJECTED,
    },
    Stage.SCREENING: {
        Stage.INTERVIEW,
        Stage.REJECTED,
    },
    Stage.INTERVIEW: {
        Stage.OFFER,
        Stage.REJECTED,
    },
    Stage.OFFER: {
        Stage.HIRED,
        Stage.REJECTED,
    },
    Stage.HIRED: set(),
    Stage.REJECTED: set(),
}


@dataclass
class CandidateNotFoundError(Exception):
    candidate_id: int


@dataclass
class InvalidStageTransitionError(Exception):
    current_stage: Stage
    requested_stage: Stage
    allowed_stages: set[Stage]


@dataclass
class StaleStageTransitionError(Exception):
    expected_stage: Stage


def transition_candidate(
    database: Session,
    candidate_id: int,
    from_stage: Stage,
    to_stage: Stage,
) -> tuple[Candidate, CandidateStageEvent]:
    """Move a candidate to an allowed stage and append an audit event."""

    candidate = database.scalar(
        select(Candidate).where(
            Candidate.id == candidate_id,
        )
    )

    if candidate is None:
        raise CandidateNotFoundError(candidate_id)

    if candidate.current_stage != from_stage:
        raise StaleStageTransitionError(
        expected_stage=from_stage,
        )
    allowed_stages = ALLOWED_TRANSITIONS[candidate.current_stage]

    if to_stage not in allowed_stages:
        raise InvalidStageTransitionError(
        current_stage=candidate.current_stage,
        requested_stage=to_stage,
        allowed_stages=allowed_stages,
        )
    

    timestamp = utc_now()

    try:
        update_result = database.execute(
            update(Candidate)
            .where(
                Candidate.id == candidate_id,
                Candidate.current_stage == from_stage,
            )
            .values(
                current_stage=to_stage,
                current_stage_entered_at=timestamp,
            )
            .execution_options(synchronize_session=False)
        )

        if update_result.rowcount != 1:
            database.rollback()

            raise StaleStageTransitionError(
                expected_stage=from_stage,
            )

        stage_event = CandidateStageEvent(
            candidate_id=candidate_id,
            from_stage=from_stage,
            to_stage=to_stage,
            occurred_at=timestamp,
        )

        database.add(stage_event)
        database.commit()

        database.refresh(candidate)
        database.refresh(stage_event)

        return candidate, stage_event

    except (
        CandidateNotFoundError,
        InvalidStageTransitionError,
        StaleStageTransitionError,
    ):
        raise

    except Exception:
        database.rollback()
        raise