from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Candidate, CandidateStageEvent, Stage


def test_candidate_and_initial_event_can_be_persisted() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        candidate = Candidate(
            full_name="Priya Sharma",
            normalized_name="priya sharma",
            current_stage=Stage.APPLIED,
        )

        session.add(candidate)
        session.flush()

        initial_event = CandidateStageEvent(
            candidate_id=candidate.id,
            from_stage=None,
            to_stage=Stage.APPLIED,
            occurred_at=candidate.current_stage_entered_at,
        )

        session.add(initial_event)
        session.commit()

        saved_candidate = session.scalar(
            select(Candidate).where(
                Candidate.id == candidate.id,
            )
        )

        assert saved_candidate is not None
        assert saved_candidate.current_stage == Stage.APPLIED
        assert len(saved_candidate.stage_events) == 1
        assert saved_candidate.stage_events[0].from_stage is None
        assert saved_candidate.stage_events[0].to_stage == Stage.APPLIED