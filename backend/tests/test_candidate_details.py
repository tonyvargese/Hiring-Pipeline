from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.services.candidates import calculate_duration_seconds


def test_candidate_details_include_initial_history(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/candidates",
        json={"full_name": "Priya Sharma"},
    )

    candidate_id = create_response.json()["id"]

    response = client.get(
        f"/api/candidates/{candidate_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == candidate_id
    assert data["full_name"] == "Priya Sharma"
    assert data["current_stage"] == "APPLIED"
    assert data["current_stage_duration_seconds"] >= 0

    assert data["allowed_next_stages"] == [
        "REJECTED",
        "SCREENING",
    ]

    assert len(data["history"]) == 1
    assert data["history"][0]["from_stage"] is None
    assert data["history"][0]["to_stage"] == "APPLIED"


def test_candidate_details_include_complete_ordered_history(
    client: TestClient,
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
    ]

    for from_stage, to_stage in transitions:
        transition_response = client.post(
            f"/api/candidates/{candidate_id}/transitions",
            json={
                "from_stage": from_stage,
                "to_stage": to_stage,
            },
        )

        assert transition_response.status_code == 201

    response = client.get(
        f"/api/candidates/{candidate_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["current_stage"] == "OFFER"

    assert data["allowed_next_stages"] == [
        "HIRED",
        "REJECTED",
    ]

    assert [
        event["to_stage"]
        for event in data["history"]
    ] == [
        "APPLIED",
        "SCREENING",
        "INTERVIEW",
        "OFFER",
    ]

    assert data["history"][0]["from_stage"] is None
    assert data["history"][1]["from_stage"] == "APPLIED"
    assert data["history"][2]["from_stage"] == "SCREENING"
    assert data["history"][3]["from_stage"] == "INTERVIEW"


def test_hired_candidate_has_no_allowed_next_stages(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/candidates",
        json={"full_name": "David Thomas"},
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

    response = client.get(
        f"/api/candidates/{candidate_id}"
    )

    assert response.status_code == 200
    assert response.json()["current_stage"] == "HIRED"
    assert response.json()["allowed_next_stages"] == []


def test_rejected_candidate_has_no_allowed_next_stages(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/candidates",
        json={"full_name": "Arun Nair"},
    )

    candidate_id = create_response.json()["id"]

    rejection_response = client.post(
        f"/api/candidates/{candidate_id}/transitions",
        json={
            "from_stage": "APPLIED",
            "to_stage": "REJECTED",
        },
    )

    assert rejection_response.status_code == 201

    response = client.get(
        f"/api/candidates/{candidate_id}"
    )

    assert response.status_code == 200
    assert response.json()["current_stage"] == "REJECTED"
    assert response.json()["allowed_next_stages"] == []


def test_missing_candidate_details_return_404(
    client: TestClient,
) -> None:
    response = client.get("/api/candidates/999")

    assert response.status_code == 404

    assert response.json()["detail"]["code"] == (
        "CANDIDATE_NOT_FOUND"
    )


def test_current_stage_duration_is_calculated_in_seconds() -> None:
    current_time = datetime(
        2026,
        9,
        28,
        12,
        0,
        tzinfo=timezone.utc,
    )

    entered_at = current_time - timedelta(
        days=2,
        hours=3,
        minutes=4,
    )

    duration = calculate_duration_seconds(
        entered_at=entered_at,
        now=current_time,
    )

    expected_seconds = (
        2 * 24 * 60 * 60
        + 3 * 60 * 60
        + 4 * 60
    )

    assert duration == expected_seconds