"""Database configuration, engine, session factory, and DB-API connection helpers."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Generator
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_DB_PATH = Path("data/experiments.db")
DEFAULT_DB_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy ORM models."""


def get_engine(db_url: str | None = None, echo: bool = False) -> Engine:
    """Create and return a configured SQLAlchemy Engine."""
    url = db_url or DEFAULT_DB_URL
    if url.startswith("sqlite") and not url.endswith(":memory:"):
        # Ensure parent directory exists for file-based SQLite
        db_file = url.replace("sqlite:///", "")
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)

    return create_engine(url, echo=echo, connect_args={"check_same_thread": False})


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a thread-safe session factory bound to the provided engine."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def get_session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_api_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Return a raw SQLite DB-API connection with foreign keys enabled."""
    path = Path(db_path or DEFAULT_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn
