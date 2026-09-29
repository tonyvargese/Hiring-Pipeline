import re
from datetime import datetime, timedelta

from app.errors import SearchQueryError
from app.models import Stage
from app.schemas import (
    ComparisonOperator,
    CurrentStageCondition,
    HistoryPredicate,
    NameSearchCondition,
    SearchInterpretation,
    SearchPlan,
    StageAgeCondition,
)


STAGE_WORDS: dict[str, Stage] = {
    "applied": Stage.APPLIED,
    "screening": Stage.SCREENING,
    "interview": Stage.INTERVIEW,
    "offer": Stage.OFFER,
    "hired": Stage.HIRED,
    "rejected": Stage.REJECTED,
}


COMMAND_WORDS = {
    "find",
    "candidate",
    "candidates",
    "person",
    "people",
    "who",
    "whos",
    "whose",
    "show",
    "me",
    "everyone",
}


def normalize_query(query: str) -> str:
    normalized = query.casefold()
    normalized = normalized.replace("who's", "who")
    normalized = normalized.replace("didn't", "did not")
    normalized = normalized.replace("hasn't", "has not")
    normalized = re.sub(r"[?!,.]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized.strip()


def most_recent_monday(now: datetime) -> datetime:
    days_since_monday = now.weekday()

    monday = now - timedelta(days=days_since_monday)

    return monday.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def extract_name_residue(query: str) -> str | None:
    tokens = query.split()

    residue = [
        token
        for token in tokens
        if token not in COMMAND_WORDS
    ]

    if not residue:
        return None

    if not all(token.isalpha() for token in residue):
        raise SearchQueryError(
            code="INVALID_SEARCH_QUERY",
            message="The remaining search text is not a valid name.",
            fragment=" ".join(residue),
            hints=["Try entering a candidate name or a supported filter."],
        )

    if len(residue) > 6:
        raise SearchQueryError(
            code="INVALID_SEARCH_QUERY",
            message="The candidate name contains too many words.",
            fragment=" ".join(residue),
            hints=["Enter a shorter candidate name."],
        )

    return " ".join(residue)


def validate_plan(plan: SearchPlan) -> None:
    included = set(plan.current_stage.include)
    excluded = set(plan.current_stage.exclude)

    contradictions = included.intersection(excluded)

    if contradictions:
        stage_names = ", ".join(
            sorted(stage.value for stage in contradictions)
        )

        raise SearchQueryError(
            code="CONTRADICTORY_SEARCH_FILTERS",
            message=(
                f"The same stage cannot be both included and excluded: "
                f"{stage_names}."
            ),
            hints=["Remove either the inclusion or exclusion condition."],
        )


def parse_search_query(
    raw_query: str,
    now: datetime,
) -> tuple[SearchPlan, SearchInterpretation]:
    query = normalize_query(raw_query)

    if not query:
        raise SearchQueryError(
            code="INVALID_SEARCH_QUERY",
            message="Search query cannot be empty.",
            hints=["Enter a candidate name or search condition."],
        )

    plan = SearchPlan()
    summary_parts: list[str] = []

    # Everyone except rejected candidates
    if "except rejected" in query or "not rejected" in query:
        plan.current_stage.exclude.append(Stage.REJECTED)
        summary_parts.append("excluding currently rejected candidates")

        query = query.replace("except rejected candidates", " ")
        query = query.replace("except rejected", " ")
        query = query.replace("not rejected", " ")
        query = query.replace("everyone", " ")

    # Reached Offer but did not get hired
    if (
        "reached offer" in query
        or "offer stage" in query
    ) and (
        "did not get hired" in query
        or "not hired" in query
    ):
        plan.history_predicates.append(
            HistoryPredicate(stage=Stage.OFFER)
        )
        plan.current_stage.exclude.append(Stage.HIRED)

        summary_parts.append(
            "candidates who reached Offer and are not currently Hired"
        )

        phrases = [
            "who reached the offer stage but did not get hired",
            "reached the offer stage but did not get hired",
            "reached offer but did not get hired",
            "offer stage but did not get hired",
            "reached offer not hired",
        ]

        for phrase in phrases:
            query = query.replace(phrase, " ")

    # Moved to Interview since Monday
    moved_since_match = re.search(
        r"moved to "
        r"(applied|screening|interview|offer|hired|rejected) "
        r"since monday",
        query,
    )

    if moved_since_match:
        stage_word = moved_since_match.group(1)
        stage = STAGE_WORDS[stage_word]
        monday = most_recent_monday(now)

        plan.history_predicates.append(
            HistoryPredicate(
                stage=stage,
                since=monday,
            )
        )

        summary_parts.append(
            f"candidates who entered {stage.value} since "
            f"{monday.isoformat()}"
        )

        query = query.replace(moved_since_match.group(0), " ")

    # Stuck in a stage for more than a week
    duration_match = re.search(
        r"(?:stuck )?in "
        r"(applied|screening|interview|offer|hired|rejected) "
        r"for more than (?:a|one|1) week",
        query,
    )

    if duration_match:
        stage_word = duration_match.group(1)
        stage = STAGE_WORDS[stage_word]

        plan.current_stage.include.append(stage)
        plan.current_stage_age = StageAgeCondition(
            operator=ComparisonOperator.GREATER_THAN,
            seconds=7 * 24 * 60 * 60,
        )

        summary_parts.append(
            f"candidates currently in {stage.value} for more than 7 days"
        )

        query = query.replace(duration_match.group(0), " ")

    # Current stage queries
    current_stage_match = re.search(
        r"(?:currently |right now )?in "
        r"(applied|screening|interview|offer|hired|rejected)"
        r"(?: right now)?",
        query,
    )

    if current_stage_match:
        stage_word = current_stage_match.group(1)
        stage = STAGE_WORDS[stage_word]

        if stage not in plan.current_stage.include:
            plan.current_stage.include.append(stage)

        summary_parts.append(
            f"candidates currently in {stage.value}"
        )

        query = query.replace(current_stage_match.group(0), " ")

    query = re.sub(
    r"\b("
    r"the|stage|but|and|are|is|get|currently|right|now|"
    r"has|have|been|who|candidate|candidates"
    r")\b",
    " ",
    query,
        )
    query = re.sub(r"\s+", " ", query).strip()

    name_residue = extract_name_residue(query)

    if name_residue:
        plan.name = NameSearchCondition(
            text=name_residue,
            fuzzy=True,
        )
        summary_parts.append(
            f'name approximately matching "{name_residue}"'
        )

    validate_plan(plan)

    has_condition = bool(
        plan.name
        or plan.current_stage.include
        or plan.current_stage.exclude
        or plan.current_stage_age
        or plan.history_predicates
        or plan.history_exclusions
    )

    if not has_condition:
        raise SearchQueryError(
            code="INVALID_SEARCH_QUERY",
            message="The search query did not contain a supported condition.",
            fragment=raw_query,
            hints=[
                "Try a candidate name.",
                "Try 'in Interview right now'.",
                "Try 'Screening for more than a week'.",
            ],
        )

    interpretation = SearchInterpretation(
        summary="; ".join(summary_parts),
        corrections=[],
    )

    return plan, interpretation