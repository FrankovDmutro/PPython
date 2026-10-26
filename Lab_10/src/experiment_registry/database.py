"""Database connection management and SQLAlchemy session lifecycle."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings
from .models import Base


def get_engine():
    """Create SQLAlchemy engine using configured database URL."""
    settings = get_settings()
    url = settings.database_url

    # Auto-create data directory if local SQLite file path
    if url.startswith("sqlite:///") and not url.startswith("sqlite:///:memory:"):
        db_path_str = url.replace("sqlite:///", "")
        db_path = Path(db_path_str).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)

    connect_args = {"check_same_thread": False} if "sqlite" in url else {}
    return create_engine(url, connect_args=connect_args)


engine = get_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def init_db(target_engine=None) -> None:
    """Initialize database tables according to declarative metadata."""
    e = target_engine or engine
    Base.metadata.create_all(bind=e)


def get_db() -> Generator[Session, None, None]:
    """Dependency injection generator providing an active SQLAlchemy database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
