"""Integration tests for raw Python DB-API (sqlite3) parameterized queries and transactions."""

from pathlib import Path
import sqlite3
import pytest

from experiment_manager.database import Base, get_db_api_connection, get_engine
from experiment_manager.db_api import (
    db_api_batch_insert,
    db_api_get_statistics,
    db_api_search_by_range,
    db_api_search_by_researcher,
)


@pytest.fixture
def db_api_conn(temp_db_file: Path) -> sqlite3.Connection:
    """Fixture providing a configured SQLite database file with tables created."""
    engine = get_engine(f"sqlite:///{temp_db_file.as_posix()}")
    Base.metadata.create_all(engine)
    engine.dispose()

    conn = get_db_api_connection(temp_db_file)

    # Seed initial researcher and experiments via raw SQL
    cursor = conn.cursor()
    cursor.execute("INSERT INTO researchers (name, department) VALUES ('Dr. Frankov', 'Quantum Physics');")
    res_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO experiments (title, researcher_id, parameter, result, date, notes) "
        "VALUES ('Cryo Test', ?, 'temperature', 25.0, '2026-04-01', 'Baseline');",
        (res_id,),
    )
    cursor.execute(
        "INSERT INTO experiments (title, researcher_id, parameter, result, date, notes) "
        "VALUES ('Pressure Test', ?, 'pressure', 101300.0, '2026-04-02', 'Nominal');",
        (res_id,),
    )
    conn.commit()

    yield conn
    conn.close()


def test_db_api_search_by_researcher(db_api_conn: sqlite3.Connection) -> None:
    """Test parameterized query searching by researcher."""
    results = db_api_search_by_researcher(db_api_conn, "Dr. Frankov")
    assert len(results) == 2
    assert results[0]["researcher"] == "Dr. Frankov"
    assert results[0]["parameter"] in {"temperature", "pressure"}


def test_db_api_search_by_range(db_api_conn: sqlite3.Connection) -> None:
    """Test parameterized query filtering by numerical result range."""
    results = db_api_search_by_range(db_api_conn, min_val=20.0, max_val=30.0, parameter="temperature")
    assert len(results) == 1
    assert results[0]["title"] == "Cryo Test"
    assert results[0]["result"] == pytest.approx(25.0)


def test_db_api_get_statistics(db_api_conn: sqlite3.Connection) -> None:
    """Test SQL aggregation functions in DB-API."""
    stats = db_api_get_statistics(db_api_conn)
    assert stats["count"] == 2.0
    assert stats["min"] == pytest.approx(25.0)
    assert stats["max"] == pytest.approx(101300.0)


def test_db_api_batch_insert_success(db_api_conn: sqlite3.Connection) -> None:
    """Test batch insert via DB-API."""
    records = [
        {"title": "Pulse 1", "researcher_id": 1, "parameter": "voltage", "result": 5.0, "date": "2026-04-10"},
        {"title": "Pulse 2", "researcher_id": 1, "parameter": "voltage", "result": 6.5, "date": "2026-04-11"},
    ]
    inserted = db_api_batch_insert(db_api_conn, records)
    assert inserted == 2

    stats = db_api_get_statistics(db_api_conn, parameter="voltage")
    assert stats["count"] == 2.0
    assert stats["average"] == pytest.approx(5.75)


def test_db_api_batch_insert_rollback_on_error(db_api_conn: sqlite3.Connection) -> None:
    """Test raw DB-API rollback when an item violates physical constraints."""
    initial_stats = db_api_get_statistics(db_api_conn)

    bad_batch = [
        {"title": "Valid Run", "researcher_id": 1, "parameter": "temperature", "result": 10.0, "date": "2026-04-15"},
        {"title": "Violating Run", "researcher_id": 1, "parameter": "temperature", "result": -300.0, "date": "2026-04-15"},
    ]

    with pytest.raises(ValueError):
        db_api_batch_insert(db_api_conn, bad_batch)

    # Verify rollback: database count must remain unchanged
    post_stats = db_api_get_statistics(db_api_conn)
    assert post_stats["count"] == initial_stats["count"]
