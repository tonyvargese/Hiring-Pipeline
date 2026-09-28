from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    """Return the current time in UTC."""

    return datetime.now(timezone.utc)


class Stage(str, Enum):
    APPLIED = "APPLIED"
    SCREENING = "SCREENING"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    HIRED = "HIRED"
    REJECTED = "REJECTED"


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    normalized_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    current_stage: Mapped[Stage] = mapped_column(
        SqlEnum(
            Stage,
            native_enum=False,
            validate_strings=True,
            length=20,
        ),
        nullable=False,
        default=Stage.APPLIED,
        index=True,
    )

    current_stage_entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    stage_events: Mapped[list["CandidateStageEvent"]] = relationship(
        back_populates="candidate",
        order_by=lambda: (
            CandidateStageEvent.occurred_at,
            CandidateStageEvent.id,
        ),
        passive_deletes=True,
    )


class CandidateStageEvent(Base):
    __tablename__ = "candidate_stage_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    candidate_id: Mapped[int] = mapped_column(
        ForeignKey(
            "candidates.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    from_stage: Mapped[Stage | None] = mapped_column(
        SqlEnum(
            Stage,
            native_enum=False,
            validate_strings=True,
            length=20,
        ),
        nullable=True,
    )

    to_stage: Mapped[Stage] = mapped_column(
        SqlEnum(
            Stage,
            native_enum=False,
            validate_strings=True,
            length=20,
        ),
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    candidate: Mapped["Candidate"] = relationship(
        back_populates="stage_events",
    )

    __table_args__ = (
        Index(
            "ix_stage_events_candidate_occurred_at",
            "candidate_id",
            "occurred_at",
        ),
    )
