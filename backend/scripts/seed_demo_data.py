from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database import Base, engine
from app.models import Candidate, CandidateStageEvent, Stage


APPLICATION_TIMEZONE = ZoneInfo("Asia/Kolkata")


def most_recent_monday(now: datetime) -> datetime:
    """Return the most recent Monday at 00:00 in the same timezone."""

    monday = now - timedelta(days=now.weekday())

    return monday.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def as_utc(value: datetime) -> datetime:
    """Convert an aware datetime to UTC."""

    return value.astimezone(timezone.utc)


def add_candidate_with_history(
    database: Session,
    full_name: str,
    history: list[tuple[Stage | None, Stage, datetime]],
) -> Candidate:
    """Create a candidate from an explicit ordered stage history."""

    if not history:
        raise ValueError("Candidate history cannot be empty.")

    first_from_stage, first_to_stage, first_timestamp = history[0]

    if first_from_stage is not None or first_to_stage != Stage.APPLIED:
        raise ValueError(
            "Candidate history must begin with creation in APPLIED."
        )

    current_stage = history[-1][1]
    current_stage_entered_at = history[-1][2]

    candidate = Candidate(
        full_name=full_name,
        normalized_name=" ".join(full_name.casefold().split()),
        current_stage=current_stage,
        current_stage_entered_at=current_stage_entered_at,
        created_at=first_timestamp,
    )

    database.add(candidate)
    database.flush()

    for from_stage, to_stage, occurred_at in history:
        database.add(
            CandidateStageEvent(
                candidate_id=candidate.id,
                from_stage=from_stage,
                to_stage=to_stage,
                occurred_at=occurred_at,
            )
        )

    return candidate


def seed_demo_data() -> None:
    """Reset and populate deterministic demonstration data."""

    Base.metadata.create_all(bind=engine)

    now_local = datetime.now(APPLICATION_TIMEZONE)
    monday_local = most_recent_monday(now_local)

    # Keep Priya's Interview transition after the most recent Monday.
    priya_interview_local = monday_local + timedelta(hours=10)

    # If the script runs early on Monday, avoid using a future timestamp.
    if priya_interview_local > now_local:
        priya_interview_local = now_local - timedelta(minutes=30)

    with Session(engine) as database:
        try:
            # Events must be deleted first because they reference candidates.
            database.execute(delete(CandidateStageEvent))
            database.execute(delete(Candidate))

            add_candidate_with_history(
                database=database,
                full_name="Priya Sharma",
                history=[
                    (
                        None,
                        Stage.APPLIED,
                        as_utc(now_local - timedelta(days=14)),
                    ),
                    (
                        Stage.APPLIED,
                        Stage.SCREENING,
                        as_utc(now_local - timedelta(days=9)),
                    ),
                    (
                        Stage.SCREENING,
                        Stage.INTERVIEW,
                        as_utc(priya_interview_local),
                    ),
                ],
            )

            add_candidate_with_history(
                database=database,
                full_name="Arun Nair",
                history=[
                    (
                        None,
                        Stage.APPLIED,
                        as_utc(now_local - timedelta(days=16)),
                    ),
                    (
                        Stage.APPLIED,
                        Stage.SCREENING,
                        as_utc(now_local - timedelta(days=8, hours=2)),
                    ),
                ],
            )

            add_candidate_with_history(
                database=database,
                full_name="Meera Joseph",
                history=[
                    (
                        None,
                        Stage.APPLIED,
                        as_utc(now_local - timedelta(days=30)),
                    ),
                    (
                        Stage.APPLIED,
                        Stage.SCREENING,
                        as_utc(now_local - timedelta(days=25)),
                    ),
                    (
                        Stage.SCREENING,
                        Stage.INTERVIEW,
                        as_utc(now_local - timedelta(days=20)),
                    ),
                    (
                        Stage.INTERVIEW,
                        Stage.OFFER,
                        as_utc(now_local - timedelta(days=12)),
                    ),
                    (
                        Stage.OFFER,
                        Stage.REJECTED,
                        as_utc(now_local - timedelta(days=5)),
                    ),
                ],
            )

            add_candidate_with_history(
                database=database,
                full_name="David Thomas",
                history=[
                    (
                        None,
                        Stage.APPLIED,
                        as_utc(now_local - timedelta(days=35)),
                    ),
                    (
                        Stage.APPLIED,
                        Stage.SCREENING,
                        as_utc(now_local - timedelta(days=30)),
                    ),
                    (
                        Stage.SCREENING,
                        Stage.INTERVIEW,
                        as_utc(now_local - timedelta(days=24)),
                    ),
                    (
                        Stage.INTERVIEW,
                        Stage.OFFER,
                        as_utc(now_local - timedelta(days=16)),
                    ),
                    (
                        Stage.OFFER,
                        Stage.HIRED,
                        as_utc(now_local - timedelta(days=10)),
                    ),
                ],
            )

            add_candidate_with_history(
                database=database,
                full_name="Neha Kapoor",
                history=[
                    (
                        None,
                        Stage.APPLIED,
                        as_utc(now_local - timedelta(days=2)),
                    ),
                ],
            )

            add_candidate_with_history(
                database=database,
                full_name="Ravi Menon",
                history=[
                    (
                        None,
                        Stage.APPLIED,
                        as_utc(now_local - timedelta(days=10)),
                    ),
                    (
                        Stage.APPLIED,
                        Stage.REJECTED,
                        as_utc(now_local - timedelta(days=6)),
                    ),
                ],
            )

            database.commit()

        except Exception:
            database.rollback()
            raise

    print("Demo data seeded successfully.")
    print("Expected demonstration results:")
    print("- 'Priya Sharam' -> Priya Sharma")
    print("- 'in Interview right now' -> Priya Sharma")
    print("- 'Screening for more than a week' -> Arun Nair")
    print("- 'moved to Interview since Monday' -> Priya Sharma")
    print("- 'reached Offer but did not get hired' -> Meera Joseph")
    print("- 'everyone except rejected' -> excludes Meera and Ravi")


if __name__ == "__main__":
    seed_demo_data()