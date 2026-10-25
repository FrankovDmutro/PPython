"""Integration tests for ResearcherRepository and ExperimentRepository."""

import pytest
from sqlalchemy.orm import Session

from experiment_manager.models import Experiment, Researcher
from experiment_manager.repositories import ExperimentRepository, ResearcherRepository


def test_researcher_crud(test_session: Session) -> None:
    """Test full CRUD operations on ResearcherRepository."""
    repo = ResearcherRepository(test_session)

    # 1. Create
    res = repo.create(name="Dr. Frankov", department="Quantum Dynamics")
    assert res.id is not None
    assert res.name == "Dr. Frankov"

    # 2. Read by ID and by Name
    by_id = repo.get_by_id(res.id)
    assert by_id is not None
    assert by_id.name == "Dr. Frankov"

    by_name = repo.get_by_name("Dr. Frankov")
    assert by_name is not None
    assert by_name.id == res.id

    # 3. Update
    updated = repo.update(res.id, department="Advanced Cybernetics")
    assert updated is not None
    assert updated.department == "Advanced Cybernetics"

    # 4. List all
    all_res = repo.list_all()
    assert len(all_res) == 1

    # 5. Delete
    deleted = repo.delete(res.id)
    assert deleted is True
    assert repo.get_by_id(res.id) is None


def test_experiment_crud_and_relationship(test_session: Session) -> None:
    """Test ExperimentRepository CRUD and One-to-Many relationship with Researcher."""
    res_repo = ResearcherRepository(test_session)
    exp_repo = ExperimentRepository(test_session)

    researcher = res_repo.create(name="Dr. Alan", department="Electrodynamics")

    # 1. Create experiment
    exp = exp_repo.create(
        title="Inductance Pulse",
        researcher_id=researcher.id,
        parameter="current",
        result=15.4,
        date="2026-04-10",
        notes="High current spike",
    )
    assert exp.id is not None
    assert exp.researcher.name == "Dr. Alan"
    assert len(researcher.experiments) == 1

    # 2. Read
    fetched = exp_repo.get_by_id(exp.id)
    assert fetched is not None
    assert fetched.result == pytest.approx(15.4)

    # 3. Update
    updated = exp_repo.update(exp.id, result=16.8, notes="Adjusted calibration")
    assert updated is not None
    assert updated.result == pytest.approx(16.8)
    assert updated.notes == "Adjusted calibration"

    # 4. Delete
    deleted = exp_repo.delete(exp.id)
    assert deleted is True
    assert exp_repo.get_by_id(exp.id) is None


def test_experiment_find_by_range_and_date_ordering(populated_session: Session) -> None:
    """Test range filtering and date ordering in ExperimentRepository."""
    exp_repo = ExperimentRepository(populated_session)

    # Range filter: temperatures in [-250.0, 50.0]
    results = exp_repo.find_by_range(-250.0, 50.0, parameter="temperature")
    assert len(results) == 2
    # Check ordering by result ascending
    assert results[0].result == pytest.approx(-210.0)
    assert results[1].result == pytest.approx(24.5)

    # Date ordering ascending
    ordered_asc = exp_repo.list_all(order_by_date=True, ascending=True)
    assert len(ordered_asc) == 4
    assert ordered_asc[0].date == "2026-04-01"
    assert ordered_asc[-1].date == "2026-04-04"

    # Date ordering descending
    ordered_desc = exp_repo.list_all(order_by_date=True, ascending=False)
    assert ordered_desc[0].date == "2026-04-04"
    assert ordered_desc[-1].date == "2026-04-01"


def test_experiment_sql_aggregates(populated_session: Session) -> None:
    """Test SQL aggregation functions: COUNT, AVG, MIN, MAX."""
    exp_repo = ExperimentRepository(populated_session)

    # Global stats
    global_stats = exp_repo.get_aggregates()
    assert global_stats["count"] == 4.0
    assert global_stats["max"] == pytest.approx(101325.0)

    # Temperature-specific stats (results: 24.5 and -210.0)
    temp_stats = exp_repo.get_aggregates(parameter="temperature")
    assert temp_stats["count"] == 2.0
    expected_avg = (24.5 + (-210.0)) / 2
    assert temp_stats["average"] == pytest.approx(expected_avg)
    assert temp_stats["min"] == pytest.approx(-210.0)
    assert temp_stats["max"] == pytest.approx(24.5)


def test_cascade_delete_researcher_removes_experiments(populated_session: Session) -> None:
    """Test that deleting a researcher cascades to all associated experiments."""
    res_repo = ResearcherRepository(populated_session)
    exp_repo = ExperimentRepository(populated_session)

    frankov = res_repo.get_by_name("Dr. Frankov")
    assert frankov is not None
    frankov_id = frankov.id

    # Verify experiments exist before deletion
    experiments_before = exp_repo.find_by_researcher_name("Dr. Frankov")
    assert len(experiments_before) == 3

    # Delete researcher
    res_repo.delete(frankov_id)
    populated_session.commit()

    # Verify researcher and experiments are deleted
    assert res_repo.get_by_id(frankov_id) is None
    assert len(exp_repo.find_by_researcher_name("Dr. Frankov")) == 0
