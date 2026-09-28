from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.errors import SearchQueryError
from app.models import Stage
from app.schemas import ComparisonOperator
from app.search.parser import parse_search_query


TEST_TIMEZONE = ZoneInfo("Asia/Kolkata")

FIXED_NOW = datetime(
    2026,
    9,
    28,
    12,
    0,
    tzinfo=TEST_TIMEZONE,
)


def test_parses_typo_tolerant_name_query() -> None:
    plan, interpretation = parse_search_query(
        "Find Priya Sharam",
        now=FIXED_NOW,
    )

    assert plan.name is not None
    assert plan.name.text == "priya sharam"
    assert plan.name.fuzzy is True
    assert "priya sharam" in interpretation.summary


def test_parses_current_interview_query() -> None:
    plan, _ = parse_search_query(
        "Who's in Interview right now?",
        now=FIXED_NOW,
    )

    assert plan.current_stage.include == [Stage.INTERVIEW]
    assert plan.current_stage.exclude == []
    assert plan.name is None


def test_parses_screening_duration_query() -> None:
    plan, _ = parse_search_query(
        "Who has been stuck in Screening for more than a week?",
        now=FIXED_NOW,
    )

    assert plan.current_stage.include == [Stage.SCREENING]
    assert plan.current_stage_age is not None
    assert plan.current_stage_age.operator == (
        ComparisonOperator.GREATER_THAN
    )
    assert plan.current_stage_age.seconds == 604800


def test_parses_interview_since_monday_query() -> None:
    plan, _ = parse_search_query(
        "Who moved to Interview since Monday?",
        now=FIXED_NOW,
    )

    assert len(plan.history_predicates) == 1

    predicate = plan.history_predicates[0]

    assert predicate.stage == Stage.INTERVIEW
    assert predicate.since == datetime(
        2026,
        9,
        28,
        0,
        0,
        tzinfo=TEST_TIMEZONE,
    )


def test_parses_offer_not_hired_query() -> None:
    plan, _ = parse_search_query(
        "Who reached the Offer stage but didn't get hired?",
        now=FIXED_NOW,
    )

    assert len(plan.history_predicates) == 1
    assert plan.history_predicates[0].stage == Stage.OFFER
    assert plan.current_stage.exclude == [Stage.HIRED]


def test_parses_excluding_rejected_query() -> None:
    plan, _ = parse_search_query(
        "Everyone except rejected candidates.",
        now=FIXED_NOW,
    )

    assert plan.current_stage.exclude == [Stage.REJECTED]
    assert plan.name is None


def test_unrecognized_alphabetic_text_becomes_name_query() -> None:
    plan, _ = parse_search_query(
        "Asdkjh",
        now=FIXED_NOW,
    )

    assert plan.name is not None
    assert plan.name.text == "asdkjh"


def test_empty_query_is_invalid() -> None:
    with pytest.raises(SearchQueryError) as error:
        parse_search_query(
            "   ",
            now=FIXED_NOW,
        )

    assert error.value.code == "INVALID_SEARCH_QUERY"


def test_invalid_punctuation_query_is_rejected() -> None:
    with pytest.raises(SearchQueryError) as error:
        parse_search_query(
            "<<<123???>>>",
            now=FIXED_NOW,
        )

    assert error.value.code == "INVALID_SEARCH_QUERY"