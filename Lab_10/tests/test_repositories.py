"""Unit tests for ResearcherRepository and ExperimentRepository."""

from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from experiment_registry.models import Experiment, Researcher
from experiment_registry.repositories import ExperimentRepository, ResearcherRepository
from experiment_registry.schemas import ExperimentCreate, ExperimentUpdate, ResearcherCreate


def test_researcher_repository(db_session: Session) -> None:
    """Verify repository operations for Researcher."""
    repo = ResearcherRepository(db_session)

    # Create
    created = repo.create(ResearcherCreate(name="Максим Бондаренко", department="Фізика"))
    assert created.id > 0
    assert created.name == "Максим Бондаренко"

    # Get by ID
    found = repo.get_by_id(created.id)
    assert found is not None
    assert found.name == created.name

    # List
    all_r = repo.get_all()
    assert len(all_r) >= 1

    # Delete
    deleted = repo.delete(created.id)
    assert deleted is True
    assert repo.get_by_id(created.id) is None


def test_experiment_repository(db_session: Session, sample_researcher: Researcher) -> None:
    """Verify repository operations for Experiment."""
    repo = ExperimentRepository(db_session)

    # Create
    exp = repo.create(
        ExperimentCreate(
            title="Оптичний спектр",
            parameter="Спектр",
            result=540.2,
            date=dt.date(2026, 4, 1),
            researcher_id=sample_researcher.id,
        )
    )
    assert exp.id > 0

    # Update
    updated = repo.update(exp.id, ExperimentUpdate(result=550.0))
    assert updated is not None
    assert updated.result == 550.0

    # Get by researcher
    by_r = repo.get_by_researcher(sample_researcher.id)
    assert len(by_r) >= 1

    # Statistics
    count, avg_res, min_res, max_res = repo.get_statistics(parameter="Спектр")
    assert count == 1
    assert avg_res == 550.0

    # Delete
    assert repo.delete(exp.id) is True
    assert repo.delete(999999) is False


def test_models_repr(sample_researcher: Researcher) -> None:
    """Verify __repr__ methods of domain models."""
    r_repr = repr(sample_researcher)
    assert "Researcher" in r_repr
    assert sample_researcher.name in r_repr

    exp = Experiment(
        id=1,
        title="Тест",
        parameter="Параметр",
        result=10.0,
        date=dt.date(2026, 1, 1),
        researcher_id=sample_researcher.id,
    )
    exp_repr = repr(exp)
    assert "Experiment" in exp_repr
    assert "Тест" in exp_repr


def test_schema_validators() -> None:
    """Verify validation exceptions for whitespace-only strings."""
    import pytest

    from experiment_registry.schemas import ExperimentCreate, ResearcherCreate

    with pytest.raises(ValueError):
        ResearcherCreate(name="   ", department="Valid")

    with pytest.raises(ValueError):
        ResearcherCreate(name="Valid", department="   ")

    with pytest.raises(ValueError):
        ExperimentCreate(
            title="   ",
            parameter="Параметр",
            result=10.0,
            date=dt.date(2026, 1, 1),
            researcher_id=1,
        )
