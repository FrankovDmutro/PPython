"""Pytest fixtures for database integration tests."""

from pathlib import Path
from typing import Generator
import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from experiment_manager.database import Base, get_engine, get_session_factory
from experiment_manager.models import Experiment, Researcher


@pytest.fixture
def test_engine() -> Generator[Engine, None, None]:
    """Provide an isolated in-memory SQLite engine for tests."""
    engine = get_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def test_session_factory(test_engine: Engine) -> sessionmaker[Session]:
    """Provide a sessionmaker bound to in-memory test engine."""
    return get_session_factory(test_engine)


@pytest.fixture
def test_session(test_session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Provide an isolated transactional session with automatic teardown."""
    session = test_session_factory()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def populated_session(test_session: Session) -> Session:
    """Provide a database session pre-populated with sample researchers and experiments."""
    r1 = Researcher(name="Dr. Frankov", department="Quantum Physics")
    r2 = Researcher(name="Dr. Smith", department="Applied Physics")
    test_session.add_all([r1, r2])
    test_session.flush()

    e1 = Experiment(
        title="Cryogenic Calibration",
        researcher_id=r1.id,
        parameter="temperature",
        result=24.5,
        date="2026-04-01",
        notes="Room temp baseline",
    )
    e2 = Experiment(
        title="Vacuum Depressurization",
        researcher_id=r2.id,
        parameter="pressure",
        result=101325.0,
        date="2026-04-02",
        notes="Standard atmospheric level",
    )
    e3 = Experiment(
        title="Laser Cooling Chamber",
        researcher_id=r1.id,
        parameter="temperature",
        result=-210.0,
        date="2026-04-03",
        notes="Sub-kelvin approach",
    )
    e4 = Experiment(
        title="Superconducting Bias",
        researcher_id=r1.id,
        parameter="voltage",
        result=3.35,
        date="2026-04-04",
        notes="Threshold test",
    )

    test_session.add_all([e1, e2, e3, e4])
    test_session.commit()
    return test_session


@pytest.fixture
def temp_db_file(tmp_path: Path) -> Path:
    """Provide a temporary SQLite file path for DB-API and migration tests."""
    return tmp_path / "test_isolated.db"
