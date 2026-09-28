from datetime import datetime, timezone
import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.errors import CandidateNotFoundError
from app.models import Candidate, CandidateStageEvent, Stage, utc_now





def normalize_name(full_name: str) -> str:
    """Normalize a candidate name for future search matching."""

    normalized = unicodedata.normalize("NFKC", full_name)
    normalized = normalized.casefold()
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized.strip()


def create_candidate(
    database: Session,
    full_name: str,
) -> Candidate:
    """Create a candidate and the initial APPLIED audit event."""

    timestamp = utc_now()

    candidate = Candidate(
        full_name=full_name,
        normalized_name=normalize_name(full_name),
        current_stage=Stage.APPLIED,
        current_stage_entered_at=timestamp,
        created_at=timestamp,
    )

    initial_event = CandidateStageEvent(
        candidate=candidate,
        from_stage=None,
        to_stage=Stage.APPLIED,
        occurred_at=timestamp,
    )

    try:
        database.add(candidate)
        database.add(initial_event)
        database.commit()
        database.refresh(candidate)
    except Exception:
        database.rollback()
        raise

    return candidate


PIPELINE_STAGE_ORDER = [
    Stage.APPLIED,
    Stage.SCREENING,
    Stage.INTERVIEW,
    Stage.OFFER,
    Stage.HIRED,
    Stage.REJECTED,
]


def get_pipeline(database: Session) -> dict[Stage, list[Candidate]]:
    """Return candidates grouped by stage in pipeline order."""

    candidates = database.scalars(
        select(Candidate).order_by(
            Candidate.current_stage_entered_at.asc(),
            Candidate.id.asc(),
        )
    ).all()

    grouped_candidates: dict[Stage, list[Candidate]] = {
        stage: [] for stage in PIPELINE_STAGE_ORDER
    }

    for candidate in candidates:
        grouped_candidates[candidate.current_stage].append(candidate)

    return grouped_candidates

def get_candidate_details(
    database: Session,
    candidate_id: int,
) -> Candidate:
    """Return one candidate with ordered stage history."""

    candidate = database.scalar(
        select(Candidate)
        .options(selectinload(Candidate.stage_events))
        .where(Candidate.id == candidate_id)
    )

    if candidate is None:
        raise CandidateNotFoundError(candidate_id)

    return candidate

def calculate_duration_seconds(
    entered_at: datetime,
    now: datetime | None = None,
) -> int:
    """Calculate elapsed seconds from stage entry until now."""

    current_time = now or datetime.now(timezone.utc)

    if entered_at.tzinfo is None:
        entered_at = entered_at.replace(tzinfo=timezone.utc)

    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    duration = current_time - entered_at

    return max(0, int(duration.total_seconds()))