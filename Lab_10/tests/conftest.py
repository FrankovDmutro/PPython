"""Pytest fixtures for production experiment registry tests."""

from __future__ import annotations

import datetime as dt
from collections.abc import Generator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from experiment_registry.api import app
from experiment_registry.database import get_db
from experiment_registry.models import Base, Experiment, Researcher

# Isolated in-memory SQLite database
TEST_DB_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provide a clean in-memory database session for each test function."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[AsyncClient, None, None]:
    """Provide an asynchronous HTTP test client bound to in-memory test database."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async_client = AsyncClient(transport=transport, base_url="http://testserver")

    yield async_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_researcher(db_session: Session) -> Researcher:
    """Fixture providing a persisted sample researcher."""
    r = Researcher(name="Олександр Франков", department="Кафедра кібербезпеки")
    db_session.add(r)
    db_session.commit()
    db_session.refresh(r)
    return r


@pytest.fixture
def sample_experiments(db_session: Session, sample_researcher: Researcher) -> list[Experiment]:
    """Fixture providing sample experiments linked to sample researcher."""
    exps = [
        Experiment(
            title="Експеримент 1: Температура",
            parameter="Температура (°C)",
            result=100.5,
            date=dt.date(2026, 3, 1),
            researcher_id=sample_researcher.id,
        ),
        Experiment(
            title="Експеримент 2: Температура",
            parameter="Температура (°C)",
            result=150.0,
            date=dt.date(2026, 3, 2),
            researcher_id=sample_researcher.id,
        ),
        Experiment(
            title="Експеримент 3: Тиск",
            parameter="Тиск (кПа)",
            result=200.0,
            date=dt.date(2026, 3, 3),
            researcher_id=sample_researcher.id,
        ),
    ]
    db_session.add_all(exps)
    db_session.commit()
    return exps
