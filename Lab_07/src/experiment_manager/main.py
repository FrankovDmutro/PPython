"""CLI application demonstrating database operations, DB-API, and transactions."""

import argparse
from pathlib import Path
import sys

from experiment_manager.database import (
    Base,
    get_db_api_connection,
    get_engine,
    get_session,
    get_session_factory,
)
from experiment_manager.db_api import (
    db_api_get_statistics,
    db_api_search_by_range,
    db_api_search_by_researcher,
)
from experiment_manager.services import ExperimentService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scientific Experiment Database System (Lab 7, Variant 15)"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("data/experiments.db"),
        help="Path to SQLite database file",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Initialize schema and seed initial sample experiments",
    )
    args = parser.parse_args(argv)

    db_path = args.db_path
    db_url = f"sqlite:///{db_path.as_posix()}"

    print(f"Connecting to SQLite database: {db_url}")
    engine = get_engine(db_url)
    session_factory = get_session_factory(engine)

    # Initialize schema
    Base.metadata.create_all(engine)
    print("Database tables ('researchers', 'experiments') initialized successfully.\n")

    # Seed or demonstrate service operations
    with get_session(session_factory) as session:
        service = ExperimentService(session)

        # 1. Register researchers and experiments
        service.record_experiment(
            title="Cryogenic Calibration",
            researcher_name="Dr. Frankov",
            parameter="temperature",
            result=24.5,
            date="2026-04-01",
            notes="Initial calibration at room temperature",
            department="Quantum Physics",
        )
        service.record_experiment(
            title="Vacuum Pressure Test",
            researcher_name="Dr. Smith",
            parameter="pressure",
            result=101325.0,
            date="2026-04-02",
            notes="Atmospheric baseline",
            department="Applied Physics",
        )
        service.record_experiment(
            title="Semiconductor Threshold",
            researcher_name="Dr. Frankov",
            parameter="voltage",
            result=3.32,
            date="2026-04-03",
            notes="Gate voltage stability",
            department="Quantum Physics",
        )
        service.record_experiment(
            title="Laser Cooling Chamber",
            researcher_name="Dr. Frankov",
            parameter="temperature",
            result=-210.15,
            date="2026-04-04",
            notes="Deep cryocooling phase",
            department="Quantum Physics",
        )

    # 2. Query data using Service Layer & SQLAlchemy
    with get_session(session_factory) as session:
        service = ExperimentService(session)
        print("=== Experiments sorted by date ===")
        all_exp = service.experiment_repo.list_all(order_by_date=True)
        for e in all_exp:
            print(f"[{e.date}] ID={e.id} | '{e.title}' | {e.parameter}: {e.result} | Researcher: {e.researcher.name}")

        stats = service.get_experiment_statistics(parameter="temperature")
        print(f"\n=== Temperature SQL Aggregates (SQLAlchemy) ===")
        print(f"Count: {stats['count']} | Average: {stats['average']:.2f} | Min: {stats['min']:.2f} | Max: {stats['max']:.2f}")

    # 3. Demonstrate raw DB-API parameterized queries
    print("\n=== Raw DB-API Parameterized Search (sqlite3) ===")
    conn = get_db_api_connection(db_path)
    try:
        frankov_experiments = db_api_search_by_researcher(conn, "Dr. Frankov")
        print(f"Found {len(frankov_experiments)} experiments by Dr. Frankov:")
        for r in frankov_experiments:
            print(f"  - [{r['date']}] {r['title']} ({r['parameter']} = {r['result']}) | Notes: {r['notes']}")

        range_results = db_api_search_by_range(conn, min_val=-250.0, max_val=50.0, parameter="temperature")
        print(f"\nDB-API Range Filter [-250.0, 50.0] C: {len(range_results)} records found.")

        raw_stats = db_api_get_statistics(conn)
        print(f"Global DB-API Stats: Count={raw_stats['count']} | Avg={raw_stats['average']:.2f}")
    finally:
        conn.close()

    # 4. Demonstrate Transaction Rollback (ACID Atomicity)
    print("\n=== Testing ACID Transaction Rollback ===")
    bad_batch = [
        {
            "title": "Valid Experiment In Batch",
            "researcher_name": "Dr. Frankov",
            "parameter": "temperature",
            "result": 10.0,
            "date": "2026-04-05",
        },
        {
            "title": "Invalid Negative Absolute Zero",
            "researcher_name": "Dr. Frankov",
            "parameter": "temperature",
            "result": -300.0,  # Below -273.15 -> Triggers Rollback!
            "date": "2026-04-05",
        },
    ]

    with get_session(session_factory) as session:
        service = ExperimentService(session)
        initial_count = service.get_experiment_statistics()["count"]
        try:
            service.batch_add_experiments_transactional(bad_batch)
            print("ERROR: Transaction should have failed!")
        except ValueError as err:
            print(f"Caught expected transaction error: '{err}'")
            print("Session successfully rolled back. Verifying count...")
            post_count = service.get_experiment_statistics()["count"]
            print(f"Initial count: {initial_count} | Post-rollback count: {post_count} (No partial commits!)")
            assert initial_count == post_count

    print("\nAll database demonstration steps completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
