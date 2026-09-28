import re
import unicodedata

from sqlalchemy.orm import Session

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