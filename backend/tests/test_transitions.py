import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Candidate, CandidateStageEvent


@pytest.mark.parametrize(
    ("from_stage", "to_stage"),
    [
        ("APPLIED", "SCREENING"),
        ("APPLIED", "REJECTED"),
    ],
)
def test_valid_transition_from_applied(
    client: TestClient,
    test_database: Session,
    from_stage: str,
    to_stage: str,
) -> None:
    create_response = client.post(
        "/api/candidates",
        json={"full_name": "Priya Sharma"},
    )

    candidate_id = create_response.json()["id"]

    response = client.post(
        f"/api/candidates/{candidate_id}/transitions",
        json={
            "from_stage": from_stage,
            "to_stage": to_stage,
        },
    )

    assert response.status_code == 201
    assert response.json()["candidate"]["current_stage"] == to_stage
    assert response.json()["event"]["from_stage"] == from_stage
    assert response.json()["event"]["to_stage"] == to_stage

    events = test_database.scalars(
        select(CandidateStageEvent)
        .where(CandidateStageEvent.candidate_id == candidate_id)
        .order_by(
            CandidateStageEvent.occurred_at,
            CandidateStageEvent.id,
        )
    ).all()

    assert len(events) == 2
    assert events[0].from_stage is None
    assert events[0].to_stage.value == "APPLIED"
    assert events[1].from_stage.value == from_stage
    assert events[1].to_stage.value == to_stage


def test_cannot_skip_a_stage(
    client: TestClient,
    test_database: Session,
) -> None:
    create_response = client.post(
        "/api/candidates",
        json={"full_name": "Priya Sharma"},
    )

    candidate_id = create_response.json()["id"]

    response = client.post(
        f"/api/candidates/{candidate_id}/transitions",
        json={
            "from_stage": "APPLIED",
            "to_stage": "INTERVIEW",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "INVALID_STAGE_TRANSITION"

    candidate = test_database.get(Candidate, candidate_id)

    assert candidate is not None
    assert candidate.current_stage.value == "APPLIED"

    events = test_database.scalars(
        select(CandidateStageEvent).where(
            CandidateStageEvent.candidate_id == candidate_id
        )
    ).all()

    assert len(events) == 1


def test_stale_transition_is_rejected(
    client: TestClient,
    test_database: Session,
) -> None:
    create_response = client.post(
        "/api/candidates",
        json={"full_name": "Priya Sharma"},
    )

    candidate_id = create_response.json()["id"]

    first_response = client.post(
        f"/api/candidates/{candidate_id}/transitions",
        json={
            "from_stage": "APPLIED",
            "to_stage": "SCREENING",
        },
    )

    second_response = client.post(
        f"/api/candidates/{candidate_id}/transitions",
        json={
            "from_stage": "APPLIED",
            "to_stage": "SCREENING",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"]["code"] == (
        "STALE_STAGE_TRANSITION"
    )

    events = test_database.scalars(
        select(CandidateStageEvent).where(
            CandidateStageEvent.candidate_id == candidate_id
        )
    ).all()

    assert len(events) == 2


def test_missing_candidate_returns_404(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/candidates/999/transitions",
        json={
            "from_stage": "APPLIED",
            "to_stage": "SCREENING",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "CANDIDATE_NOT_FOUND"


def test_candidate_can_follow_complete_hiring_path(
    client: TestClient,
    test_database: Session,
) -> None:
    create_response = client.post(
        "/api/candidates",
        json={"full_name": "Priya Sharma"},
    )

    candidate_id = create_response.json()["id"]

    transitions = [
        ("APPLIED", "SCREENING"),
        ("SCREENING", "INTERVIEW"),
        ("INTERVIEW", "OFFER"),
        ("OFFER", "HIRED"),
    ]

    for from_stage, to_stage in transitions:
        response = client.post(
            f"/api/candidates/{candidate_id}/transitions",
            json={
                "from_stage": from_stage,
                "to_stage": to_stage,
            },
        )

        assert response.status_code == 201

    candidate = test_database.get(Candidate, candidate_id)

    assert candidate is not None
    assert candidate.current_stage.value == "HIRED"

    terminal_response = client.post(
        f"/api/candidates/{candidate_id}/transitions",
        json={
            "from_stage": "HIRED",
            "to_stage": "REJECTED",
        },
    )

    assert terminal_response.status_code == 409
    assert terminal_response.json()["detail"]["code"] == (
        "INVALID_STAGE_TRANSITION"
    )

    events = test_database.scalars(
        select(CandidateStageEvent).where(
            CandidateStageEvent.candidate_id == candidate_id
        )
    ).all()

    assert len(events) == 5


def test_candidate_can_be_rejected_before_hired(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/candidates",
        json={"full_name": "Arun Nair"},
    )

    candidate_id = create_response.json()["id"]

    screening_response = client.post(
        f"/api/candidates/{candidate_id}/transitions",
        json={
            "from_stage": "APPLIED",
            "to_stage": "SCREENING",
        },
    )

    assert screening_response.status_code == 201

    rejection_response = client.post(
        f"/api/candidates/{candidate_id}/transitions",
        json={
            "from_stage": "SCREENING",
            "to_stage": "REJECTED",
        },
    )

    assert rejection_response.status_code == 201
    assert rejection_response.json()["candidate"]["current_stage"] == (
        "REJECTED"
    )

    terminal_response = client.post(
        f"/api/candidates/{candidate_id}/transitions",
        json={
            "from_stage": "REJECTED",
            "to_stage": "INTERVIEW",
        },
    )

    assert terminal_response.status_code == 409