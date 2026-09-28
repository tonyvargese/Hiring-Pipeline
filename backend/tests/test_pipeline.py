from fastapi.testclient import TestClient


EXPECTED_STAGE_ORDER = [
    "APPLIED",
    "SCREENING",
    "INTERVIEW",
    "OFFER",
    "HIRED",
    "REJECTED",
]


def test_pipeline_returns_all_stages_when_empty(
    client: TestClient,
) -> None:
    response = client.get("/api/pipeline")

    assert response.status_code == 200

    stages = response.json()["stages"]

    assert [group["stage"] for group in stages] == EXPECTED_STAGE_ORDER
    assert all(group["candidates"] == [] for group in stages)


def test_pipeline_groups_candidate_under_applied(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/candidates",
        json={"full_name": "Priya Sharma"},
    )

    assert create_response.status_code == 201

    response = client.get("/api/pipeline")

    assert response.status_code == 200

    stages = response.json()["stages"]
    applied_group = stages[0]

    assert applied_group["stage"] == "APPLIED"
    assert len(applied_group["candidates"]) == 1
    assert applied_group["candidates"][0]["full_name"] == "Priya Sharma"

    assert all(
        group["candidates"] == []
        for group in stages[1:]
    )


def test_pipeline_keeps_duplicate_names_as_separate_candidates(
    client: TestClient,
) -> None:
    first_response = client.post(
        "/api/candidates",
        json={"full_name": "Priya Sharma"},
    )

    second_response = client.post(
        "/api/candidates",
        json={"full_name": "Priya Sharma"},
    )

    response = client.get("/api/pipeline")
    applied_candidates = response.json()["stages"][0]["candidates"]

    assert response.status_code == 200
    assert len(applied_candidates) == 2
    assert first_response.json()["id"] != second_response.json()["id"]