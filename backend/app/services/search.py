from datetime import datetime, timedelta, timezone

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Candidate, CandidateStageEvent
from app.schemas import (
    ComparisonOperator,
    SearchCandidateResponse,
    SearchPlan,
)


MINIMUM_NAME_SCORE = 60.0


def as_utc(value: datetime) -> datetime:
    """Return an aware UTC datetime.

    SQLite may return naive datetime values, so naive values are treated
    as UTC because application timestamps are stored in UTC.
    """

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def matches_stage_age(
    candidate: Candidate,
    plan: SearchPlan,
    now: datetime,
) -> bool:
    condition = plan.current_stage_age

    if condition is None:
        return True

    entered_at = as_utc(candidate.current_stage_entered_at)
    current_time = as_utc(now)
    elapsed_seconds = (current_time - entered_at).total_seconds()

    if condition.operator == ComparisonOperator.GREATER_THAN:
        return elapsed_seconds > condition.seconds

    if condition.operator == ComparisonOperator.GREATER_THAN_OR_EQUAL:
        return elapsed_seconds >= condition.seconds

    if condition.operator == ComparisonOperator.LESS_THAN:
        return elapsed_seconds < condition.seconds

    if condition.operator == ComparisonOperator.LESS_THAN_OR_EQUAL:
        return elapsed_seconds <= condition.seconds

    return False


def event_matches_predicate(
    event: CandidateStageEvent,
    predicate,
) -> bool:
    if event.to_stage != predicate.stage:
        return False

    occurred_at = as_utc(event.occurred_at)

    if predicate.since is not None:
        since = as_utc(predicate.since)

        if occurred_at < since:
            return False

    if predicate.until is not None:
        until = as_utc(predicate.until)

        if occurred_at > until:
            return False

    return True


def matches_history(
    candidate: Candidate,
    plan: SearchPlan,
) -> bool:
    for predicate in plan.history_predicates:
        predicate_matched = any(
            event_matches_predicate(event, predicate)
            for event in candidate.stage_events
        )

        if not predicate_matched:
            return False

    for excluded_stage in plan.history_exclusions:
        reached_excluded_stage = any(
            event.to_stage == excluded_stage
            for event in candidate.stage_events
        )

        if reached_excluded_stage:
            return False

    return True


def calculate_name_score(
    candidate: Candidate,
    plan: SearchPlan,
) -> float | None:
    if plan.name is None:
        return None

    query_name = plan.name.text.casefold().strip()

    if candidate.normalized_name == query_name:
        return 100.0

    return float(
        fuzz.WRatio(
            query_name,
            candidate.normalized_name,
        )
    )


def get_matching_history_time(
    candidate: Candidate,
    plan: SearchPlan,
) -> datetime | None:
    """Return the newest event matching the historical predicates."""

    matching_times: list[datetime] = []

    for predicate in plan.history_predicates:
        for event in candidate.stage_events:
            if event_matches_predicate(event, predicate):
                matching_times.append(as_utc(event.occurred_at))

    if not matching_times:
        return None

    return max(matching_times)


def execute_search(
    database: Session,
    plan: SearchPlan,
    now: datetime,
) -> list[SearchCandidateResponse]:
    """Execute a validated search plan and rank matching candidates."""

    candidates = database.scalars(
        select(Candidate)
        .options(selectinload(Candidate.stage_events))
        .order_by(Candidate.id)
    ).all()

    matches: list[tuple[Candidate, float | None]] = []

    included_stages = set(plan.current_stage.include)
    excluded_stages = set(plan.current_stage.exclude)

    for candidate in candidates:
        if (
            included_stages
            and candidate.current_stage not in included_stages
        ):
            continue

        if candidate.current_stage in excluded_stages:
            continue

        if not matches_stage_age(candidate, plan, now):
            continue

        if not matches_history(candidate, plan):
            continue

        name_score = calculate_name_score(candidate, plan)

        if (
            plan.name is not None
            and (
                name_score is None
                or name_score < MINIMUM_NAME_SCORE
            )
        ):
            continue

        matches.append((candidate, name_score))

    if plan.name is not None:
        matches.sort(
            key=lambda item: (
                -(item[1] or 0),
                item[0].full_name.casefold(),
                item[0].id,
            )
        )

    elif plan.current_stage_age is not None:
        matches.sort(
            key=lambda item: (
                as_utc(item[0].current_stage_entered_at),
                item[0].id,
            )
        )

    elif plan.history_predicates:
        matches.sort(
            key=lambda item: (
                get_matching_history_time(item[0], plan)
                or datetime.min.replace(tzinfo=timezone.utc),
                item[0].id,
            ),
            reverse=True,
        )

    else:
        matches.sort(
            key=lambda item: (
                item[0].full_name.casefold(),
                item[0].id,
            )
        )

    return [
        SearchCandidateResponse(
            id=candidate.id,
            full_name=candidate.full_name,
            current_stage=candidate.current_stage,
            current_stage_entered_at=candidate.current_stage_entered_at,
            score=score,
        )
        for candidate, score in matches
    ]