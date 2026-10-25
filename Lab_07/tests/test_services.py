"""Integration tests for ExperimentService and ACID transactional rollback."""

import pytest
from sqlalchemy.orm import Session

from experiment_manager.services import ExperimentService


def test_service_record_and_statistics(test_session: Session) -> None:
    """Test service creating records and calculating statistics."""
    service = ExperimentService(test_session)

    service.record_experiment(
        title="Radiation Pulse",
        researcher_name="Dr. Frankov",
        parameter="radiation",
        result=0.15,
        date="2026-04-12",
        department="Nuclear Lab",
    )
    service.record_experiment(
        title="Radiation Baseline",
        researcher_name="Dr. Frankov",
        parameter="radiation",
        result=0.25,
        date="2026-04-13",
        department="Nuclear Lab",
    )
    test_session.commit()

    stats = service.get_experiment_statistics(parameter="radiation")
    assert stats["count"] == 2.0
    assert stats["average"] == pytest.approx(0.20)
    assert stats["min"] == pytest.approx(0.15)
    assert stats["max"] == pytest.approx(0.25)


def test_transactional_batch_insert_success(test_session: Session) -> None:
    """Test successful atomic batch insertion."""
    service = ExperimentService(test_session)

    batch = [
        {
            "title": "Batch Exp 1",
            "researcher_name": "Dr. Frankov",
            "parameter": "voltage",
            "result": 12.0,
            "date": "2026-04-20",
        },
        {
            "title": "Batch Exp 2",
            "researcher_name": "Dr. Frankov",
            "parameter": "voltage",
            "result": 15.0,
            "date": "2026-04-21",
        },
    ]

    created = service.batch_add_experiments_transactional(batch)
    test_session.commit()

    assert len(created) == 2
    stats = service.get_experiment_statistics(parameter="voltage")
    assert stats["count"] == 2.0


def test_transactional_batch_insert_rollback_on_failure(test_session: Session) -> None:
    """Test ACID Atomicity: failure on any record rolls back the entire batch."""
    service = ExperimentService(test_session)

    # Initial state: 0 experiments
    assert service.get_experiment_statistics()["count"] == 0.0

    bad_batch = [
        {
            "title": "Good Experiment",
            "researcher_name": "Dr. Frankov",
            "parameter": "temperature",
            "result": 20.0,
            "date": "2026-04-20",
        },
        {
            "title": "Violating Record (Sub-Absolute Zero)",
            "researcher_name": "Dr. Frankov",
            "parameter": "temperature",
            "result": -350.0,  # Below -273.15 C
            "date": "2026-04-20",
        },
    ]

    with pytest.raises(ValueError) as exc_info:
        service.batch_add_experiments_transactional(bad_batch)

    assert "Physical constraint violation" in str(exc_info.value)

    # Verify that the good experiment was NOT saved!
    post_stats = service.get_experiment_statistics()
    assert post_stats["count"] == 0.0
