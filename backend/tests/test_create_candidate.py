from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Candidate, CandidateStageEvent, Stage


@pytest.fixture
def test_database() -> Generator[Session, None, None]:
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def enable_foreign_keys(
        database_connection,
        connection_record,
    ) -> None:
        cursor = database_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=test_engine)

    TestSession = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    database = TestSession()

    try:
        yield database
    finally:
        database.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture
def client(
    test_database: Session,
) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield test_database

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_create_candidate_adds_initial_applied_event(
    client: TestClient,
    test_database: Session,
) -> None:
    response = client.post(
        "/api/candidates",
        json={"full_name": "Priya Sharma"},
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["full_name"] == "Priya Sharma"
    assert response_data["current_stage"] == "APPLIED"

    candidate = test_database.scalar(
        select(Candidate).where(
            Candidate.id == response_data["id"],
        )
    )

    assert candidate is not None
    assert candidate.normalized_name == "priya sharma"
    assert candidate.current_stage == Stage.APPLIED

    events = test_database.scalars(
        select(CandidateStageEvent).where(
            CandidateStageEvent.candidate_id == candidate.id,
        )
    ).all()

    assert len(events) == 1

    initial_event = events[0]

    assert initial_event.from_stage is None
    assert initial_event.to_stage == Stage.APPLIED
    assert initial_event.occurred_at == candidate.current_stage_entered_at


def test_create_candidate_normalizes_whitespace(
    client: TestClient,
    test_database: Session,
) -> None:
    response = client.post(
        "/api/candidates",
        json={"full_name": "  Priya   Sharma  "},
    )

    assert response.status_code == 201
    assert response.json()["full_name"] == "Priya Sharma"

    candidate = test_database.scalar(select(Candidate))

    assert candidate is not None
    assert candidate.normalized_name == "priya sharma"


def test_create_candidate_rejects_blank_name(
    client: TestClient,
    test_database: Session,
) -> None:
    response = client.post(
        "/api/candidates",
        json={"full_name": "     "},
    )

    assert response.status_code == 422

    candidate_count = test_database.scalar(
        select(func.count()).select_from(Candidate)
    )

    event_count = test_database.scalar(
        select(func.count()).select_from(CandidateStageEvent)
    )

    assert candidate_count == 0
    assert event_count == 0


def test_duplicate_candidate_names_are_allowed(
    client: TestClient,
    test_database: Session,
) -> None:
    first_response = client.post(
        "/api/candidates",
        json={"full_name": "Priya Sharma"},
    )

    second_response = client.post(
        "/api/candidates",
        json={"full_name": "Priya Sharma"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json()["id"] != second_response.json()["id"]

    candidate_count = test_database.scalar(
        select(func.count()).select_from(Candidate)
    )

    event_count = test_database.scalar(
        select(func.count()).select_from(CandidateStageEvent)
    )

    assert candidate_count == 2
    assert event_count == 2