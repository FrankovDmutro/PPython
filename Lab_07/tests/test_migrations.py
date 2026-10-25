"""Integration tests for Alembic database migrations."""

from pathlib import Path
import sqlite3
from alembic.config import Config
from alembic import command
import pytest

from experiment_manager.database import Base, get_engine


def test_alembic_upgrade_head(tmp_path: Path) -> None:
    """Test running Alembic upgrade head on SQLite database and verifying 'notes' column."""
    db_file = tmp_path / "alembic_test.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    # 1. Initialize initial tables without notes
    engine = get_engine(db_url)
    with engine.connect() as conn:
        conn.exec_driver_sql(
            """
            CREATE TABLE researchers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                department VARCHAR(100) NOT NULL
            );
            """
        )
        conn.exec_driver_sql(
            """
            CREATE TABLE experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                researcher_id INTEGER NOT NULL REFERENCES researchers(id),
                parameter VARCHAR(50) NOT NULL,
                result FLOAT NOT NULL,
                date VARCHAR(20) NOT NULL
            );
            """
        )
        conn.commit()
    engine.dispose()

    # Verify notes column does NOT exist yet
    conn = sqlite3.connect(str(db_file))
    columns_before = [col[1] for col in conn.execute("PRAGMA table_info(experiments);").fetchall()]
    conn.close()
    assert "notes" not in columns_before

    # 2. Run Alembic upgrade head
    ini_path = Path("Lab_07/alembic.ini")
    alembic_cfg = Config(str(ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    command.upgrade(alembic_cfg, "head")

    # 3. Verify notes column exists now
    conn = sqlite3.connect(str(db_file))
    columns_after = [col[1] for col in conn.execute("PRAGMA table_info(experiments);").fetchall()]
    conn.close()
    assert "notes" in columns_after
