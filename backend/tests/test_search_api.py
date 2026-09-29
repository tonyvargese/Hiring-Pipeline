from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Candidate, CandidateStageEvent, Stage


def search(
    client: TestClient,
    query: str,
):
    return client.get(
        f"/api/search?q={quote(query)}"
    )


def create_candidate(
    client: TestClient,
    full_name: str,
) -> int:
    response = client.post(
        "/api/candidates",
        json={"full_name": full_name},
    )

    assert response.status_code == 201

    return response.json()["id"]


def transition(
    client: TestClient,
    candidate_id: int,
    from_stage: str,
    to_stage: str,
) -> None:
    response = client.post(
        f"/api/candidates/{candidate_id}/transitions",
        json={
            "from_stage": from_stage,
            "to_stage": to_stage,
        },
    )

    assert response.status_code == 201


def test_search_finds_name_with_typo(
    client: TestClient,
) -> None:
    create_candidate(client, "Priya Sharma")
    create_candidate(client, "Arun Nair")

    response = search(client, "Find Priya Sharam")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 1
    assert data["results"][0]["full_name"] == "Priya Sharma"
    assert data["results"][0]["score"] > 60
    assert data["plan"]["name"]["text"] == "priya sharam"


def test_search_finds_current_interview_candidates(
    client: TestClient,
) -> None:
    priya_id = create_candidate(client, "Priya Sharma")
    create_candidate(client, "Arun Nair")

    transition(client, priya_id, "APPLIED", "SCREENING")
    transition(client, priya_id, "SCREENING", "INTERVIEW")

    response = search(
        client,
        "Who's in Interview right now?",
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["full_name"] == (
        "Priya Sharma"
    )


def test_search_finds_candidate_stuck_in_screening(
    client: TestClient,
    test_database: Session,
) -> None:
    arun_id = create_candidate(client, "Arun Nair")

    transition(client, arun_id, "APPLIED", "SCREENING")

    old_timestamp = datetime.now(timezone.utc) - timedelta(days=8)

    candidate = test_database.get(Candidate, arun_id)

    assert candidate is not None

    candidate.current_stage_entered_at = old_timestamp

    latest_event = (
        test_database.query(CandidateStageEvent)
        .filter(
            CandidateStageEvent.candidate_id == arun_id,
            CandidateStageEvent.to_stage == Stage.SCREENING,
        )
        .one()
    )

    latest_event.occurred_at = old_timestamp

    test_database.commit()

    response = search(
        client,
        "Who has been stuck in Screening for more than a week?",
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["full_name"] == "Arun Nair"


def test_historical_search_finds_candidate_who_advanced(
    client: TestClient,
    test_database: Session,
) -> None:
    priya_id = create_candidate(client, "Priya Sharma")

    transition(client, priya_id, "APPLIED", "SCREENING")
    transition(client, priya_id, "SCREENING", "INTERVIEW")
    transition(client, priya_id, "INTERVIEW", "OFFER")

    interview_event = (
        test_database.query(CandidateStageEvent)
        .filter(
            CandidateStageEvent.candidate_id == priya_id,
            CandidateStageEvent.to_stage == Stage.INTERVIEW,
        )
        .one()
    )

    interview_event.occurred_at = datetime.now(timezone.utc)
    test_database.commit()

    response = search(
        client,
        "Who moved to Interview since Monday?",
    )

    assert response.status_code == 200

    result_names = [
        result["full_name"]
        for result in response.json()["results"]
    ]

    assert "Priya Sharma" in result_names
    assert response.json()["results"][0]["current_stage"] == "OFFER"


def test_offer_then_rejected_matches_not_hired_query(
    client: TestClient,
) -> None:
    meera_id = create_candidate(client, "Meera Joseph")

    transitions = [
        ("APPLIED", "SCREENING"),
        ("SCREENING", "INTERVIEW"),
        ("INTERVIEW", "OFFER"),
        ("OFFER", "REJECTED"),
    ]

    for from_stage, to_stage in transitions:
        transition(
            client,
            meera_id,
            from_stage,
            to_stage,
        )

    response = search(
        client,
        "Who reached the Offer stage but didn't get hired?",
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["full_name"] == (
        "Meera Joseph"
    )
    assert response.json()["results"][0]["current_stage"] == (
        "REJECTED"
    )


def test_hired_candidate_does_not_match_offer_not_hired(
    client: TestClient,
) -> None:
    david_id = create_candidate(client, "David Thomas")

    transitions = [
        ("APPLIED", "SCREENING"),
        ("SCREENING", "INTERVIEW"),
        ("INTERVIEW", "OFFER"),
        ("OFFER", "HIRED"),
    ]

    for from_stage, to_stage in transitions:
        transition(
            client,
            david_id,
            from_stage,
            to_stage,
        )

    response = search(
        client,
        "Who reached the Offer stage but didn't get hired?",
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0


def test_search_excludes_rejected_candidates(
    client: TestClient,
) -> None:
    applied_id = create_candidate(client, "Neha Kapoor")
    rejected_id = create_candidate(client, "Arun Nair")

    transition(
        client,
        rejected_id,
        "APPLIED",
        "REJECTED",
    )

    response = search(
        client,
        "Everyone except rejected candidates.",
    )

    assert response.status_code == 200

    result_ids = {
        result["id"]
        for result in response.json()["results"]
    }

    assert applied_id in result_ids
    assert rejected_id not in result_ids


def test_valid_search_with_no_results_returns_200(
    client: TestClient,
) -> None:
    response = search(
        client,
        "Nonexistent Candidate",
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["results"] == []


def test_invalid_search_returns_understandable_error(
    client: TestClient,
) -> None:
    response = search(
        client,
        "<<<123???>>>",
    )

    assert response.status_code == 422

    error = response.json()["detail"]

    assert error["code"] == "INVALID_SEARCH_QUERY"
    assert error["message"]
    assert "hints" in error